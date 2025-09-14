"""
Caching utilities for D3 Identity Service client
"""

import time
import threading
from typing import Dict, Any, Optional, TypeVar, Generic

T = TypeVar('T')

class LRUCache(Generic[T]):
    """
    Thread-safe LRU cache with TTL support
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        """
        Initialize LRU cache
        
        Args:
            max_size: Maximum number of items to store
            ttl_seconds: Time to live for cached items
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        
        self.data: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {}
        self.access_order: Dict[str, float] = {}
        
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[T]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self.lock:
            if key not in self.data:
                return None
            
            # Check TTL
            if self._is_expired(key):
                self._remove_key(key)
                return None
            
            # Update access order
            self.access_order[key] = time.time()
            return self.data[key]
    
    def set(self, key: str, value: T) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            current_time = time.time()
            
            # If cache is at capacity and key is new, evict LRU item
            if len(self.data) >= self.max_size and key not in self.data:
                self._evict_lru()
            
            # Store value
            self.data[key] = value
            self.timestamps[key] = current_time
            self.access_order[key] = current_time
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        with self.lock:
            if key in self.data:
                self._remove_key(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cached items"""
        with self.lock:
            self.data.clear()
            self.timestamps.clear()
            self.access_order.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        with self.lock:
            return len(self.data)
    
    def keys(self) -> list:
        """Get list of all cache keys"""
        with self.lock:
            return list(self.data.keys())
    
    def cleanup_expired(self) -> int:
        """
        Remove expired items from cache
        
        Returns:
            Number of items removed
        """
        with self.lock:
            expired_keys = []
            current_time = time.time()
            
            for key, timestamp in self.timestamps.items():
                if current_time - timestamp > self.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove_key(key)
            
            return len(expired_keys)
    
    def _is_expired(self, key: str) -> bool:
        """Check if a key is expired"""
        if key not in self.timestamps:
            return True
        
        return (time.time() - self.timestamps[key]) > self.ttl_seconds
    
    def _evict_lru(self) -> None:
        """Evict least recently used item"""
        if not self.access_order:
            return
        
        # Find LRU key
        lru_key = min(self.access_order.keys(), key=lambda k: self.access_order[k])
        self._remove_key(lru_key)
    
    def _remove_key(self, key: str) -> None:
        """Remove key from all internal data structures"""
        self.data.pop(key, None)
        self.timestamps.pop(key, None)
        self.access_order.pop(key, None)

class ThreadSafeDict:
    """
    Thread-safe dictionary wrapper
    """
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key"""
        with self._lock:
            return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set value by key"""
        with self._lock:
            self._data[key] = value
    
    def delete(self, key: str) -> bool:
        """Delete key"""
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False
    
    def keys(self) -> list:
        """Get all keys"""
        with self._lock:
            return list(self._data.keys())
    
    def values(self) -> list:
        """Get all values"""
        with self._lock:
            return list(self._data.values())
    
    def items(self) -> list:
        """Get all key-value pairs"""
        with self._lock:
            return list(self._data.items())
    
    def clear(self) -> None:
        """Clear all data"""
        with self._lock:
            self._data.clear()
    
    def size(self) -> int:
        """Get size"""
        with self._lock:
            return len(self._data)