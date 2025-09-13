"""
Test controller for SDK functionality validation
Matches C# IdentityServiceSDK TestController endpoints
"""

import logging
import json
import aiohttp
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from ..models.auth import AuthenticationContext
from ..services.auth_service import AuthService
from ..services.tenant_service import TenantService

logger = logging.getLogger(__name__)

class TestRequest(BaseModel):
    """Test request model matching C# TestRequest"""
    callback_url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class TestResponse(BaseModel):
    """Test response model matching C# TestResponse"""
    status: str
    message: str
    caller_tenant_guid: str
    tenant_guid: Optional[str] = None
    tenant_name: Optional[str] = None
    tenant_type: Optional[str] = None
    tenant_status: Optional[str] = None
    processed_at: datetime
    callback_sent: bool

class RegisterRequest(BaseModel):
    """Register request model matching C# RegisterRequest"""
    service_url: str
    callback_url: Optional[str] = None
    message: Optional[str] = None

class RegisterResponse(BaseModel):
    """Register response model matching C# RegisterResponse"""
    status: str
    message: str
    tenant_guid: str
    target_url: str
    response_received: Optional[str] = None
    processed_at: datetime

class TestController:
    """
    Test controller for SDK functionality validation
    Matches C# IdentityServiceSDK TestController
    """
    
    def __init__(self, auth_service: AuthService, tenant_service: TenantService):
        """
        Initialize TestController
        
        Args:
            auth_service: Authentication service
            tenant_service: Tenant service for configuration
        """
        self.auth_service = auth_service
        self.tenant_service = tenant_service
        self.router = APIRouter(prefix="/identitysdk", tags=["SDK Test"])
        
        # Register routes
        self._register_routes()
        
        logger.info("TestController initialized")
    
    def _register_routes(self):
        """Register FastAPI routes"""
        
        @self.router.post("/test", response_model=TestResponse)
        async def test_endpoint(
            request: TestRequest,
            auth_context: AuthenticationContext = Depends(self._get_auth_context)
        ):
            """
            Test endpoint that receives requests and calls back using authenticated HTTP client
            Matches C# TestController.Test method
            """
            return await self.test(request, auth_context)
        
        @self.router.post("/register", response_model=RegisterResponse)
        async def register_endpoint(
            request: RegisterRequest,
            auth_context: AuthenticationContext = Depends(self._get_auth_context)
        ):
            """
            Register endpoint that calls another service's identitysdk/test endpoint
            Matches C# TestController.RegisterEndpoint method
            """
            return await self.register(request, auth_context)
    
    async def _get_auth_context(self, request: Request) -> AuthenticationContext:
        """
        Extract authentication context from request
        
        Args:
            request: FastAPI request object
            
        Returns:
            AuthenticationContext
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Get Authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header:
                raise HTTPException(status_code=401, detail="Authorization header required")
            
            # Extract Bearer token
            if not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Bearer token required")
            
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Authenticate token
            auth_context = await self.auth_service.authenticate_any_token(token)
            if not auth_context:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            
            return auth_context
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(status_code=500, detail="Authentication service error")
    
    async def test(self, request: TestRequest, auth_context: AuthenticationContext) -> TestResponse:
        """
        Test endpoint implementation matching C# TestController.Test
        
        Args:
            request: Test request data
            auth_context: Authentication context from token
            
        Returns:
            TestResponse with tenant information and callback status
        """
        try:
            tenant_guid = auth_context.tenant_guid
            logger.info(f"Received test request for tenant {tenant_guid}")
            
            # Get full tenant information
            tenant_info = await self.tenant_service.get_tenant(tenant_guid)
            
            # Prepare callback data
            callback_data = {
                "status": "OK",
                "message": "Test endpoint received request successfully",
                "tenant_guid": tenant_guid,
                "tenant_name": tenant_info.tenant_name if tenant_info else "Unknown",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "received_data": request.data
            }
            
            # Send callback if URL provided
            callback_sent = False
            if request.callback_url:
                callback_sent = await self._make_callback(
                    request.callback_url, 
                    callback_data, 
                    tenant_guid
                )
            
            # Return response
            return TestResponse(
                status="OK",
                message="Test completed successfully",
                caller_tenant_guid=tenant_guid,
                tenant_guid=tenant_info.tenant_guid if tenant_info else None,
                tenant_name=tenant_info.tenant_name if tenant_info else None,
                tenant_type=tenant_info.tenant_type.value if tenant_info else None,
                tenant_status=tenant_info.status.value if tenant_info else None,
                processed_at=datetime.now(timezone.utc),
                callback_sent=callback_sent
            )
            
        except Exception as e:
            logger.error(f"Error processing test request: {e}")
            return TestResponse(
                status="Error",
                message=f"Test failed: {str(e)}",
                caller_tenant_guid=auth_context.tenant_guid,
                processed_at=datetime.now(timezone.utc),
                callback_sent=False
            )
    
    async def register(self, request: RegisterRequest, auth_context: AuthenticationContext) -> RegisterResponse:
        """
        Register endpoint implementation matching C# TestController.RegisterEndpoint
        
        Args:
            request: Registration request data
            auth_context: Authentication context from token
            
        Returns:
            RegisterResponse with registration status
        """
        try:
            tenant_guid = auth_context.tenant_guid
            tenant_info = await self.tenant_service.get_tenant(tenant_guid)
            
            logger.info(f"Registering with service {request.service_url} for tenant {tenant_guid}")
            
            # Prepare test data to send to target service
            test_data = {
                "source_service": "SDK-TestController",
                "registration_time": datetime.now(timezone.utc).isoformat(),
                "tenant_guid": tenant_guid,
                "tenant_name": tenant_info.tenant_name if tenant_info else "Unknown",
                "message": request.message or "Registration from Python SDK",
                "callback_url": request.callback_url
            }
            
            # Construct target URL
            target_url = request.service_url.rstrip('/')
            if not target_url.lower().endswith("/identitysdk/test"):
                target_url += "/identitysdk/test"
            
            # Send registration request
            response_content = await self._send_authenticated_request(
                target_url,
                {"data": test_data, "callback_url": request.callback_url},
                tenant_guid
            )
            
            logger.info(f"Registration successful to {target_url} for tenant {tenant_guid}")
            
            return RegisterResponse(
                status="OK",
                message="Registration completed successfully",
                tenant_guid=tenant_guid,
                target_url=target_url,
                response_received=response_content,
                processed_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error during registration to {request.service_url}: {e}")
            return RegisterResponse(
                status="Error",
                message=f"Registration failed: {str(e)}",
                tenant_guid=auth_context.tenant_guid,
                target_url=request.service_url,
                response_received=None,
                processed_at=datetime.now(timezone.utc)
            )
    
    async def _make_callback(self, callback_url: str, data: Dict[str, Any], tenant_guid: str) -> bool:
        """
        Make callback to specified URL using authenticated HTTP client
        Matches C# TestController.MakeCallback
        
        Args:
            callback_url: URL to send callback to
            data: Data to send in callback
            tenant_guid: Tenant GUID for authentication
            
        Returns:
            True if callback successful, False otherwise
        """
        try:
            await self._send_authenticated_request(callback_url, data, tenant_guid)
            logger.info(f"Callback sent successfully to {callback_url} for tenant {tenant_guid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send callback to {callback_url} for tenant {tenant_guid}: {e}")
            return False
    
    async def _send_authenticated_request(
        self, 
        url: str, 
        data: Dict[str, Any], 
        tenant_guid: str
    ) -> Optional[str]:
        """
        Send authenticated HTTP request (matches C# D3HttpClient functionality)
        
        Args:
            url: Target URL
            data: Data to send
            tenant_guid: Tenant GUID for authentication
            
        Returns:
            Response content as string
            
        Raises:
            Exception: If request fails
        """
        try:
            # Generate service token for authentication
            token = await self.auth_service.generate_service_authentication(
                tenant_guid=tenant_guid,
                service_name="CommandService",
                permissions=[],
                expiration_minutes=30
            )
            
            if not token:
                raise Exception("Failed to generate authentication token")
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Tenant-GUID": tenant_guid,
                "X-Source-Service": "Python-SDK"
            }
            
            # Send request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
                    
                    return await response.text()
                    
        except Exception as e:
            logger.error(f"Authenticated request failed to {url}: {e}")
            raise

def create_test_endpoints(auth_service: AuthService, tenant_service: TenantService) -> APIRouter:
    """
    Factory function to create test endpoints router
    
    Args:
        auth_service: Authentication service
        tenant_service: Tenant service
        
    Returns:
        FastAPI router with test endpoints
    """
    controller = TestController(auth_service, tenant_service)
    return controller.router

# Alias for backward compatibility
TestEndpoints = create_test_endpoints