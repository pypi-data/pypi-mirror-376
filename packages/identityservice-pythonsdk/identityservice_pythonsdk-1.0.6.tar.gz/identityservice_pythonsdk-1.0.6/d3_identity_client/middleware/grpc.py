"""
gRPC interceptor for D3 Identity Service authentication
"""

import grpc
import logging
from typing import Optional, Dict, Any, Callable
from grpc import aio
from ..models.auth import AuthenticationContext
from ..services.auth_service import AuthService

logger = logging.getLogger(__name__)

class D3IdentityGrpcInterceptor(aio.ServerInterceptor):
    """
    gRPC server interceptor for D3 Identity Service authentication
    """
    
    def __init__(
        self, 
        auth_service: AuthService,
        skip_methods: Optional[list] = None,
        require_auth: bool = True
    ):
        """
        Initialize gRPC interceptor
        
        Args:
            auth_service: Authentication service
            skip_methods: Methods to skip authentication
            require_auth: Whether to require authentication globally
        """
        self.auth_service = auth_service
        self.skip_methods = skip_methods or ['/grpc.health.v1.Health/Check']
        self.require_auth = require_auth
        
        logger.info("D3IdentityGrpcInterceptor initialized")
    
    async def intercept_service(self, continuation, handler_call_details):
        """
        Intercept gRPC service calls for authentication
        
        Args:
            continuation: Next interceptor or handler
            handler_call_details: gRPC handler call details
            
        Returns:
            gRPC handler with authentication
        """
        method_name = handler_call_details.method
        
        # Skip authentication for certain methods
        if method_name in self.skip_methods:
            return await continuation(handler_call_details)
        
        # Create authenticated handler
        async def authenticated_handler(request, context):
            try:
                # Extract authentication from metadata
                auth_context = await self._authenticate_request(context)
                
                # Handle authentication requirement
                if self.require_auth and not auth_context:
                    await context.abort(
                        grpc.StatusCode.UNAUTHENTICATED, 
                        'Authentication required'
                    )
                    return
                
                # Add authentication context to gRPC context
                if auth_context:
                    await context.set_details(f"Authenticated as {auth_context.tenant_guid}")
                    # Store in context for handlers to access
                    setattr(context, 'tenant_context', auth_context)
                    
                    # Add tenant information to response metadata
                    await context.send_initial_metadata([
                        ('x-tenant-guid', auth_context.tenant_guid),
                        ('x-tenant-name', auth_context.tenant_name),
                        ('x-authenticated-at', auth_context.authenticated_at.isoformat())
                    ])
                
                # Get original handler
                original_handler = await continuation(handler_call_details)
                if original_handler is None:
                    await context.abort(grpc.StatusCode.UNIMPLEMENTED, 'Method not found')
                    return
                
                # Call original handler
                return await original_handler(request, context)
                
            except grpc.aio.AioRpcError:
                # Re-raise gRPC errors
                raise
            except Exception as e:
                logger.error(f"gRPC authentication error: {e}")
                await context.abort(grpc.StatusCode.INTERNAL, 'Internal server error')
                return
        
        return aio.unary_unary_rpc_method_handler(authenticated_handler)
    
    async def _authenticate_request(
        self, 
        context: grpc.aio.ServicerContext
    ) -> Optional[AuthenticationContext]:
        """
        Extract and validate authentication from gRPC context
        
        Args:
            context: gRPC servicer context
            
        Returns:
            AuthenticationContext or None if authentication failed
        """
        try:
            # Get metadata from context
            metadata = dict(context.invocation_metadata())
            
            # Look for authorization header
            auth_token = None
            
            # Check standard Authorization header
            if 'authorization' in metadata:
                auth_header = metadata['authorization']
                if auth_header.startswith('Bearer '):
                    auth_token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Check x-authorization header (alternative)
            elif 'x-authorization' in metadata:
                auth_token = metadata['x-authorization']
            
            # Check for tenant-specific headers (for API key auth)
            elif 'x-tenant-guid' in metadata and 'x-api-key' in metadata:
                # API key authentication (not implemented in current JWT service)
                logger.debug("API key authentication not yet supported")
                return None
            
            if not auth_token:
                logger.debug("No authentication token found in gRPC metadata")
                return None
            
            # Authenticate token
            auth_context = await self.auth_service.authenticate_any_token(auth_token)
            
            if auth_context:
                logger.debug(f"gRPC authentication successful: {auth_context.tenant_guid}")
            else:
                logger.debug("gRPC authentication failed")
            
            return auth_context
            
        except Exception as e:
            logger.error(f"gRPC authentication extraction failed: {e}")
            return None

class D3IdentityGrpcClientInterceptor(aio.UnaryUnaryClientInterceptor):
    """
    gRPC client interceptor for adding D3 Identity Service authentication
    """
    
    def __init__(self, auth_service: AuthService, tenant_guid: str):
        """
        Initialize gRPC client interceptor
        
        Args:
            auth_service: Authentication service
            tenant_guid: Tenant GUID for token generation
        """
        self.auth_service = auth_service
        self.tenant_guid = tenant_guid
        self._cached_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        
        logger.info("D3IdentityGrpcClientInterceptor initialized")
    
    async def intercept_unary_unary(self, continuation, client_call_details, request):
        """
        Intercept outgoing gRPC calls to add authentication
        
        Args:
            continuation: Next interceptor or call
            client_call_details: gRPC client call details
            request: Request object
            
        Returns:
            Response from gRPC call
        """
        try:
            # Get authentication token
            token = await self._get_auth_token()
            
            if token:
                # Add authorization header to metadata
                metadata = list(client_call_details.metadata or [])
                metadata.append(('authorization', f'Bearer {token}'))
                
                # Create new call details with authentication
                authenticated_call_details = client_call_details._replace(metadata=metadata)
                
                logger.debug("Added authentication to gRPC client call")
                return await continuation(authenticated_call_details, request)
            else:
                logger.warning("No authentication token available for gRPC client call")
                return await continuation(client_call_details, request)
                
        except Exception as e:
            logger.error(f"gRPC client authentication failed: {e}")
            # Continue without authentication rather than failing
            return await continuation(client_call_details, request)
    
    async def _get_auth_token(self) -> Optional[str]:
        """
        Get authentication token, using cache if available
        
        Returns:
            JWT token string or None if failed
        """
        try:
            import time
            
            # Check if cached token is still valid
            if (self._cached_token and 
                self._token_expires_at and 
                time.time() < (self._token_expires_at - 60)):  # 1 minute buffer
                return self._cached_token
            
            # Generate new service token
            service_name = "GrpcClient"  # Could be configurable
            token = await self.auth_service.generate_service_authentication(
                tenant_guid=self.tenant_guid,
                service_name=service_name,
                expiration_minutes=30
            )
            
            if token:
                self._cached_token = token
                self._token_expires_at = time.time() + (30 * 60)  # 30 minutes
                logger.debug("Generated new gRPC client authentication token")
            
            return token
            
        except Exception as e:
            logger.error(f"Failed to get auth token for gRPC client: {e}")
            return None

# Utility functions for gRPC authentication
def get_tenant_context_from_grpc_context(context: grpc.aio.ServicerContext) -> Optional[AuthenticationContext]:
    """
    Get tenant context from gRPC servicer context
    
    Args:
        context: gRPC servicer context
        
    Returns:
        AuthenticationContext or None
    """
    return getattr(context, 'tenant_context', None)

def require_grpc_authentication(context: grpc.aio.ServicerContext) -> AuthenticationContext:
    """
    Require authentication in gRPC handler
    
    Args:
        context: gRPC servicer context
        
    Returns:
        AuthenticationContext
        
    Raises:
        grpc.aio.AioRpcError: If not authenticated
    """
    auth_context = get_tenant_context_from_grpc_context(context)
    if not auth_context:
        context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Authentication required')
    return auth_context

async def require_grpc_service_authentication(
    context: grpc.aio.ServicerContext,
    required_service: Optional[str] = None
) -> AuthenticationContext:
    """
    Require service authentication in gRPC handler
    
    Args:
        context: gRPC servicer context
        required_service: Required service name
        
    Returns:
        AuthenticationContext for service
        
    Raises:
        grpc.aio.AioRpcError: If authentication fails
    """
    auth_context = get_tenant_context_from_grpc_context(context)
    
    if not auth_context:
        await context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Authentication required')
        return None
    
    if not auth_context.is_service_authentication():
        await context.abort(grpc.StatusCode.PERMISSION_DENIED, 'Service authentication required')
        return None
    
    if required_service and auth_context.get_service_name() != required_service:
        await context.abort(
            grpc.StatusCode.PERMISSION_DENIED, 
            f'Service {required_service} authentication required'
        )
        return None
    
    return auth_context

async def require_grpc_user_authentication(
    context: grpc.aio.ServicerContext,
    required_role: Optional[str] = None
) -> AuthenticationContext:
    """
    Require user authentication in gRPC handler
    
    Args:
        context: gRPC servicer context
        required_role: Required user role
        
    Returns:
        AuthenticationContext for user
        
    Raises:
        grpc.aio.AioRpcError: If authentication fails
    """
    auth_context = get_tenant_context_from_grpc_context(context)
    
    if not auth_context:
        await context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Authentication required')
        return None
    
    if not auth_context.is_user_authentication():
        await context.abort(grpc.StatusCode.PERMISSION_DENIED, 'User authentication required')
        return None
    
    if (required_role and 
        auth_context.token_claims and
        auth_context.token_claims.role != required_role):
        await context.abort(
            grpc.StatusCode.PERMISSION_DENIED, 
            f'Role {required_role} required'
        )
        return None
    
    return auth_context