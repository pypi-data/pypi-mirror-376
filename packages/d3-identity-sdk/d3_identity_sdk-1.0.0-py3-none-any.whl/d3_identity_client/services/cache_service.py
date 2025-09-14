"""
Cache service for D3 Identity Service client
Provides high-performance caching with TTL and LRU eviction
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Any, Set
from datetime import datetime, timedelta
from ..models.config import CacheConfiguration, CacheType

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class CacheEntry:
    """Cache entry with TTL support"""
    
    def __init__(self, value: Any, ttl_seconds: Optional[int] = None):
        self.value = value
        self.created_at = time.time()
        self.expires_at = None
        
        if ttl_seconds and ttl_seconds > 0:
            self.expires_at = self.created_at + ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def time_to_expiry(self) -> Optional[float]:
        """Get seconds until expiry"""
        if self.expires_at is None:
            return None
        return max(0, self.expires_at - time.time())

class MemoryCache:
    """In-memory LRU cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.data: Dict[str, CacheEntry] = {}
        self.access_order: Dict[str, float] = {}  # key -> last_access_time
        self.lock = asyncio.Lock()
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_expired())
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self.lock:
            entry = self.data.get(key)
            
            if entry is None:
                return None
            
            if entry.is_expired():
                # Remove expired entry
                del self.data[key]
                self.access_order.pop(key, None)
                return None
            
            # Update access time
            self.access_order[key] = time.time()
            return entry.value
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in cache"""
        async with self.lock:
            if ttl_seconds is None:
                ttl_seconds = self.default_ttl
            
            # Create cache entry
            entry = CacheEntry(value, ttl_seconds)
            
            # Check if we need to evict entries
            if len(self.data) >= self.max_size and key not in self.data:
                await self._evict_lru()
            
            # Store entry
            self.data[key] = entry
            self.access_order[key] = time.time()
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        async with self.lock:
            if key in self.data:
                del self.data[key]
                self.access_order.pop(key, None)
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self.lock:
            self.data.clear()
            self.access_order.clear()
    
    async def keys(self) -> Set[str]:
        """Get all cache keys"""
        async with self.lock:
            return set(self.data.keys())
    
    async def size(self) -> int:
        """Get cache size"""
        async with self.lock:
            return len(self.data)
    
    async def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.access_order:
            return
        
        # Find LRU key
        lru_key = min(self.access_order.keys(), key=lambda k: self.access_order[k])
        
        # Remove LRU entry
        del self.data[lru_key]
        del self.access_order[lru_key]
        
        logger.debug(f"Evicted LRU key: {lru_key}")
    
    async def _cleanup_expired(self):
        """Background task to cleanup expired entries"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                async with self.lock:
                    expired_keys = []
                    current_time = time.time()
                    
                    for key, entry in self.data.items():
                        if entry.is_expired():
                            expired_keys.append(key)
                    
                    # Remove expired keys
                    for key in expired_keys:
                        del self.data[key]
                        self.access_order.pop(key, None)
                    
                    if expired_keys:
                        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
    
    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, '_cleanup_task') and not self._cleanup_task.done():
            self._cleanup_task.cancel()

class RedisCache:
    """Redis-based cache implementation"""
    
    def __init__(self, config: CacheConfiguration):
        if not REDIS_AVAILABLE:
            raise ImportError("redis package is required for Redis cache")
        
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = config.tenant_info_ttl_minutes * 60
        
    async def connect(self) -> bool:
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                self.config.get_redis_url(),
                max_connections=self.config.redis_connection_pool_size,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        try:
            if not self.redis_client:
                await self.connect()
            
            value = await self.redis_client.get(f"d3_identity:{key}")
            return value
            
        except Exception as e:
            logger.error(f"Redis get failed for key '{key}': {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in Redis cache"""
        try:
            if not self.redis_client:
                await self.connect()
            
            if ttl_seconds is None:
                ttl_seconds = self.default_ttl
            
            await self.redis_client.setex(
                f"d3_identity:{key}",
                ttl_seconds,
                str(value)
            )
            
        except Exception as e:
            logger.error(f"Redis set failed for key '{key}': {e}")
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache"""
        try:
            if not self.redis_client:
                await self.connect()
            
            result = await self.redis_client.delete(f"d3_identity:{key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis delete failed for key '{key}': {e}")
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        try:
            if not self.redis_client:
                await self.connect()
            
            # Delete all keys with our prefix
            keys = await self.redis_client.keys("d3_identity:*")
            if keys:
                await self.redis_client.delete(*keys)
                
        except Exception as e:
            logger.error(f"Redis clear failed: {e}")
    
    async def keys(self) -> Set[str]:
        """Get all cache keys"""
        try:
            if not self.redis_client:
                await self.connect()
            
            redis_keys = await self.redis_client.keys("d3_identity:*")
            # Remove prefix from keys
            return {key.replace("d3_identity:", "") for key in redis_keys}
            
        except Exception as e:
            logger.error(f"Redis keys failed: {e}")
            return set()
    
    async def size(self) -> int:
        """Get cache size"""
        keys = await self.keys()
        return len(keys)

class HybridCache:
    """Hybrid cache using memory + Redis fallback"""
    
    def __init__(self, config: CacheConfiguration):
        self.memory_cache = MemoryCache(
            max_size=min(config.max_cache_size, 500),  # Limit memory cache
            default_ttl=config.tenant_info_ttl_minutes * 60
        )
        
        if REDIS_AVAILABLE:
            self.redis_cache = RedisCache(config)
        else:
            self.redis_cache = None
            logger.warning("Redis not available, using memory-only cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (memory first, then Redis)"""
        # Try memory cache first
        value = await self.memory_cache.get(key)
        if value is not None:
            return value
        
        # Fallback to Redis
        if self.redis_cache:
            value = await self.redis_cache.get(key)
            if value is not None:
                # Populate memory cache
                await self.memory_cache.set(key, value)
                return value
        
        return None
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in both caches"""
        # Set in memory cache
        await self.memory_cache.set(key, value, ttl_seconds)
        
        # Set in Redis cache
        if self.redis_cache:
            await self.redis_cache.set(key, value, ttl_seconds)
    
    async def delete(self, key: str) -> bool:
        """Delete key from both caches"""
        memory_result = await self.memory_cache.delete(key)
        redis_result = True
        
        if self.redis_cache:
            redis_result = await self.redis_cache.delete(key)
        
        return memory_result or redis_result
    
    async def clear(self) -> None:
        """Clear both caches"""
        await self.memory_cache.clear()
        if self.redis_cache:
            await self.redis_cache.clear()
    
    async def keys(self) -> Set[str]:
        """Get all cache keys from both caches"""
        memory_keys = await self.memory_cache.keys()
        
        if self.redis_cache:
            redis_keys = await self.redis_cache.keys()
            return memory_keys.union(redis_keys)
        
        return memory_keys
    
    async def size(self) -> int:
        """Get total cache size"""
        keys = await self.keys()
        return len(keys)

class CacheService:
    """Main cache service with configurable backends"""
    
    def __init__(self, config: CacheConfiguration):
        self.config = config
        
        # Initialize cache backend based on configuration
        if config.cache_type == CacheType.MEMORY:
            self.cache = MemoryCache(
                max_size=config.max_cache_size,
                default_ttl=config.tenant_info_ttl_minutes * 60
            )
        elif config.cache_type == CacheType.REDIS:
            self.cache = RedisCache(config)
        elif config.cache_type == CacheType.HYBRID:
            self.cache = HybridCache(config)
        else:
            raise ValueError(f"Unsupported cache type: {config.cache_type}")
        
        logger.info(f"CacheService initialized with {config.cache_type.value} backend")
    
    async def get_tenant_info(self, tenant_guid: str) -> Optional[str]:
        """Get tenant info from cache"""
        return await self.cache.get(f"tenant:{tenant_guid}")
    
    async def set_tenant_info(self, tenant_guid: str, tenant_info: str) -> None:
        """Set tenant info in cache"""
        await self.cache.set(
            f"tenant:{tenant_guid}", 
            tenant_info, 
            self.config.tenant_info_ttl_minutes * 60
        )
    
    async def get_jwt_validation(self, token_hash: str) -> Optional[str]:
        """Get JWT validation result from cache"""
        return await self.cache.get(f"jwt:{token_hash}")
    
    async def set_jwt_validation(self, token_hash: str, validation_result: str) -> None:
        """Set JWT validation result in cache"""
        await self.cache.set(
            f"jwt:{token_hash}", 
            validation_result, 
            self.config.jwt_validation_ttl_minutes * 60
        )
    
    async def get_configuration(self, config_key: str) -> Optional[str]:
        """Get configuration from cache"""
        return await self.cache.get(f"config:{config_key}")
    
    async def set_configuration(self, config_key: str, config_value: str) -> None:
        """Set configuration in cache"""
        await self.cache.set(
            f"config:{config_key}", 
            config_value, 
            self.config.configuration_ttl_minutes * 60
        )
    
    async def invalidate_tenant(self, tenant_guid: str) -> None:
        """Invalidate all cached data for a tenant"""
        await self.cache.delete(f"tenant:{tenant_guid}")
        # Could also invalidate related JWT validations, etc.
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        size = await self.cache.size()
        keys = await self.cache.keys()
        
        return {
            "cache_type": self.config.cache_type.value,
            "total_entries": size,
            "tenant_entries": len([k for k in keys if k.startswith("tenant:")]),
            "jwt_entries": len([k for k in keys if k.startswith("jwt:")]),
            "config_entries": len([k for k in keys if k.startswith("config:")]),
            "max_size": self.config.max_cache_size,
        }
    
    async def clear_all(self) -> None:
        """Clear all cached data"""
        await self.cache.clear()
        logger.info("All cache data cleared")
    
    async def disconnect(self):
        """Disconnect from cache backend"""
        if hasattr(self.cache, 'disconnect'):
            await self.cache.disconnect()
        elif hasattr(self.cache, 'redis_cache') and self.cache.redis_cache:
            await self.cache.redis_cache.disconnect()