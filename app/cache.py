import hashlib
import json
import logging
from typing import Optional, Dict, Any
from cachetools import TTLCache
from app.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Simple in-memory cache manager"""
    
    def __init__(self, ttl: int = 604800, maxsize: int = 1000):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.enabled = settings.cache_enabled
    
    def get_key(self, query: str, params: Dict[str, Any]) -> str:
        """Generate cache key from query and parameters"""
        key_data = {
            'query': query,
            **params
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached result"""
        if not self.enabled:
            return None
        
        result = self.cache.get(key)
        if result:
            logger.info(f"Cache hit for key: {key}")
        return result
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Store result in cache"""
        if not self.enabled:
            return
        
        self.cache[key] = value
        logger.info(f"Cached result for key: {key}")
    
    def clear(self) -> None:
        """Clear all cached results"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "enabled": self.enabled,
            "size": len(self.cache),
            "maxsize": self.cache.maxsize,
            "ttl": self.cache.ttl
        }


# Global cache instance
cache_manager = CacheManager(ttl=settings.cache_ttl)
