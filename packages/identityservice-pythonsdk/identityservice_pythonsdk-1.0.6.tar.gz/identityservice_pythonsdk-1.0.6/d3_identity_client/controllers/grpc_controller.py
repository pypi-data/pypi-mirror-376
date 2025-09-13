"""
gRPC controller for SDK functionality validation
Implements TestConnectionGrpcService from protobuf definition
"""

import logging
import grpc
from typing import Optional
from google.rpc import status_pb2

try:
    # Import generated protobuf files from protos directory
    from protos import test_connection_pb2
    from protos import test_connection_pb2_grpc
    PROTOBUF_AVAILABLE = True
except ImportError:
    # Fallback if protobuf files aren't generated yet
    PROTOBUF_AVAILABLE = False
    test_connection_pb2 = None
    test_connection_pb2_grpc = None

from ..models.auth import AuthenticationContext
from ..services.auth_service import AuthService
from ..services.tenant_service import TenantService

logger = logging.getLogger(__name__)


class TestConnectionGrpcServicer(test_connection_pb2_grpc.TestConnectionGrpcServiceServicer if PROTOBUF_AVAILABLE else object):
    """
    gRPC servicer for Identity Service SDK
    Implements TestConnectionGrpcService from protobuf definition
    """
    
    def __init__(self, auth_service: AuthService, tenant_service: TenantService):
        """
        Initialize gRPC servicer
        
        Args:
            auth_service: Authentication service
            tenant_service: Tenant service
        """
        self.auth_service = auth_service
        self.tenant_service = tenant_service
        
        if not PROTOBUF_AVAILABLE:
            logger.warning("Protobuf files not available. Run 'python generate_protos.py' to generate them.")
        else:
            logger.info("TestConnectionGrpcServicer initialized")
    
    def TestConnection(
        self, 
        request: 'test_connection_pb2.TestConnectionRequest', 
        context: grpc.ServicerContext
    ) -> 'test_connection_pb2.TestConnectionResponse':
        """
        Test connection gRPC method
        Implements the TestConnection RPC from the protobuf service definition
        
        Args:
            request: TestConnectionRequest (empty message)
            context: gRPC context
            
        Returns:
            TestConnectionResponse with tenant information
        """
        if not PROTOBUF_AVAILABLE:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Protobuf files not generated. Run 'python generate_protos.py'")
            return test_connection_pb2.TestConnectionResponse() if test_connection_pb2 else None
        
        try:
            logger.info("TestConnection gRPC method called")
            
            # Authenticate gRPC request
            auth_context = self._authenticate_grpc_request(context)
            if not auth_context:
                response = test_connection_pb2.TestConnectionResponse()
                response.Status.CopyFrom(status_pb2.Status(
                    code=grpc.StatusCode.UNAUTHENTICATED.value[0],
                    message="Authentication required for test connection"
                ))
                return response
            
            tenant_guid = auth_context.tenant_guid
            logger.info(f"TestConnection called for tenant {tenant_guid}")
            
            # Get tenant information (sync call - convert from async if needed)
            tenant_info = self._get_tenant_sync(tenant_guid)
            
            # Create response
            response = test_connection_pb2.TestConnectionResponse()
            
            if tenant_info:
                response.TenantGuid = tenant_info.tenant_guid
                response.TenantName = tenant_info.tenant_name
                response.TenantType = tenant_info.tenant_type.value
                response.Status.CopyFrom(status_pb2.Status(
                    code=0,  # OK
                    message=f"Connection test successful for tenant {tenant_info.tenant_name}"
                ))
                
                logger.info(f"TestConnection successful for tenant {tenant_info.tenant_name}")
            else:
                response.TenantGuid = tenant_guid
                response.TenantName = "Unknown"
                response.TenantType = "Unknown"
                response.Status.CopyFrom(status_pb2.Status(
                    code=grpc.StatusCode.NOT_FOUND.value[0],
                    message=f"Tenant {tenant_guid} not found"
                ))
                
                logger.warning(f"Tenant {tenant_guid} not found")
            
            return response
            
        except Exception as e:
            logger.error(f"TestConnection failed: {e}")
            
            response = test_connection_pb2.TestConnectionResponse()
            response.Status.CopyFrom(status_pb2.Status(
                code=grpc.StatusCode.INTERNAL.value[0],
                message=f"Connection test failed: {str(e)}"
            ))
            return response
    
    def _authenticate_grpc_request(self, context: grpc.ServicerContext) -> Optional[AuthenticationContext]:
        """
        Authenticate gRPC request using metadata
        
        Args:
            context: gRPC servicer context
            
        Returns:
            AuthenticationContext if valid, None otherwise
        """
        try:
            # Get metadata from context
            metadata = dict(context.invocation_metadata())
            
            # Look for authorization header
            auth_token = None
            if 'authorization' in metadata:
                auth_header = metadata['authorization']
                if auth_header.startswith('Bearer '):
                    auth_token = auth_header[7:]  # Remove "Bearer " prefix
            elif 'Authorization' in metadata:  # Case variation
                auth_header = metadata['Authorization']
                if auth_header.startswith('Bearer '):
                    auth_token = auth_header[7:]
            
            if not auth_token:
                logger.debug("No authorization token found in gRPC metadata")
                return None
            
            # Authenticate token (sync version needed for gRPC)
            auth_context = self._authenticate_token_sync(auth_token)
            
            if auth_context:
                logger.debug(f"gRPC authentication successful for tenant: {auth_context.tenant_guid}")
                return auth_context
            else:
                logger.debug("gRPC authentication failed - invalid token")
                return None
                
        except Exception as e:
            logger.error(f"gRPC authentication error: {e}")
            return None
    
    def _authenticate_token_sync(self, token: str) -> Optional[AuthenticationContext]:
        """
        Synchronous token authentication (wrapper for async method)
        
        Args:
            token: JWT token to authenticate
            
        Returns:
            AuthenticationContext if valid, None otherwise
        """
        import asyncio
        
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an async context, create a new thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self.auth_service.authenticate_any_token(token))
                    )
                    return future.result(timeout=10)
            except RuntimeError:
                # No running loop, we can use asyncio.run
                return asyncio.run(self.auth_service.authenticate_any_token(token))
                
        except Exception as e:
            logger.error(f"Sync token authentication failed: {e}")
            return None
    
    def _get_tenant_sync(self, tenant_guid: str):
        """
        Synchronous tenant retrieval (wrapper for async method)
        
        Args:
            tenant_guid: Tenant GUID
            
        Returns:
            TenantInfo if found, None otherwise
        """
        import asyncio
        
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an async context, create a new thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self.tenant_service.get_tenant(tenant_guid))
                    )
                    return future.result(timeout=10)
            except RuntimeError:
                # No running loop, we can use asyncio.run
                return asyncio.run(self.tenant_service.get_tenant(tenant_guid))
                
        except Exception as e:
            logger.error(f"Sync tenant retrieval failed: {e}")
            return None


def create_grpc_servicer(auth_service: AuthService, tenant_service: TenantService) -> TestConnectionGrpcServicer:
    """
    Factory function to create gRPC servicer
    
    Args:
        auth_service: Authentication service
        tenant_service: Tenant service
        
    Returns:
        TestConnectionGrpcServicer instance
    """
    return TestConnectionGrpcServicer(auth_service, tenant_service)


def add_servicer_to_server(servicer: TestConnectionGrpcServicer, server: grpc.Server):
    """
    Add the gRPC servicer to a gRPC server
    
    Args:
        servicer: TestConnectionGrpcServicer instance
        server: gRPC server
    """
    if PROTOBUF_AVAILABLE:
        test_connection_pb2_grpc.add_TestConnectionGrpcServiceServicer_to_server(servicer, server)
        logger.info("TestConnectionGrpcService added to server on port 50051")
    else:
        logger.error("Cannot add servicer - protobuf files not available")


def create_grpc_server(auth_service: AuthService, tenant_service: TenantService, port: int = 50051) -> grpc.Server:
    """
    Create and configure a gRPC server with the TestConnection service
    
    Args:
        auth_service: Authentication service
        tenant_service: Tenant service
        port: Port to listen on (default: 50051)
        
    Returns:
        Configured gRPC server
    """
    import concurrent.futures
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    
    # Create and add servicer
    servicer = create_grpc_servicer(auth_service, tenant_service)
    add_servicer_to_server(servicer, server)
    
    # Add listening port
    server.add_insecure_port(f'[::]:{port}')
    
    logger.info(f"gRPC server configured on port {port}")
    return server


# Backwards compatibility
GrpcController = TestConnectionGrpcServicer