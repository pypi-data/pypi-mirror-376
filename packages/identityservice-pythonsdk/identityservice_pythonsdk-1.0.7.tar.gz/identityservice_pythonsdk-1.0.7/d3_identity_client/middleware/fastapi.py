"""
FastAPI middleware for D3 Identity Service authentication
"""

import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from ..models.auth import AuthenticationContext
from ..services.auth_service import AuthService

logger = logging.getLogger(__name__)

class D3IdentityMiddleware:
    """
    FastAPI dependency for D3 Identity Service authentication
    """
    
    def __init__(self, auth_service: AuthService):
        """
        Initialize middleware
        
        Args:
            auth_service: Authentication service instance
        """
        self.auth_service = auth_service
        self.security = HTTPBearer()
        
        logger.info("D3IdentityMiddleware initialized")
    
    async def get_current_tenant_context(
        self, 
        request: Request
    ) -> Optional[AuthenticationContext]:
        """
        Extract current tenant context from request
        
        Args:
            request: FastAPI request object
            
        Returns:
            AuthenticationContext or None if not authenticated
        """
        try:
            # Check for Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return None
            
            # Extract token
            if not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Authenticate token
            context = await self.auth_service.authenticate_any_token(token)
            
            if context:
                # Add context to request state for later use
                request.state.tenant_context = context
                logger.debug(f"Authenticated request for tenant: {context.tenant_guid}")
            
            return context
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
    
    async def require_authentication(
        self, 
        request: Request
    ) -> AuthenticationContext:
        """
        Require valid authentication
        
        Args:
            request: FastAPI request object
            
        Returns:
            AuthenticationContext
            
        Raises:
            HTTPException: If authentication fails
        """
        context = await self.get_current_tenant_context(request)
        if not context:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return context
    
    async def require_service_authentication(
        self, 
        request: Request,
        required_service: Optional[str] = None,
        required_permissions: Optional[list] = None
    ) -> AuthenticationContext:
        """
        Require service token authentication
        
        Args:
            request: FastAPI request object
            required_service: Required service name
            required_permissions: Required permissions
            
        Returns:
            AuthenticationContext for service
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Bearer token required",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            token = auth_header[7:]
            context = await self.auth_service.authenticate_service_token(
                token, required_service, required_permissions
            )
            
            if not context:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid service authentication"
                )
            
            request.state.tenant_context = context
            return context
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Service authentication failed: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    async def require_user_authentication(
        self, 
        request: Request,
        required_role: Optional[str] = None,
        required_permissions: Optional[list] = None
    ) -> AuthenticationContext:
        """
        Require user token authentication
        
        Args:
            request: FastAPI request object
            required_role: Required user role
            required_permissions: Required permissions
            
        Returns:
            AuthenticationContext for user
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Bearer token required",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            token = auth_header[7:]
            context = await self.auth_service.authenticate_user_token(
                token, required_role, required_permissions
            )
            
            if not context:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid user authentication"
                )
            
            request.state.tenant_context = context
            return context
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User authentication failed: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    def create_auth_dependency(
        self,
        require_service_token: bool = False,
        require_user_token: bool = False,
        required_service: Optional[str] = None,
        required_role: Optional[str] = None,
        required_permissions: Optional[list] = None
    ) -> Callable:
        """
        Create FastAPI dependency function for authentication
        
        Args:
            require_service_token: Require service token
            require_user_token: Require user token
            required_service: Required service name
            required_role: Required user role
            required_permissions: Required permissions
            
        Returns:
            FastAPI dependency function
        """
        if require_service_token:
            async def auth_dependency(request: Request) -> AuthenticationContext:
                return await self.require_service_authentication(
                    request, required_service, required_permissions
                )
        elif require_user_token:
            async def auth_dependency(request: Request) -> AuthenticationContext:
                return await self.require_user_authentication(
                    request, required_role, required_permissions
                )
        else:
            async def auth_dependency(request: Request) -> AuthenticationContext:
                return await self.require_authentication(request)
        
        return Depends(auth_dependency)

class D3IdentityFastAPIMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic tenant context injection
    """
    
    def __init__(
        self, 
        app, 
        auth_service: AuthService,
        skip_paths: Optional[list] = None,
        require_auth: bool = False
    ):
        """
        Initialize FastAPI middleware
        
        Args:
            app: FastAPI application
            auth_service: Authentication service
            skip_paths: Paths to skip authentication
            require_auth: Whether to require authentication globally
        """
        super().__init__(app)
        self.auth_service = auth_service
        self.skip_paths = skip_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.require_auth = require_auth
        self.identity_middleware = D3IdentityMiddleware(auth_service)
        
        logger.info("D3IdentityFastAPIMiddleware initialized")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with authentication
        
        Args:
            request: FastAPI request
            call_next: Next middleware function
            
        Returns:
            Response object
        """
        try:
            # Skip authentication for certain paths
            if request.url.path in self.skip_paths:
                return await call_next(request)
            
            # Extract tenant context
            context = await self.identity_middleware.get_current_tenant_context(request)
            
            # Handle authentication requirement
            if self.require_auth and not context:
                return Response(
                    content='{"detail":"Authentication required"}',
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer", "Content-Type": "application/json"}
                )
            
            # Add tenant headers if context available
            if context:
                request.state.tenant_context = context
                # Add custom headers for downstream services
                request.scope["headers"].append((b"x-tenant-guid", context.tenant_guid.encode()))
                request.scope["headers"].append((b"x-tenant-name", context.tenant_name.encode()))
                
                if context.token_claims and context.token_claims.service_name:
                    request.scope["headers"].append((b"x-service-name", context.token_claims.service_name.encode()))
                
                if context.token_claims and context.token_claims.user_id:
                    request.scope["headers"].append((b"x-user-id", context.token_claims.user_id.encode()))
            
            # Process request
            response = await call_next(request)
            
            # Add tenant context to response headers (for debugging)
            if context and hasattr(request.state, 'tenant_context'):
                response.headers["X-Tenant-Guid"] = context.tenant_guid
                response.headers["X-Authenticated-At"] = context.authenticated_at.isoformat()
            
            return response
            
        except Exception as e:
            logger.error(f"Middleware error: {e}")
            return Response(
                content='{"detail":"Internal server error"}',
                status_code=500,
                headers={"Content-Type": "application/json"}
            )

# Convenience functions for common authentication patterns
def create_service_auth_dependency(
    auth_service: AuthService,
    required_service: Optional[str] = None,
    required_permissions: Optional[list] = None
) -> Callable:
    """
    Create service authentication dependency
    
    Args:
        auth_service: Authentication service
        required_service: Required service name
        required_permissions: Required permissions
        
    Returns:
        FastAPI dependency function
    """
    middleware = D3IdentityMiddleware(auth_service)
    return middleware.create_auth_dependency(
        require_service_token=True,
        required_service=required_service,
        required_permissions=required_permissions
    )

def create_user_auth_dependency(
    auth_service: AuthService,
    required_role: Optional[str] = None,
    required_permissions: Optional[list] = None
) -> Callable:
    """
    Create user authentication dependency
    
    Args:
        auth_service: Authentication service
        required_role: Required user role
        required_permissions: Required permissions
        
    Returns:
        FastAPI dependency function
    """
    middleware = D3IdentityMiddleware(auth_service)
    return middleware.create_auth_dependency(
        require_user_token=True,
        required_role=required_role,
        required_permissions=required_permissions
    )

def create_any_auth_dependency(auth_service: AuthService) -> Callable:
    """
    Create authentication dependency that accepts any valid token
    
    Args:
        auth_service: Authentication service
        
    Returns:
        FastAPI dependency function
    """
    middleware = D3IdentityMiddleware(auth_service)
    return middleware.create_auth_dependency()

# Example usage functions
def get_tenant_context_from_request(request: Request) -> Optional[AuthenticationContext]:
    """
    Get tenant context from FastAPI request state
    
    Args:
        request: FastAPI request object
        
    Returns:
        AuthenticationContext or None
    """
    return getattr(request.state, 'tenant_context', None)