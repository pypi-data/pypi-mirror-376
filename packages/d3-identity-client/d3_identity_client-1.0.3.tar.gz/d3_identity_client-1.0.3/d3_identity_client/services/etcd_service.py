"""
etcd integration service for D3 Identity Service
Provides distributed configuration management and tenant data storage
"""

import asyncio
import json
import logging
from typing import Dict, Optional, Any, List, Callable, Awaitable
from datetime import datetime
import etcd3
from ..models.tenant import TenantInfo
from ..models.config import EtcdConfiguration
from ..utils.cache import LRUCache

logger = logging.getLogger(__name__)

class EtcdService:
    """
    etcd client service for distributed configuration and tenant management
    Provides CRUD operations, watching, and transaction support
    """
    
    def __init__(self, config: EtcdConfiguration):
        """
        Initialize etcd service
        
        Args:
            config: etcd configuration settings
        """
        self.config = config
        self.client: Optional[Any] = None
        self.watch_handles: Dict[str, Any] = {}
        self.is_connected = False
        self.connection_lock = asyncio.Lock()
        
        # Cache for frequently accessed data
        self.cache = LRUCache(max_size=1000, ttl_seconds=300)  # 5 minute TTL
        
        logger.info(f"EtcdService initialized with endpoints: {config.endpoints}")
    
    async def connect(self) -> bool:
        """
        Establish connection to etcd cluster
        
        Returns:
            True if connection successful, False otherwise
        """
        async with self.connection_lock:
            if self.is_connected and self.client:
                return True
            
            try:
                # Parse first endpoint for connection
                endpoint = self.config.endpoints[0]
                if '://' in endpoint:
                    # Remove protocol if present
                    endpoint = endpoint.split('://', 1)[1]
                
                host, port = endpoint.split(':')
                port = int(port)
                
                # Create etcd client
                self.client = etcd3.client(
                    host=host,
                    port=port,
                    timeout=self.config.timeout,
                    user=self.config.username,
                    password=self.config.password,
                    ca_cert=self.config.ca_cert,
                    cert_cert=self.config.cert_cert,
                    cert_key=self.config.cert_key
                )
                
                # Test connection
                await self.health_check()
                self.is_connected = True
                
                logger.info("Connected to etcd successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to connect to etcd: {e}")
                self.client = None
                self.is_connected = False
                return False
    
    async def disconnect(self):
        """Disconnect from etcd and cleanup resources"""
        async with self.connection_lock:
            try:
                # Stop all watches
                for key, handle in self.watch_handles.items():
                    try:
                        handle.cancel()
                    except:
                        pass
                self.watch_handles.clear()
                
                # Close client connection
                if self.client:
                    self.client.close()
                    self.client = None
                
                self.is_connected = False
                logger.info("Disconnected from etcd")
                
            except Exception as e:
                logger.error(f"Error during etcd disconnect: {e}")
    
    async def ensure_connected(self):
        """Ensure etcd connection is active"""
        if not self.is_connected:
            await self.connect()
        
        if not self.is_connected:
            raise ConnectionError("Failed to establish etcd connection")
    
    async def health_check(self) -> bool:
        """
        Check etcd cluster health
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self.client:
                return False
            
            # Simple status check
            status = self.client.status()
            logger.debug(f"etcd status: leader={status.leader}, version={status.version}")
            return True
            
        except Exception as e:
            logger.error(f"etcd health check failed: {e}")
            return False
    
    async def get(self, key: str, use_cache: bool = True) -> Optional[str]:
        """
        Get value from etcd
        
        Args:
            key: Key to retrieve
            use_cache: Whether to use local cache
            
        Returns:
            Value as string or None if not found
        """
        try:
            await self.ensure_connected()
            
            # Check cache first
            if use_cache:
                cached_value = self.cache.get(key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for key: {key}")
                    return cached_value
            
            # Get from etcd
            value, metadata = self.client.get(key)
            
            if value is not None:
                value_str = value.decode('utf-8')
                
                # Update cache
                if use_cache:
                    self.cache.set(key, value_str)
                
                logger.debug(f"Retrieved key from etcd: {key}")
                return value_str
            else:
                logger.debug(f"Key not found: {key}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get key '{key}': {e}")
            raise
    
    async def put(self, key: str, value: str) -> bool:
        """
        Put value to etcd
        
        Args:
            key: Key to store
            value: Value to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.ensure_connected()
            
            # Store in etcd
            result = self.client.put(key, value)
            
            # Update cache
            self.cache.set(key, value)
            
            logger.debug(f"Stored key in etcd: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to put key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from etcd
        
        Args:
            key: Key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.ensure_connected()
            
            # Delete from etcd
            result = self.client.delete(key)
            
            # Remove from cache
            self.cache.delete(key)
            
            logger.debug(f"Deleted key from etcd: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete key '{key}': {e}")
            return False
    
    async def get_prefix(self, prefix: str, use_cache: bool = False) -> Dict[str, str]:
        """
        Get all keys with specified prefix
        
        Args:
            prefix: Key prefix to search for
            use_cache: Whether to use local cache (not recommended for prefix queries)
            
        Returns:
            Dictionary of key-value pairs
        """
        try:
            await self.ensure_connected()
            
            results = {}
            
            # Get all keys with prefix
            for value, metadata in self.client.get_prefix(prefix):
                key = metadata.key.decode('utf-8')
                value_str = value.decode('utf-8')
                results[key] = value_str
                
                # Update cache
                if use_cache:
                    self.cache.set(key, value_str)
            
            logger.debug(f"Retrieved {len(results)} keys with prefix: {prefix}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get prefix '{prefix}': {e}")
            raise
    
    async def watch(
        self, 
        key: str, 
        callback: Callable[[str, Optional[str], str], Awaitable[None]]
    ) -> str:
        """
        Watch for changes to a key
        
        Args:
            key: Key to watch
            callback: Async callback function (key, value, event_type)
            
        Returns:
            Watch handle ID for cancellation
        """
        try:
            await self.ensure_connected()
            
            # Create watch handle
            watch_id = f"watch_{len(self.watch_handles)}"
            
            async def watch_callback(event):
                try:
                    event_key = event.key.decode('utf-8')
                    
                    if hasattr(event, 'value') and event.value:
                        event_value = event.value.decode('utf-8') if event.value else None
                        event_type = "PUT"
                        
                        # Update cache
                        if event_value:
                            self.cache.set(event_key, event_value)
                    
                    else:
                        event_value = None
                        event_type = "DELETE"
                        
                        # Remove from cache
                        self.cache.delete(event_key)
                    
                    # Call user callback
                    await callback(event_key, event_value, event_type)
                    
                except Exception as e:
                    logger.error(f"Error in watch callback for key '{key}': {e}")
            
            # Start watching
            watch_handle = self.client.add_watch_callback(key, watch_callback)
            self.watch_handles[watch_id] = watch_handle
            
            logger.info(f"Started watching key: {key}")
            return watch_id
            
        except Exception as e:
            logger.error(f"Failed to watch key '{key}': {e}")
            raise
    
    async def watch_prefix(
        self, 
        prefix: str, 
        callback: Callable[[str, Optional[str], str], Awaitable[None]]
    ) -> str:
        """
        Watch for changes to all keys with prefix
        
        Args:
            prefix: Key prefix to watch
            callback: Async callback function (key, value, event_type)
            
        Returns:
            Watch handle ID for cancellation
        """
        try:
            await self.ensure_connected()
            
            # Create watch handle
            watch_id = f"watch_prefix_{len(self.watch_handles)}"
            
            async def watch_callback(event):
                try:
                    event_key = event.key.decode('utf-8')
                    
                    if hasattr(event, 'value') and event.value:
                        event_value = event.value.decode('utf-8') if event.value else None
                        event_type = "PUT"
                        
                        # Update cache
                        if event_value:
                            self.cache.set(event_key, event_value)
                    
                    else:
                        event_value = None
                        event_type = "DELETE"
                        
                        # Remove from cache
                        self.cache.delete(event_key)
                    
                    # Call user callback
                    await callback(event_key, event_value, event_type)
                    
                except Exception as e:
                    logger.error(f"Error in watch callback for prefix '{prefix}': {e}")
            
            # Start watching prefix
            watch_handle = self.client.add_watch_prefix_callback(prefix, watch_callback)
            self.watch_handles[watch_id] = watch_handle
            
            logger.info(f"Started watching prefix: {prefix}")
            return watch_id
            
        except Exception as e:
            logger.error(f"Failed to watch prefix '{prefix}': {e}")
            raise
    
    async def cancel_watch(self, watch_id: str) -> bool:
        """
        Cancel a watch
        
        Args:
            watch_id: Watch handle ID returned from watch()
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            if watch_id in self.watch_handles:
                handle = self.watch_handles[watch_id]
                handle.cancel()
                del self.watch_handles[watch_id]
                logger.info(f"Cancelled watch: {watch_id}")
                return True
            else:
                logger.warning(f"Watch handle not found: {watch_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to cancel watch '{watch_id}': {e}")
            return False
    
    async def transaction(
        self, 
        conditions: List[Any], 
        success_ops: List[Any], 
        failure_ops: List[Any] = None
    ) -> bool:
        """
        Execute atomic transaction
        
        Args:
            conditions: List of conditions to check
            success_ops: Operations to perform if conditions are met
            failure_ops: Operations to perform if conditions are not met
            
        Returns:
            True if transaction succeeded, False otherwise
        """
        try:
            await self.ensure_connected()
            
            if failure_ops is None:
                failure_ops = []
            
            # Execute transaction
            result = self.client.transaction(
                compare=conditions,
                success=success_ops,
                failure=failure_ops
            )
            
            logger.debug(f"Transaction result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return False
    
    async def lease_grant(self, ttl: int) -> Optional[int]:
        """
        Grant a lease with TTL
        
        Args:
            ttl: Time to live in seconds
            
        Returns:
            Lease ID or None if failed
        """
        try:
            await self.ensure_connected()
            
            lease = self.client.lease(ttl)
            logger.debug(f"Granted lease {lease.id} with TTL {ttl}")
            return lease.id
            
        except Exception as e:
            logger.error(f"Failed to grant lease: {e}")
            return None
    
    async def lease_revoke(self, lease_id: int) -> bool:
        """
        Revoke a lease
        
        Args:
            lease_id: Lease ID to revoke
            
        Returns:
            True if revoked successfully, False otherwise
        """
        try:
            await self.ensure_connected()
            
            self.client.revoke_lease(lease_id)
            logger.debug(f"Revoked lease: {lease_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke lease {lease_id}: {e}")
            return False
    
    def get_client_info(self) -> Dict[str, Any]:
        """
        Get etcd client information
        
        Returns:
            Dictionary with client information
        """
        return {
            "is_connected": self.is_connected,
            "endpoints": self.config.endpoints,
            "has_authentication": self.config.has_authentication(),
            "has_tls": self.config.has_tls(),
            "active_watches": len(self.watch_handles),
            "cache_size": len(self.cache.data) if hasattr(self.cache, 'data') else 0
        }