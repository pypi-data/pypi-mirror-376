"""
Tenant service for D3 Identity Service
Provides tenant management, configuration, and service registration
"""

import json
import logging
from typing import Dict, Optional, List, Callable, Awaitable, Any
from datetime import datetime
from ..models.tenant import TenantInfo, InternalServices
from ..models.auth import ServiceRegistrationInfo
from ..services.etcd_service import EtcdService
from ..services.cache_service import CacheService

logger = logging.getLogger(__name__)

class TenantService:
    """
    Tenant management service providing CRUD operations and real-time updates
    """
    
    def __init__(
        self, 
        etcd_service: EtcdService, 
        cache_service: Optional[CacheService] = None
    ):
        """
        Initialize tenant service
        
        Args:
            etcd_service: etcd service for distributed storage
            cache_service: Optional cache service for performance
        """
        self.etcd_service = etcd_service
        self.cache_service = cache_service
        self.tenant_watchers: Dict[str, str] = {}  # tenant_guid -> watch_id
        self.tenant_callbacks: Dict[str, List[Callable]] = {}  # tenant_guid -> callbacks
        
        logger.info("TenantService initialized")
    
    async def get_tenant(self, tenant_guid: str) -> Optional[TenantInfo]:
        """
        Get tenant information by GUID
        
        Args:
            tenant_guid: Tenant GUID to retrieve
            
        Returns:
            TenantInfo object or None if not found
        """
        try:
            # Check cache first
            if self.cache_service:
                cached_tenant = await self.cache_service.get_tenant_info(tenant_guid)
                if cached_tenant:
                    logger.debug(f"Tenant cache hit: {tenant_guid}")
                    return TenantInfo.from_dict(json.loads(cached_tenant))
            
            # Get from etcd
            tenant_key = f"tenants/{tenant_guid}"
            tenant_data = await self.etcd_service.get(tenant_key)
            
            if tenant_data:
                tenant_info = TenantInfo.from_dict(json.loads(tenant_data))
                
                # Cache for future use
                if self.cache_service:
                    await self.cache_service.set_tenant_info(
                        tenant_guid, 
                        json.dumps(tenant_info.to_dict())
                    )
                
                logger.debug(f"Retrieved tenant from etcd: {tenant_guid}")
                return tenant_info
            
            logger.debug(f"Tenant not found: {tenant_guid}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_guid}: {e}")
            return None
    
    async def get_multiple_tenants(self, tenant_guids: List[str]) -> Dict[str, Optional[TenantInfo]]:
        """
        Get multiple tenants in a single batch operation
        
        Args:
            tenant_guids: List of tenant GUIDs to retrieve
            
        Returns:
            Dictionary mapping tenant GUID to TenantInfo (or None if not found)
        """
        results = {}
        
        try:
            # For each tenant, try to get from cache first, then etcd
            for tenant_guid in tenant_guids:
                tenant_info = await self.get_tenant(tenant_guid)
                results[tenant_guid] = tenant_info
            
            logger.debug(f"Retrieved {len([t for t in results.values() if t])} of {len(tenant_guids)} tenants")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get multiple tenants: {e}")
            # Return partial results if any were successful
            return results
    
    async def get_active_tenant_guids(self) -> List[str]:
        """
        Get list of all active tenant GUIDs
        
        Returns:
            List of active tenant GUIDs
        """
        try:
            # Get all tenants with prefix
            tenant_data = await self.etcd_service.get_prefix("tenants/")
            
            active_guids = []
            for key, value in tenant_data.items():
                try:
                    tenant_info = TenantInfo.from_dict(json.loads(value))
                    if tenant_info.is_active_tenant():
                        # Extract GUID from key (tenants/{guid})
                        tenant_guid = key.split('/')[-1]
                        active_guids.append(tenant_guid)
                except Exception as e:
                    logger.warning(f"Failed to parse tenant data for key {key}: {e}")
            
            logger.debug(f"Found {len(active_guids)} active tenants")
            return active_guids
            
        except Exception as e:
            logger.error(f"Failed to get active tenant GUIDs: {e}")
            return []
    
    async def watch_tenant(
        self, 
        tenant_guid: str, 
        callback: Callable[[TenantInfo], Awaitable[None]]
    ) -> bool:
        """
        Watch for changes to a specific tenant
        
        Args:
            tenant_guid: Tenant GUID to watch
            callback: Async callback function to call on changes
            
        Returns:
            True if watch was established, False otherwise
        """
        try:
            if tenant_guid in self.tenant_watchers:
                logger.warning(f"Already watching tenant: {tenant_guid}")
                return True
            
            tenant_key = f"tenants/{tenant_guid}"
            
            async def watch_callback(key: str, value: Optional[str], event_type: str):
                try:
                    if event_type == "PUT" and value:
                        tenant_info = TenantInfo.from_dict(json.loads(value))
                        
                        # Update cache
                        if self.cache_service:
                            await self.cache_service.set_tenant_info(
                                tenant_guid, 
                                value
                            )
                        
                        # Call user callback
                        await callback(tenant_info)
                        
                        # Call other registered callbacks
                        if tenant_guid in self.tenant_callbacks:
                            for cb in self.tenant_callbacks[tenant_guid]:
                                try:
                                    await cb(tenant_info)
                                except Exception as e:
                                    logger.error(f"Error in tenant callback: {e}")
                    
                    elif event_type == "DELETE":
                        # Remove from cache
                        if self.cache_service:
                            await self.cache_service.invalidate_tenant(tenant_guid)
                        
                        logger.info(f"Tenant deleted: {tenant_guid}")
                    
                except Exception as e:
                    logger.error(f"Error in tenant watch callback: {e}")
            
            # Start watching
            watch_id = await self.etcd_service.watch(tenant_key, watch_callback)
            self.tenant_watchers[tenant_guid] = watch_id
            
            # Initialize callbacks list
            if tenant_guid not in self.tenant_callbacks:
                self.tenant_callbacks[tenant_guid] = []
            
            logger.info(f"Started watching tenant: {tenant_guid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to watch tenant {tenant_guid}: {e}")
            return False
    
    async def stop_watching_tenant(self, tenant_guid: str) -> bool:
        """
        Stop watching a tenant for changes
        
        Args:
            tenant_guid: Tenant GUID to stop watching
            
        Returns:
            True if watch was stopped, False otherwise
        """
        try:
            if tenant_guid not in self.tenant_watchers:
                logger.warning(f"Not watching tenant: {tenant_guid}")
                return True
            
            watch_id = self.tenant_watchers[tenant_guid]
            success = await self.etcd_service.cancel_watch(watch_id)
            
            if success:
                del self.tenant_watchers[tenant_guid]
                # Keep callbacks for potential future watching
                logger.info(f"Stopped watching tenant: {tenant_guid}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to stop watching tenant {tenant_guid}: {e}")
            return False
    
    async def add_tenant_change_callback(
        self, 
        tenant_guid: str, 
        callback: Callable[[TenantInfo], Awaitable[None]]
    ) -> bool:
        """
        Add additional callback for tenant changes
        
        Args:
            tenant_guid: Tenant GUID
            callback: Async callback function
            
        Returns:
            True if callback was added
        """
        try:
            if tenant_guid not in self.tenant_callbacks:
                self.tenant_callbacks[tenant_guid] = []
            
            self.tenant_callbacks[tenant_guid].append(callback)
            
            # Start watching if not already watching
            if tenant_guid not in self.tenant_watchers:
                await self.watch_tenant(tenant_guid, lambda t: None)  # Dummy callback
            
            logger.debug(f"Added callback for tenant: {tenant_guid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add tenant callback: {e}")
            return False
    
    async def register_internal_service(
        self,
        service_name: str,
        tenant_guid: Optional[str] = None,
        service_endpoints: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Register an internal service with the Identity Service
        
        Args:
            service_name: Name of the service to register
            tenant_guid: Optional tenant GUID for tenant-specific services
            service_endpoints: Service endpoints (http, grpc, etc.)
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Validate service name
            try:
                service_enum = InternalServices(service_name)
            except ValueError:
                logger.error(f"Invalid service name: {service_name}")
                return False
            
            # Create service registration info
            service_info = ServiceRegistrationInfo(
                service_name=service_name,
                tenant_guid=tenant_guid,
                service_endpoints=service_endpoints or {},
                registration_timestamp=datetime.utcnow(),
                is_active=True
            )
            
            # Store in etcd
            service_key = f"internal-services/{service_name}"
            if tenant_guid:
                service_key += f"/{tenant_guid}"
            
            service_data = json.dumps(service_info.to_dict())
            success = await self.etcd_service.put(service_key, service_data)
            
            if success:
                logger.info(f"Registered internal service: {service_name}")
                return True
            else:
                logger.error(f"Failed to register internal service: {service_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to register internal service {service_name}: {e}")
            return False
    
    async def get_internal_service_info(self, service_name: str) -> Optional[ServiceRegistrationInfo]:
        """
        Get internal service registration information
        
        Args:
            service_name: Name of the service
            
        Returns:
            ServiceRegistrationInfo or None if not found
        """
        try:
            service_key = f"internal-services/{service_name}"
            service_data = await self.etcd_service.get(service_key)
            
            if service_data:
                service_info = ServiceRegistrationInfo.from_dict(json.loads(service_data))
                logger.debug(f"Retrieved internal service info: {service_name}")
                return service_info
            
            logger.debug(f"Internal service not found: {service_name}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get internal service info {service_name}: {e}")
            return None
    
    async def get_all_internal_services(self) -> Dict[str, ServiceRegistrationInfo]:
        """
        Get all registered internal services
        
        Returns:
            Dictionary mapping service name to ServiceRegistrationInfo
        """
        try:
            services_data = await self.etcd_service.get_prefix("internal-services/")
            
            services = {}
            for key, value in services_data.items():
                try:
                    service_info = ServiceRegistrationInfo.from_dict(json.loads(value))
                    # Extract service name from key
                    service_name = key.split('/')[-1]
                    if '/' in service_name:  # Handle tenant-specific services
                        service_name = service_name.split('/')[0]
                    
                    services[service_name] = service_info
                    
                except Exception as e:
                    logger.warning(f"Failed to parse service data for key {key}: {e}")
            
            logger.debug(f"Retrieved {len(services)} internal services")
            return services
            
        except Exception as e:
            logger.error(f"Failed to get internal services: {e}")
            return {}
    
    async def watch_internal_services(
        self, 
        callback: Callable[[str, Optional[ServiceRegistrationInfo], str], Awaitable[None]]
    ) -> Optional[str]:
        """
        Watch for changes to internal service registrations
        
        Args:
            callback: Async callback (service_name, service_info, event_type)
            
        Returns:
            Watch handle ID or None if failed
        """
        try:
            async def watch_callback(key: str, value: Optional[str], event_type: str):
                try:
                    # Extract service name from key (internal-services/{service_name})
                    service_name = key.split('/')[-1]
                    
                    if event_type == "PUT" and value:
                        service_info = ServiceRegistrationInfo.from_dict(json.loads(value))
                        await callback(service_name, service_info, "UPDATED")
                    
                    elif event_type == "DELETE":
                        await callback(service_name, None, "DELETED")
                    
                except Exception as e:
                    logger.error(f"Error in internal services watch callback: {e}")
            
            # Watch all internal services
            watch_id = await self.etcd_service.watch_prefix("internal-services/", watch_callback)
            
            if watch_id:
                logger.info("Started watching internal services")
                return watch_id
            else:
                logger.error("Failed to start watching internal services")
                return None
                
        except Exception as e:
            logger.error(f"Failed to watch internal services: {e}")
            return None
    
    async def update_tenant_configuration(
        self, 
        tenant_guid: str, 
        configuration_updates: Dict[str, Any]
    ) -> bool:
        """
        Update tenant configuration
        
        Args:
            tenant_guid: Tenant GUID
            configuration_updates: Dictionary of configuration updates
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Get current tenant info
            tenant_info = await self.get_tenant(tenant_guid)
            if not tenant_info:
                logger.error(f"Tenant not found for configuration update: {tenant_guid}")
                return False
            
            # Apply configuration updates
            if not tenant_info.configurations:
                tenant_info.configurations = {}
            
            tenant_info.configurations.update(configuration_updates)
            tenant_info.updated_at = datetime.utcnow()
            tenant_info.version += 1
            
            # Store updated tenant info
            tenant_key = f"tenants/{tenant_guid}"
            tenant_data = json.dumps(tenant_info.to_dict())
            success = await self.etcd_service.put(tenant_key, tenant_data)
            
            if success:
                # Invalidate cache
                if self.cache_service:
                    await self.cache_service.invalidate_tenant(tenant_guid)
                
                logger.info(f"Updated tenant configuration: {tenant_guid}")
                return True
            else:
                logger.error(f"Failed to update tenant configuration: {tenant_guid}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update tenant configuration {tenant_guid}: {e}")
            return False
    
    async def get_tenant_children(self, parent_tenant_guid: str) -> List[TenantInfo]:
        """
        Get all child tenants for a parent tenant
        
        Args:
            parent_tenant_guid: Parent tenant GUID
            
        Returns:
            List of child TenantInfo objects
        """
        try:
            # Get all tenants
            tenant_data = await self.etcd_service.get_prefix("tenants/")
            
            children = []
            for key, value in tenant_data.items():
                try:
                    tenant_info = TenantInfo.from_dict(json.loads(value))
                    if tenant_info.parent_tenant_guid == parent_tenant_guid:
                        children.append(tenant_info)
                except Exception as e:
                    logger.warning(f"Failed to parse tenant data for key {key}: {e}")
            
            logger.debug(f"Found {len(children)} child tenants for {parent_tenant_guid}")
            return children
            
        except Exception as e:
            logger.error(f"Failed to get child tenants for {parent_tenant_guid}: {e}")
            return []
    
    async def cleanup_resources(self):
        """Clean up resources and stop all watches"""
        try:
            # Stop all tenant watches
            for tenant_guid, watch_id in list(self.tenant_watchers.items()):
                await self.etcd_service.cancel_watch(watch_id)
            
            self.tenant_watchers.clear()
            self.tenant_callbacks.clear()
            
            logger.info("TenantService resources cleaned up")
            
        except Exception as e:
            logger.error(f"Error during TenantService cleanup: {e}")