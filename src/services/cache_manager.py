"""
Cache Manager for Medical Chatbot

Provides in-memory LRU caching with TTL support to reduce latency
and API costs by caching search results and generated responses.
"""

import time
import re
import hashlib
import logging
from typing import Any, Optional, Dict
from functools import lru_cache
from collections import OrderedDict
from threading import Lock

logger = logging.getLogger(__name__)


class CacheEntry:
    """Represents a cached item with TTL"""
    
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expiry = time.time() + ttl if ttl > 0 else float('inf')
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() > self.expiry


class CacheManager:
    """
    Thread-safe LRU cache with TTL support
    
    Features:
    - LRU eviction when cache is full
    - TTL (Time To Live) for automatic expiration
    - Thread-safe operations
    - Cache statistics tracking
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize cache manager
        
        Args:
            max_size: Maximum number of entries in cache
        """
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = Lock()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        logger.info(f"Cache manager initialized with max_size={max_size}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            entry = self.cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self.cache[key]
                self.misses += 1
                logger.debug(f"Cache expired: {key}")
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            logger.debug(f"Cache hit: {key}")
            return entry.value
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 1 hour)
        """
        with self.lock:
            # Remove if already exists
            if key in self.cache:
                del self.cache[key]
            
            # Evict oldest if cache is full
            if len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.evictions += 1
                logger.debug(f"Cache evicted: {oldest_key}")
            
            # Add new entry
            self.cache[key] = CacheEntry(value, ttl)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }
    
    def reset_stats(self) -> None:
        """Reset cache statistics"""
        with self.lock:
            self.hits = 0
            self.misses = 0
            self.evictions = 0
            logger.info("Cache statistics reset")


def normalize_query(query: str) -> str:
    """
    Normalize query for consistent cache keys
    
    Args:
        query: User query
        
    Returns:
        Normalized query string
        
    Examples:
        "Triệu chứng sốt xuất huyết?" -> "trieu_chung_sot_xuat_huyet"
        "TRIỆU CHỨNG SỐT XUẤT HUYẾT" -> "trieu_chung_sot_xuat_huyet"
    """
    # Lowercase
    normalized = query.lower().strip()
    
    # Remove punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Remove extra spaces
    normalized = ' '.join(normalized.split())
    
    # Replace spaces with underscore
    normalized = normalized.replace(' ', '_')
    
    return normalized


def generate_cache_key(prefix: str, query: str, **kwargs) -> str:
    """
    Generate cache key with prefix and normalized query
    
    Args:
        prefix: Key prefix (e.g., 'search', 'response')
        query: User query
        **kwargs: Additional parameters to include in key
        
    Returns:
        Cache key string
    """
    normalized = normalize_query(query)
    
    # Add kwargs to key if provided
    if kwargs:
        # Sort kwargs for consistent keys
        sorted_kwargs = sorted(kwargs.items())
        kwargs_str = '_'.join(f"{k}={v}" for k, v in sorted_kwargs)
        key = f"{prefix}:{normalized}:{kwargs_str}"
    else:
        key = f"{prefix}:{normalized}"
    
    # Hash if key is too long
    if len(key) > 200:
        key_hash = hashlib.md5(key.encode()).hexdigest()
        key = f"{prefix}:{key_hash}"
    
    return key


# Global cache instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(max_size: int = 1000) -> CacheManager:
    """
    Get or create global cache manager instance
    
    Args:
        max_size: Maximum cache size (only used on first call)
        
    Returns:
        CacheManager instance
    """
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager(max_size=max_size)
    
    return _cache_manager
