"""
Supabase-based caching service for LLM responses and other data
Implements persistent caching with TTL, statistics tracking, and cleanup
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hashlib
import json
import asyncio
from dataclasses import dataclass

from database.supabase_client import get_supabase
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@dataclass
class CacheStats:
    """Cache statistics data class"""
    total_entries: int
    hit_count: int
    miss_count: int
    expired_count: int
    total_size_mb: float
    hit_rate: float
    
@dataclass
class CacheEntry:
    """Cache entry data class"""
    cache_key: str
    response_data: Dict[str, Any]
    model_name: str
    prompt_hash: str
    created_at: datetime
    expires_at: datetime
    access_count: int
    size_bytes: int

class CacheService:
    """Service class for Supabase-based caching operations"""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.default_ttl_hours = settings.CACHE_TTL_HOURS
        self._stats_cache = {}
        self._stats_last_updated = None
    
    async def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached data by key"""
        try:
            # Query cache table with expiration check
            result = self.supabase.table('llm_response_cache').select('*').eq(
                'cache_key', cache_key
            ).gt('expires_at', datetime.now().isoformat()).execute()
            
            if result.data:
                cache_entry = result.data[0]
                
                # Update access count asynchronously
                asyncio.create_task(self._update_access_count(cache_entry['id']))
                
                logger.debug(f"Cache hit for key: {cache_key}")
                return cache_entry['response_data']
            
            logger.debug(f"Cache miss for key: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {cache_key}: {e}")
            return None
    
    async def set(
        self, 
        cache_key: str, 
        data: Dict[str, Any], 
        model_name: str = "default",
        prompt_text: str = "",
        ttl_hours: Optional[int] = None
    ) -> bool:
        """Set cached data with TTL"""
        try:
            ttl = ttl_hours or self.default_ttl_hours
            expires_at = datetime.now() + timedelta(hours=ttl)
            prompt_hash = self._generate_prompt_hash(prompt_text)
            
            # Calculate approximate size
            data_size = len(json.dumps(data).encode('utf-8'))
            
            cache_data = {
                'cache_key': cache_key,
                'response_data': data,
                'model_name': model_name,
                'prompt_hash': prompt_hash,
                'expires_at': expires_at.isoformat(),
                'access_count': 1,
                'size_bytes': data_size
            }
            
            # Use upsert to handle duplicate keys
            result = self.supabase.table('llm_response_cache').upsert(
                cache_data, 
                on_conflict='cache_key'
            ).execute()
            
            logger.debug(f"Cache set for key: {cache_key}, TTL: {ttl}h")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Cache set error for key {cache_key}: {e}")
            return False
    
    async def delete(self, cache_key: str) -> bool:
        """Delete cached data by key"""
        try:
            result = self.supabase.table('llm_response_cache').delete().eq(
                'cache_key', cache_key
            ).execute()
            
            logger.debug(f"Cache delete for key: {cache_key}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Cache delete error for key {cache_key}: {e}")
            return False
    
    async def exists(self, cache_key: str) -> bool:
        """Check if cache key exists and is not expired"""
        try:
            result = self.supabase.table('llm_response_cache').select('id').eq(
                'cache_key', cache_key
            ).gt('expires_at', datetime.now().isoformat()).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Cache exists check error for key {cache_key}: {e}")
            return False
    
    async def clear_expired(self) -> int:
        """Clear expired cache entries"""
        try:
            # Use the database function for efficient cleanup
            result = self.supabase.rpc('clean_expired_cache').execute()
            
            deleted_count = result.data if result.data else 0
            logger.info(f"Cleared {deleted_count} expired cache entries")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            return 0
    
    async def clear_all(self) -> bool:
        """Clear all cache entries (use with caution)"""
        try:
            result = self.supabase.table('llm_response_cache').delete().neq(
                'id', '00000000-0000-0000-0000-000000000000'  # Delete all
            ).execute()
            
            logger.warning("All cache entries cleared")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear all error: {e}")
            return False
    
    async def get_stats(self, force_refresh: bool = False) -> CacheStats:
        """Get cache statistics"""
        try:
            # Use cached stats if available and recent (within 5 minutes)
            if (not force_refresh and 
                self._stats_last_updated and 
                datetime.now() - self._stats_last_updated < timedelta(minutes=5)):
                return self._stats_cache
            
            # Query cache statistics
            stats_query = """
            SELECT 
                COUNT(*) as total_entries,
                COUNT(CASE WHEN expires_at > NOW() THEN 1 END) as active_entries,
                COUNT(CASE WHEN expires_at <= NOW() THEN 1 END) as expired_entries,
                SUM(access_count) as total_accesses,
                SUM(size_bytes) as total_size_bytes,
                AVG(access_count) as avg_access_count
            FROM llm_response_cache
            """
            
            result = self.supabase.rpc('execute_sql', {'query': stats_query}).execute()
            
            if result.data:
                stats_data = result.data[0]
                
                total_entries = stats_data.get('total_entries', 0)
                total_accesses = stats_data.get('total_accesses', 0)
                total_size_bytes = stats_data.get('total_size_bytes', 0)
                
                # Calculate hit rate (approximation based on access patterns)
                hit_rate = 0.0
                if total_entries > 0:
                    avg_access = stats_data.get('avg_access_count', 1)
                    hit_rate = min(1.0, (avg_access - 1) / avg_access) if avg_access > 1 else 0.0
                
                cache_stats = CacheStats(
                    total_entries=total_entries,
                    hit_count=int(total_accesses * hit_rate) if total_accesses else 0,
                    miss_count=int(total_accesses * (1 - hit_rate)) if total_accesses else 0,
                    expired_count=stats_data.get('expired_entries', 0),
                    total_size_mb=total_size_bytes / (1024 * 1024) if total_size_bytes else 0.0,
                    hit_rate=hit_rate
                )
                
                # Cache the stats
                self._stats_cache = cache_stats
                self._stats_last_updated = datetime.now()
                
                return cache_stats
            
            # Return empty stats if no data
            return CacheStats(0, 0, 0, 0, 0.0, 0.0)
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return CacheStats(0, 0, 0, 0, 0.0, 0.0)
    
    async def get_entries_by_model(self, model_name: str, limit: int = 100) -> List[CacheEntry]:
        """Get cache entries for a specific model"""
        try:
            result = self.supabase.table('llm_response_cache').select('*').eq(
                'model_name', model_name
            ).order('created_at', desc=True).limit(limit).execute()
            
            entries = []
            for entry_data in result.data:
                entry = CacheEntry(
                    cache_key=entry_data['cache_key'],
                    response_data=entry_data['response_data'],
                    model_name=entry_data['model_name'],
                    prompt_hash=entry_data['prompt_hash'],
                    created_at=datetime.fromisoformat(entry_data['created_at'].replace('Z', '+00:00')),
                    expires_at=datetime.fromisoformat(entry_data['expires_at'].replace('Z', '+00:00')),
                    access_count=entry_data['access_count'],
                    size_bytes=entry_data.get('size_bytes', 0)
                )
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Get entries by model error for {model_name}: {e}")
            return []
    
    async def get_popular_entries(self, limit: int = 50) -> List[CacheEntry]:
        """Get most frequently accessed cache entries"""
        try:
            result = self.supabase.table('llm_response_cache').select('*').order(
                'access_count', desc=True
            ).limit(limit).execute()
            
            entries = []
            for entry_data in result.data:
                entry = CacheEntry(
                    cache_key=entry_data['cache_key'],
                    response_data=entry_data['response_data'],
                    model_name=entry_data['model_name'],
                    prompt_hash=entry_data['prompt_hash'],
                    created_at=datetime.fromisoformat(entry_data['created_at'].replace('Z', '+00:00')),
                    expires_at=datetime.fromisoformat(entry_data['expires_at'].replace('Z', '+00:00')),
                    access_count=entry_data['access_count'],
                    size_bytes=entry_data.get('size_bytes', 0)
                )
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Get popular entries error: {e}")
            return []
    
    def generate_cache_key(
        self, 
        model: str, 
        prompt: str, 
        brand: str, 
        additional_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate consistent cache key for LLM requests"""
        content = f"{model}:{prompt}:{brand}"
        
        if additional_params:
            # Sort params for consistent key generation
            sorted_params = sorted(additional_params.items())
            params_str = ":".join([f"{k}={v}" for k, v in sorted_params])
            content += f":{params_str}"
        
        # Generate SHA256 hash and truncate to 32 characters
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _generate_prompt_hash(self, prompt: str) -> str:
        """Generate hash for prompt content"""
        return hashlib.sha256(prompt.encode()).hexdigest()
    
    async def _update_access_count(self, cache_id: str) -> None:
        """Update access count for cache entry (async)"""
        try:
            self.supabase.table('llm_response_cache').update({
                'access_count': 'access_count + 1'
            }).eq('id', cache_id).execute()
            
        except Exception as e:
            logger.error(f"Access count update error for {cache_id}: {e}")
    
    async def warm_cache(self, entries: List[Dict[str, Any]]) -> int:
        """Warm cache with predefined entries"""
        try:
            warmed_count = 0
            
            for entry in entries:
                cache_key = self.generate_cache_key(
                    entry['model'],
                    entry['prompt'],
                    entry['brand'],
                    entry.get('params')
                )
                
                success = await self.set(
                    cache_key,
                    entry['response_data'],
                    entry['model'],
                    entry['prompt'],
                    entry.get('ttl_hours')
                )
                
                if success:
                    warmed_count += 1
            
            logger.info(f"Cache warmed with {warmed_count} entries")
            return warmed_count
            
        except Exception as e:
            logger.error(f"Cache warming error: {e}")
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check"""
        try:
            # Test basic operations
            test_key = "health_check_test"
            test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
            
            # Test set
            set_success = await self.set(test_key, test_data, "test_model", "test prompt", 1)
            
            # Test get
            retrieved_data = await self.get(test_key)
            get_success = retrieved_data is not None
            
            # Test delete
            delete_success = await self.delete(test_key)
            
            # Get stats
            stats = await self.get_stats()
            
            return {
                "status": "healthy" if all([set_success, get_success, delete_success]) else "unhealthy",
                "operations": {
                    "set": set_success,
                    "get": get_success,
                    "delete": delete_success
                },
                "stats": {
                    "total_entries": stats.total_entries,
                    "hit_rate": stats.hit_rate,
                    "total_size_mb": stats.total_size_mb
                }
            }
            
        except Exception as e:
            logger.error(f"Cache health check error: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Global cache service instance
cache_service = CacheService()

# Convenience functions for common operations
async def get_cached_llm_response(
    model: str, 
    prompt: str, 
    brand: str, 
    params: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Get cached LLM response"""
    cache_key = cache_service.generate_cache_key(model, prompt, brand, params)
    return await cache_service.get(cache_key)

async def cache_llm_response(
    model: str, 
    prompt: str, 
    brand: str, 
    response_data: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None,
    ttl_hours: Optional[int] = None
) -> bool:
    """Cache LLM response"""
    cache_key = cache_service.generate_cache_key(model, prompt, brand, params)
    return await cache_service.set(cache_key, response_data, model, prompt, ttl_hours)

async def clear_expired_cache() -> int:
    """Clear expired cache entries"""
    return await cache_service.clear_expired()

async def get_cache_stats() -> CacheStats:
    """Get cache statistics"""
    return await cache_service.get_stats()