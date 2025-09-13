"""
Main D3 Identity Service client implementation
Provides high-level interface for all Identity Service functionality
"""

import asyncio
import logging
from typing import Dict, Optional, Any, List, Callable, Awaitable
from datetime import datetime
from .models.tenant import TenantInfo, InternalServices
from .models.auth import (
    JwtClaims, TokenValidationResult, AuthenticationContext,
    ServiceRegistrationInfo, TokenGenerationResponse
)
from .models.config import IdentityServiceOptions
from .services.etcd_service import EtcdService
from .services.cache_service import CacheService
from .services.jwt_service import JwtService
from .services.tenant_service import TenantService
from .services.auth_service import AuthService
from .utils.config import load_config_from_environment

logger = logging.getLogger(__name__)

class D3IdentityClient:
    """
    Main client for D3 Identity Service integration
    Provides unified interface for all Identity Service functionality
    """
    
    def __init__(self, config: Optional[IdentityServiceOptions] = None):
        """
        Initialize D3 Identity Service client
        
        Args:
            config: Configuration options (loads from environment if None)
        """
        # Load configuration
        self.config = config or load_config_from_environment()
        
        # Validate configuration
        validation_errors = self.config.validate()
        if validation_errors:
            raise ValueError(f"Configuration validation failed: {validation_errors}")
        
        # Initialize services
        self.etcd_service: Optional[EtcdService] = None
        self.cache_service: Optional[CacheService] = None
        self.jwt_service: Optional[JwtService] = None
        self.tenant_service: Optional[TenantService] = None
        self.auth_service: Optional[AuthService] = None
        
        # Initialize logging
        self._setup_logging()
        
        # State tracking
        self.is_initialized = False
        self.current_tenant: Optional[TenantInfo] = None
        
        logger.info(f"D3IdentityClient created for tenant: {self.config.tenant_guid}")
    
    async def initialize(self) -> bool:
        """
        Initialize all services and establish connections
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if self.is_initialized:
                logger.debug("Client already initialized")
                return True
            
            logger.info("Initializing D3 Identity Service client...")
            
            # Initialize etcd service
            if not self.config.mock_etcd_for_testing:
                self.etcd_service = EtcdService(self.config.etcd)
                if not await self.etcd_service.connect():
                    logger.error("Failed to connect to etcd")
                    return False
                logger.debug("etcd service initialized")
            else:
                logger.warning("Using mock etcd for testing")
                # Could implement mock etcd service here
                return False
            
            # Initialize cache service
            if self.config.enable_configuration_caching:
                self.cache_service = CacheService(self.config.cache)
                logger.debug("Cache service initialized")
            
            # Initialize JWT service
            self.jwt_service = JwtService(
                etcd_service=self.etcd_service,
                cache_service=self.cache_service,
                security_config=self.config.security
            )
            logger.debug("JWT service initialized")
            
            # Initialize tenant service
            self.tenant_service = TenantService(
                etcd_service=self.etcd_service,
                cache_service=self.cache_service
            )
            logger.debug("Tenant service initialized")
            
            # Initialize auth service
            self.auth_service = AuthService(
                jwt_service=self.jwt_service,
                tenant_service=self.tenant_service
            )
            logger.debug("Auth service initialized")
            
            # Load current tenant information
            if self.config.tenant_guid:
                await self._initialize_current_tenant()
            
            # Register service if configured
            if (self.config.service and 
                self.config.service.enable_service_registration):
                await self._register_service()
            
            # Set up tenant watching if enabled
            if (self.config.enable_tenant_watching and 
                self.config.tenant_guid):
                await self._setup_tenant_watching()
            
            self.is_initialized = True
            logger.info("D3 Identity Service client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize D3 Identity Service client: {e}")
            await self.cleanup()
            return False
    
    async def cleanup(self):
        """Clean up resources and connections"""
        try:
            logger.info("Cleaning up D3 Identity Service client...")
            
            # Cleanup services in reverse order
            if self.tenant_service:
                await self.tenant_service.cleanup_resources()
            
            if self.cache_service:
                await self.cache_service.disconnect()
            
            if self.etcd_service:
                await self.etcd_service.disconnect()
            
            self.is_initialized = False
            logger.info("D3 Identity Service client cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    # Tenant Operations
    async def get_tenant_info(self, tenant_guid: Optional[str] = None) -> Optional[TenantInfo]:
        """
        Get tenant information
        
        Args:
            tenant_guid: Tenant GUID (uses current tenant if None)
            
        Returns:
            TenantInfo object or None if not found
        """
        if not self._ensure_initialized():
            return None
        
        guid = tenant_guid or self.config.tenant_guid
        if not guid:
            logger.error("No tenant GUID provided")
            return None
        
        return await self.tenant_service.get_tenant(guid)
    
    async def get_multiple_tenants(self, tenant_guids: List[str]) -> Dict[str, Optional[TenantInfo]]:
        """
        Get multiple tenants in batch
        
        Args:
            tenant_guids: List of tenant GUIDs
            
        Returns:
            Dictionary mapping GUID to TenantInfo
        """
        if not self._ensure_initialized():
            return {}
        
        return await self.tenant_service.get_multiple_tenants(tenant_guids)
    
    async def watch_tenant(
        self, 
        tenant_guid: str, 
        callback: Callable[[TenantInfo], Awaitable[None]]
    ) -> bool:
        """
        Watch tenant for configuration changes
        
        Args:
            tenant_guid: Tenant GUID to watch
            callback: Async callback function for changes
            
        Returns:
            True if watch established, False otherwise
        """
        if not self._ensure_initialized():
            return False
        
        return await self.tenant_service.watch_tenant(tenant_guid, callback)
    
    # JWT Operations
    async def generate_token(
        self, 
        claims: Dict[str, Any],
        tenant_guid: Optional[str] = None,
        expiration_minutes: int = 30
    ) -> Optional[TokenGenerationResponse]:
        """
        Generate JWT token
        
        Args:
            claims: Token claims
            tenant_guid: Target tenant (uses current if None)
            expiration_minutes: Token expiration
            
        Returns:
            TokenGenerationResponse or None if failed
        """
        if not self._ensure_initialized():
            return None
        
        guid = tenant_guid or self.config.tenant_guid
        if not guid:
            logger.error("No tenant GUID provided for token generation")
            return None
        
        return await self.jwt_service.generate_token(
            tenant_guid=guid,
            claims=claims,
            expiration_minutes=expiration_minutes
        )
    
    async def validate_token(self, token: str) -> TokenValidationResult:
        """
        Validate JWT token
        
        Args:
            token: JWT token to validate
            
        Returns:
            TokenValidationResult with validation details
        """
        if not self._ensure_initialized():
            return TokenValidationResult(is_valid=False, error_message="Client not initialized")
        
        return await self.jwt_service.validate_token(token)
    
    async def generate_service_token(
        self,
        service_name: str,
        tenant_guid: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        expiration_minutes: int = 30
    ) -> Optional[str]:
        """
        Generate service-to-service token
        
        Args:
            service_name: Name of requesting service
            tenant_guid: Target tenant (uses current if None)
            permissions: Service permissions
            expiration_minutes: Token expiration
            
        Returns:
            JWT token string or None if failed
        """
        if not self._ensure_initialized():
            return None
        
        return await self.auth_service.generate_service_authentication(
            tenant_guid=tenant_guid or self.config.tenant_guid,
            service_name=service_name,
            permissions=permissions,
            expiration_minutes=expiration_minutes
        )
    
    # Authentication Operations
    async def authenticate_token(self, token: str) -> Optional[AuthenticationContext]:
        """
        Authenticate any valid token
        
        Args:
            token: JWT token to authenticate
            
        Returns:
            AuthenticationContext or None if failed
        """
        if not self._ensure_initialized():
            return None
        
        return await self.auth_service.authenticate_any_token(token)
    
    async def authenticate_service_token(
        self, 
        token: str,
        required_service: Optional[str] = None,
        required_permissions: Optional[List[str]] = None
    ) -> Optional[AuthenticationContext]:
        """
        Authenticate service token
        
        Args:
            token: Service JWT token
            required_service: Required service name
            required_permissions: Required permissions
            
        Returns:
            AuthenticationContext or None if failed
        """
        if not self._ensure_initialized():
            return None
        
        return await self.auth_service.authenticate_service_token(
            token, required_service, required_permissions
        )
    
    # Service Registration
    async def register_internal_service(
        self,
        service_name: str,
        service_endpoints: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Register as internal service
        
        Args:
            service_name: Service name to register
            service_endpoints: Service endpoints (http, grpc, etc.)
            
        Returns:
            True if registration successful, False otherwise
        """
        if not self._ensure_initialized():
            return False
        
        return await self.tenant_service.register_internal_service(
            service_name=service_name,
            tenant_guid=self.config.tenant_guid,
            service_endpoints=service_endpoints
        )
    
    async def get_internal_service_info(self, service_name: str) -> Optional[ServiceRegistrationInfo]:
        """
        Get internal service registration info
        
        Args:
            service_name: Service name to lookup
            
        Returns:
            ServiceRegistrationInfo or None if not found
        """
        if not self._ensure_initialized():
            return None
        
        return await self.tenant_service.get_internal_service_info(service_name)
    
    async def get_all_internal_services(self) -> Dict[str, ServiceRegistrationInfo]:
        """
        Get all registered internal services
        
        Returns:
            Dictionary mapping service name to registration info
        """
        if not self._ensure_initialized():
            return {}
        
        return await self.tenant_service.get_all_internal_services()
    
    # Health and Status
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check
        
        Returns:
            Dictionary with health status of all components
        """
        health_status = {
            "client_initialized": self.is_initialized,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if not self.is_initialized:
            health_status["status"] = "unhealthy"
            return health_status
        
        try:
            # Check etcd connectivity
            if self.etcd_service:
                etcd_healthy = await self.etcd_service.health_check()
                health_status["etcd"] = "healthy" if etcd_healthy else "unhealthy"
            else:
                health_status["etcd"] = "not_configured"
            
            # Check cache status
            if self.cache_service:
                cache_stats = await self.cache_service.get_cache_stats()
                health_status["cache"] = {
                    "status": "healthy",
                    "stats": cache_stats
                }
            else:
                health_status["cache"] = "not_configured"
            
            # Check current tenant
            if self.current_tenant:
                health_status["current_tenant"] = {
                    "guid": self.current_tenant.tenant_guid,
                    "name": self.current_tenant.tenant_name,
                    "active": self.current_tenant.is_active_tenant()
                }
            
            # Overall status
            overall_healthy = all([
                health_status["etcd"] in ["healthy", "not_configured"],
                health_status["cache"] != "unhealthy"
            ])
            health_status["status"] = "healthy" if overall_healthy else "unhealthy"
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    # Properties
    @property
    def current_tenant_info(self) -> Optional[TenantInfo]:
        """Get current tenant information"""
        return self.current_tenant
    
    @property
    def tenant_guid(self) -> Optional[str]:
        """Get current tenant GUID"""
        return self.config.tenant_guid
    
    @property
    def is_ready(self) -> bool:
        """Check if client is ready for use"""
        return self.is_initialized and self.etcd_service and self.etcd_service.is_connected
    
    # Private helper methods
    def _ensure_initialized(self) -> bool:
        """Ensure client is initialized"""
        if not self.is_initialized:
            logger.error("Client not initialized. Call initialize() first.")
            return False
        return True
    
    async def _initialize_current_tenant(self):
        """Initialize current tenant information"""
        try:
            self.current_tenant = await self.tenant_service.get_tenant(self.config.tenant_guid)
            if self.current_tenant:
                logger.info(f"Loaded current tenant: {self.current_tenant.tenant_name}")
            else:
                logger.warning(f"Current tenant not found: {self.config.tenant_guid}")
        except Exception as e:
            logger.error(f"Failed to load current tenant: {e}")
    
    async def _register_service(self):
        """Register this service with Identity Service"""
        try:
            if not self.config.service:
                return
            
            service_endpoints = {}
            if self.config.service.http_port:
                service_endpoints["http"] = f"http://localhost:{self.config.service.http_port}"
            if self.config.service.grpc_port:
                service_endpoints["grpc"] = f"grpc://localhost:{self.config.service.grpc_port}"
            
            success = await self.register_internal_service(
                service_name=self.config.service.service_name,
                service_endpoints=service_endpoints
            )
            
            if success:
                logger.info(f"Registered service: {self.config.service.service_name}")
            else:
                logger.warning(f"Failed to register service: {self.config.service.service_name}")
                
        except Exception as e:
            logger.error(f"Service registration failed: {e}")
    
    async def _setup_tenant_watching(self):
        """Set up tenant configuration watching"""
        try:
            async def tenant_change_callback(updated_tenant: TenantInfo):
                logger.info(f"Tenant configuration updated: {updated_tenant.tenant_name}")
                self.current_tenant = updated_tenant
            
            success = await self.tenant_service.watch_tenant(
                self.config.tenant_guid, 
                tenant_change_callback
            )
            
            if success:
                logger.info("Tenant watching enabled")
            else:
                logger.warning("Failed to enable tenant watching")
                
        except Exception as e:
            logger.error(f"Failed to setup tenant watching: {e}")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        try:
            log_config = self.config.logging
            
            # Set log level
            logging.getLogger().setLevel(log_config.log_level.value)
            
            # Create formatters
            if log_config.enable_json_logging:
                # JSON formatter would go here
                formatter = logging.Formatter(log_config.log_format)
            else:
                formatter = logging.Formatter(log_config.log_format)
            
            # Console handler
            if log_config.log_to_console:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                logging.getLogger().addHandler(console_handler)
            
            # File handler
            if log_config.log_to_file and log_config.log_file_path:
                file_handler = logging.FileHandler(log_config.log_file_path)
                file_handler.setFormatter(formatter)
                logging.getLogger().addHandler(file_handler)
            
        except Exception as e:
            print(f"Failed to setup logging: {e}")  # Use print since logging may not be working
    

    # Controller Integration Methods
    def create_fastapi_router(self):
        """
        Create FastAPI router with SDK test endpoints
        Matches C# IdentityServiceSDK TestController functionality
        
        Returns:
            FastAPI APIRouter with /identitysdk/test and /identitysdk/register endpoints
        """
        if not self._ensure_initialized():
            raise Exception("Client not initialized")
        
        from .controllers.test_controller import create_test_endpoints
        return create_test_endpoints(self.auth_service, self.tenant_service)
    
    def create_grpc_servicer(self):
        """
        Create gRPC servicer with SDK test endpoints
        Matches C# IdentitySdkClientGrpcController functionality
        
        Returns:
            gRPC servicer with TestConnection method
        """
        if not self._ensure_initialized():
            raise Exception("Client not initialized")
        
        from .controllers.grpc_controller import create_grpc_servicer
        return create_grpc_servicer(self.auth_service, self.tenant_service)
    
    async def test_service_endpoint(
        self, 
        service_url: str, 
        callback_url: Optional[str] = None,
        test_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Test another service's /identitysdk/test endpoint
        Matches C# TestController.RegisterEndpoint functionality
        
        Args:
            service_url: Target service URL
            callback_url: Optional callback URL
            test_data: Optional test data to send
            
        Returns:
            Dictionary with test results
        """
        if not self._ensure_initialized():
            raise Exception("Client not initialized")
        
        from .controllers.test_controller import TestController
        controller = TestController(self.auth_service, self.tenant_service)
        
        # Create mock auth context from current client
        class MockAuthContext:
            def __init__(self, tenant_guid):
                self.tenant_guid = tenant_guid
        
        auth_context = MockAuthContext(self.config.tenant_guid)
        
        from .controllers.test_controller import RegisterRequest
        register_request = RegisterRequest(
            service_url=service_url,
            callback_url=callback_url,
            message="Test from Python SDK client"
        )
        
        response = await controller.register(register_request, auth_context)
        return response.dict()

    # Context manager support
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()

# Convenience function
async def create_client(config: Optional[IdentityServiceOptions] = None) -> D3IdentityClient:
    """
    Create and initialize D3 Identity Service client
    
    Args:
        config: Configuration options (loads from environment if None)
        
    Returns:
        Initialized D3IdentityClient
        
    Raises:
        Exception: If initialization fails
    """
    client = D3IdentityClient(config)
    
    if not await client.initialize():
        await client.cleanup()
        raise Exception("Failed to initialize D3 Identity Service client")
    
    return client