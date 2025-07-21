"""
Database service layer for handling Supabase operations
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import uuid

from database.supabase_client import get_supabase
from models.database import (
    Profile, ProfileCreate, ProfileUpdate,
    Brand, BrandCreate, BrandUpdate,
    Scan, ScanCreate, ScanUpdate,
    VisibilityResult, VisibilityResultCreate,
    AuditResult, AuditResultCreate,
    SimulationResult, SimulationResultCreate,
    CacheEntry, ScanStatus, ScanType
)

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service class for database operations"""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    # Profile operations
    async def get_profile(self, user_id: str) -> Optional[Profile]:
        """Get user profile by ID"""
        try:
            result = self.supabase.table('profiles').select('*').eq('id', user_id).execute()
            if result.data:
                return Profile(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting profile {user_id}: {e}")
            raise
    
    async def create_profile(self, user_id: str, profile_data: ProfileCreate) -> Profile:
        """Create a new user profile"""
        try:
            data = profile_data.dict()
            data['id'] = user_id
            
            result = self.supabase.table('profiles').insert(data).execute()
            return Profile(**result.data[0])
        except Exception as e:
            logger.error(f"Error creating profile for user {user_id}: {e}")
            raise
    
    async def update_profile(self, user_id: str, profile_data: ProfileUpdate) -> Profile:
        """Update user profile"""
        try:
            data = profile_data.dict(exclude_unset=True)
            if not data:
                # No updates provided, return current profile
                return await self.get_profile(user_id)
            
            result = self.supabase.table('profiles').update(data).eq('id', user_id).execute()
            return Profile(**result.data[0])
        except Exception as e:
            logger.error(f"Error updating profile {user_id}: {e}")
            raise
    
    async def update_scan_usage(self, user_id: str, increment: int = 1) -> Profile:
        """Update user's scan usage and remaining scans"""
        try:
            # Get current profile
            profile = await self.get_profile(user_id)
            if not profile:
                raise ValueError(f"Profile not found for user {user_id}")
            
            # Update scan counts
            new_scans_used = profile.scans_used + increment
            new_scans_remaining = max(0, profile.scans_remaining - increment)
            
            result = self.supabase.table('profiles').update({
                'scans_used': new_scans_used,
                'scans_remaining': new_scans_remaining
            }).eq('id', user_id).execute()
            
            return Profile(**result.data[0])
        except Exception as e:
            logger.error(f"Error updating scan usage for user {user_id}: {e}")
            raise
    
    # Brand operations
    async def get_user_brands(self, user_id: str) -> List[Brand]:
        """Get all brands for a user"""
        try:
            result = self.supabase.table('brands').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            return [Brand(**brand) for brand in result.data]
        except Exception as e:
            logger.error(f"Error getting brands for user {user_id}: {e}")
            raise
    
    async def get_brand(self, brand_id: str, user_id: str) -> Optional[Brand]:
        """Get a specific brand by ID (with user ownership check)"""
        try:
            result = self.supabase.table('brands').select('*').eq('id', brand_id).eq('user_id', user_id).execute()
            if result.data:
                return Brand(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting brand {brand_id}: {e}")
            raise
    
    async def create_brand(self, user_id: str, brand_data: BrandCreate) -> Brand:
        """Create a new brand"""
        try:
            data = brand_data.dict()
            data['user_id'] = user_id
            data['id'] = str(uuid.uuid4())
            
            result = self.supabase.table('brands').insert(data).execute()
            return Brand(**result.data[0])
        except Exception as e:
            logger.error(f"Error creating brand for user {user_id}: {e}")
            raise
    
    async def update_brand(self, brand_id: str, user_id: str, brand_data: BrandUpdate) -> Brand:
        """Update a brand"""
        try:
            data = brand_data.dict(exclude_unset=True)
            if not data:
                # No updates provided, return current brand
                return await self.get_brand(brand_id, user_id)
            
            result = self.supabase.table('brands').update(data).eq('id', brand_id).eq('user_id', user_id).execute()
            if not result.data:
                raise ValueError(f"Brand {brand_id} not found or access denied")
            return Brand(**result.data[0])
        except Exception as e:
            logger.error(f"Error updating brand {brand_id}: {e}")
            raise
    
    async def delete_brand(self, brand_id: str, user_id: str) -> bool:
        """Delete a brand"""
        try:
            result = self.supabase.table('brands').delete().eq('id', brand_id).eq('user_id', user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error deleting brand {brand_id}: {e}")
            raise
    
    # Scan operations
    async def get_user_scans(self, user_id: str, limit: int = 50) -> List[Scan]:
        """Get all scans for a user"""
        try:
            result = self.supabase.table('scans').select('*').eq('user_id', user_id).order('started_at', desc=True).limit(limit).execute()
            return [Scan(**scan) for scan in result.data]
        except Exception as e:
            logger.error(f"Error getting scans for user {user_id}: {e}")
            raise
    
    async def get_scan(self, scan_id: str, user_id: str) -> Optional[Scan]:
        """Get a specific scan by ID"""
        try:
            result = self.supabase.table('scans').select('*').eq('id', scan_id).eq('user_id', user_id).execute()
            if result.data:
                return Scan(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting scan {scan_id}: {e}")
            raise
    
    async def create_scan(self, user_id: str, scan_data: ScanCreate) -> Scan:
        """Create a new scan"""
        try:
            data = scan_data.dict()
            data['user_id'] = user_id
            data['id'] = str(uuid.uuid4())
            data['status'] = ScanStatus.PENDING
            data['progress'] = 0
            data['started_at'] = datetime.now().isoformat()
            
            result = self.supabase.table('scans').insert(data).execute()
            return Scan(**result.data[0])
        except Exception as e:
            logger.error(f"Error creating scan for user {user_id}: {e}")
            raise
    
    async def update_scan(self, scan_id: str, scan_data: ScanUpdate) -> Scan:
        """Update scan status and progress"""
        try:
            data = scan_data.dict(exclude_unset=True)
            if not data:
                raise ValueError("No update data provided")
            
            # Set completion time if status is completed or failed
            if 'status' in data and data['status'] in [ScanStatus.COMPLETED, ScanStatus.FAILED]:
                data['completed_at'] = datetime.now().isoformat()
            
            result = self.supabase.table('scans').update(data).eq('id', scan_id).execute()
            if not result.data:
                raise ValueError(f"Scan {scan_id} not found")
            return Scan(**result.data[0])
        except Exception as e:
            logger.error(f"Error updating scan {scan_id}: {e}")
            raise
    
    # Results operations
    async def create_visibility_result(self, result_data: VisibilityResultCreate) -> VisibilityResult:
        """Create visibility scan result"""
        try:
            data = result_data.dict()
            data['id'] = str(uuid.uuid4())
            
            result = self.supabase.table('visibility_results').insert(data).execute()
            return VisibilityResult(**result.data[0])
        except Exception as e:
            logger.error(f"Error creating visibility result: {e}")
            raise
    
    async def get_visibility_result(self, scan_id: str) -> Optional[VisibilityResult]:
        """Get visibility result by scan ID"""
        try:
            result = self.supabase.table('visibility_results').select('*').eq('scan_id', scan_id).execute()
            if result.data:
                return VisibilityResult(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting visibility result for scan {scan_id}: {e}")
            raise
    
    async def create_audit_result(self, result_data: AuditResultCreate) -> AuditResult:
        """Create audit scan result"""
        try:
            data = result_data.dict()
            data['id'] = str(uuid.uuid4())
            
            result = self.supabase.table('audit_results').insert(data).execute()
            return AuditResult(**result.data[0])
        except Exception as e:
            logger.error(f"Error creating audit result: {e}")
            raise
    
    async def get_audit_result(self, scan_id: str) -> Optional[AuditResult]:
        """Get audit result by scan ID"""
        try:
            result = self.supabase.table('audit_results').select('*').eq('scan_id', scan_id).execute()
            if result.data:
                return AuditResult(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting audit result for scan {scan_id}: {e}")
            raise
    
    async def create_simulation_results(self, results_data: List[SimulationResultCreate]) -> List[SimulationResult]:
        """Create multiple simulation results"""
        try:
            data = []
            for result_data in results_data:
                result_dict = result_data.dict()
                result_dict['id'] = str(uuid.uuid4())
                data.append(result_dict)
            
            result = self.supabase.table('simulation_results').insert(data).execute()
            return [SimulationResult(**item) for item in result.data]
        except Exception as e:
            logger.error(f"Error creating simulation results: {e}")
            raise
    
    async def get_simulation_results(self, scan_id: str) -> List[SimulationResult]:
        """Get simulation results by scan ID"""
        try:
            result = self.supabase.table('simulation_results').select('*').eq('scan_id', scan_id).order('created_at').execute()
            return [SimulationResult(**item) for item in result.data]
        except Exception as e:
            logger.error(f"Error getting simulation results for scan {scan_id}: {e}")
            raise
    
    # Cache operations
    async def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached LLM response"""
        try:
            result = self.supabase.table('llm_response_cache').select('*').eq('cache_key', cache_key).gt('expires_at', datetime.now().isoformat()).execute()
            
            if result.data:
                # Update access count
                cache_entry = result.data[0]
                self.supabase.table('llm_response_cache').update({
                    'access_count': cache_entry['access_count'] + 1
                }).eq('id', cache_entry['id']).execute()
                
                return cache_entry['response_data']
            return None
        except Exception as e:
            logger.error(f"Error getting cached response {cache_key}: {e}")
            raise
    
    async def cache_response(self, cache_key: str, response_data: Dict[str, Any], model_name: str, prompt_hash: str, ttl_hours: int = 24) -> bool:
        """Cache LLM response"""
        try:
            expires_at = datetime.now() + timedelta(hours=ttl_hours)
            
            data = {
                'id': str(uuid.uuid4()),
                'cache_key': cache_key,
                'response_data': response_data,
                'model_name': model_name,
                'prompt_hash': prompt_hash,
                'expires_at': expires_at.isoformat(),
                'access_count': 1
            }
            
            # Use upsert to handle duplicate keys
            result = self.supabase.table('llm_response_cache').upsert(data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error caching response {cache_key}: {e}")
            return False
    
    async def clean_expired_cache(self) -> int:
        """Clean expired cache entries"""
        try:
            result = self.supabase.rpc('clean_expired_cache').execute()
            return result.data if result.data else 0
        except Exception as e:
            logger.error(f"Error cleaning expired cache: {e}")
            return 0
    
    def generate_cache_key(self, model: str, prompt: str, brand: str, additional_params: Dict[str, Any] = None) -> str:
        """Generate consistent cache key for LLM requests"""
        content = f"{model}:{prompt}:{brand}"
        if additional_params:
            # Sort params for consistent key generation
            sorted_params = sorted(additional_params.items())
            params_str = ":".join([f"{k}={v}" for k, v in sorted_params])
            content += f":{params_str}"
        
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def generate_prompt_hash(self, prompt: str) -> str:
        """Generate hash for prompt content"""
        return hashlib.sha256(prompt.encode()).hexdigest()

# Global database service instance
db_service = DatabaseService()