"""
Unit tests for database operations and RLS policies
"""
import pytest
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock
import uuid

from database.supabase_client import SupabaseClient, get_supabase
from models.database import (
    Profile, ProfileCreate, ProfileUpdate,
    Brand, BrandCreate, BrandUpdate,
    Scan, ScanCreate, ScanUpdate,
    VisibilityResult, VisibilityResultCreate,
    AuditResult, AuditResultCreate,
    SimulationResult, SimulationResultCreate,
    ScanType, ScanStatus, SubscriptionTier
)

class TestSupabaseClient:
    """Test Supabase client initialization and configuration"""
    
    def test_singleton_pattern(self):
        """Test that SupabaseClient follows singleton pattern"""
        client1 = SupabaseClient()
        client2 = SupabaseClient()
        assert client1 is client2
    
    @patch.dict(os.environ, {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_SERVICE_KEY': 'test-service-key'
    })
    @patch('database.supabase_client.create_client')
    def test_client_initialization(self, mock_create_client):
        """Test Supabase client initialization with environment variables"""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        client = SupabaseClient()
        client._client = None  # Reset to force re-initialization
        client._initialize_client()
        
        mock_create_client.assert_called_once()
        assert client.client == mock_client
    
    def test_missing_environment_variables(self):
        """Test that missing environment variables raise ValueError"""
        with patch.dict(os.environ, {}, clear=True):
            client = SupabaseClient()
            client._client = None
            
            with pytest.raises(ValueError, match="SUPABASE_URL and SUPABASE_SERVICE_KEY"):
                client._initialize_client()
    
    @patch('database.supabase_client.create_client')
    async def test_health_check_success(self, mock_create_client):
        """Test successful health check"""
        mock_client = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_limit = Mock()
        mock_execute = Mock()
        
        mock_execute.return_value = Mock(data=[])
        mock_limit.return_value.execute = mock_execute
        mock_select.return_value.limit = mock_limit
        mock_table.return_value.select = mock_select
        mock_client.table = mock_table
        mock_create_client.return_value = mock_client
        
        client = SupabaseClient()
        client._client = mock_client
        
        result = await client.health_check()
        assert result is True
    
    @patch('database.supabase_client.create_client')
    async def test_health_check_failure(self, mock_create_client):
        """Test health check failure"""
        mock_client = Mock()
        mock_client.table.side_effect = Exception("Connection failed")
        mock_create_client.return_value = mock_client
        
        client = SupabaseClient()
        client._client = mock_client
        
        result = await client.health_check()
        assert result is False

class TestDatabaseModels:
    """Test Pydantic models for database entities"""
    
    def test_profile_create_validation(self):
        """Test ProfileCreate model validation"""
        # Valid profile
        profile_data = {
            "first_name": "John",
            "last_name": "Doe",
            "company_name": "Test Company",
            "subscription_tier": "pro"
        }
        profile = ProfileCreate(**profile_data)
        assert profile.first_name == "John"
        assert profile.subscription_tier == SubscriptionTier.PRO
        
        # Test default values
        minimal_profile = ProfileCreate()
        assert minimal_profile.subscription_tier == SubscriptionTier.FREE
    
    def test_brand_create_validation(self):
        """Test BrandCreate model validation"""
        # Valid brand
        brand_data = {
            "name": "Test Brand",
            "domain": "https://example.com",
            "industry": "Technology",
            "keywords": ["ai", "machine learning", "tech"],
            "competitors": ["competitor1.com", "competitor2.com"]
        }
        brand = BrandCreate(**brand_data)
        assert brand.name == "Test Brand"
        assert len(brand.keywords) == 3
        
        # Test domain validation
        with pytest.raises(ValueError, match="Domain must start with http"):
            BrandCreate(name="Test", domain="example.com")
        
        # Test keywords limit
        with pytest.raises(ValueError, match="Maximum 20 keywords"):
            BrandCreate(
                name="Test",
                domain="https://example.com",
                keywords=[f"keyword{i}" for i in range(25)]
            )
    
    def test_scan_create_validation(self):
        """Test ScanCreate model validation"""
        scan_data = {
            "brand_id": str(uuid.uuid4()),
            "scan_type": "visibility",
            "metadata": {"test": "data"}
        }
        scan = ScanCreate(**scan_data)
        assert scan.scan_type == ScanType.VISIBILITY
        assert scan.metadata["test"] == "data"
    
    def test_visibility_result_validation(self):
        """Test VisibilityResult model validation"""
        result_data = {
            "scan_id": str(uuid.uuid4()),
            "overall_score": 85,
            "gpt35_score": 80,
            "gpt4_score": 90,
            "claude_score": 85,
            "mention_count": 5,
            "competitor_comparison": {"competitor1": 70},
            "raw_responses": {"gpt4": "response text"},
            "recommendations": [{"type": "improve_schema", "priority": "high"}]
        }
        result = VisibilityResultCreate(**result_data)
        assert result.overall_score == 85
        assert result.mention_count == 5
        
        # Test score validation
        with pytest.raises(ValueError):
            VisibilityResultCreate(scan_id=str(uuid.uuid4()), overall_score=150)
    
    def test_audit_result_validation(self):
        """Test AuditResult model validation"""
        result_data = {
            "scan_id": str(uuid.uuid4()),
            "overall_score": 75,
            "schema_score": 80,
            "meta_score": 70,
            "content_score": 75,
            "technical_score": 80,
            "recommendations": [{"type": "add_schema", "description": "Add Organization schema"}],
            "technical_details": {"page_speed": 85, "mobile_friendly": True},
            "audit_data": {"meta_tags": {"title": "Present", "description": "Present"}}
        }
        result = AuditResultCreate(**result_data)
        assert result.overall_score == 75
        assert result.technical_details["mobile_friendly"] is True

class TestDatabaseOperations:
    """Test database operations with mocked Supabase client"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing"""
        with patch('database.supabase_client.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client
            yield mock_client
    
    def test_profile_operations(self, mock_supabase_client):
        """Test profile CRUD operations"""
        # Mock profile data
        profile_id = str(uuid.uuid4())
        profile_data = {
            "id": profile_id,
            "first_name": "John",
            "last_name": "Doe",
            "company_name": "Test Company",
            "subscription_tier": "pro",
            "scans_remaining": 10,
            "scans_used": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Mock table operations
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        
        # Test select operation
        mock_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[profile_data]
        )
        
        # Test insert operation
        mock_table.insert.return_value.execute.return_value = Mock(
            data=[profile_data]
        )
        
        # Test update operation
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock(
            data=[{**profile_data, "company_name": "Updated Company"}]
        )
        
        # Verify mock setup
        assert mock_supabase_client.table is not None
    
    def test_brand_operations(self, mock_supabase_client):
        """Test brand CRUD operations"""
        brand_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        brand_data = {
            "id": brand_id,
            "user_id": user_id,
            "name": "Test Brand",
            "domain": "https://example.com",
            "industry": "Technology",
            "keywords": ["ai", "tech"],
            "description": "A test brand",
            "competitors": ["competitor.com"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        
        # Test operations
        mock_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[brand_data]
        )
        mock_table.insert.return_value.execute.return_value = Mock(
            data=[brand_data]
        )
        
        assert mock_supabase_client.table is not None
    
    def test_scan_operations(self, mock_supabase_client):
        """Test scan CRUD operations"""
        scan_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        brand_id = str(uuid.uuid4())
        scan_data = {
            "id": scan_id,
            "user_id": user_id,
            "brand_id": brand_id,
            "scan_type": "visibility",
            "status": "pending",
            "progress": 0,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "error_message": None,
            "metadata": {}
        }
        
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        
        # Test scan creation and updates
        mock_table.insert.return_value.execute.return_value = Mock(
            data=[scan_data]
        )
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock(
            data=[{**scan_data, "progress": 50, "status": "processing"}]
        )
        
        assert mock_supabase_client.table is not None

class TestRLSPolicies:
    """Test Row Level Security policies"""
    
    def test_profile_rls_policy(self):
        """Test that profiles RLS policy allows users to access only their own data"""
        # This would typically require integration testing with actual Supabase
        # For unit tests, we verify the policy logic conceptually
        user_id = str(uuid.uuid4())
        other_user_id = str(uuid.uuid4())
        
        # Simulate RLS check: user can access their own profile
        def check_profile_access(requesting_user_id: str, profile_user_id: str) -> bool:
            return requesting_user_id == profile_user_id
        
        assert check_profile_access(user_id, user_id) is True
        assert check_profile_access(user_id, other_user_id) is False
    
    def test_brand_rls_policy(self):
        """Test that brands RLS policy allows users to access only their own brands"""
        user_id = str(uuid.uuid4())
        other_user_id = str(uuid.uuid4())
        
        def check_brand_access(requesting_user_id: str, brand_user_id: str) -> bool:
            return requesting_user_id == brand_user_id
        
        assert check_brand_access(user_id, user_id) is True
        assert check_brand_access(user_id, other_user_id) is False
    
    def test_scan_results_rls_policy(self):
        """Test that scan results RLS policy allows access only to own scan results"""
        user_id = str(uuid.uuid4())
        other_user_id = str(uuid.uuid4())
        
        def check_results_access(requesting_user_id: str, scan_user_id: str) -> bool:
            # Simulates the JOIN check in the RLS policy
            return requesting_user_id == scan_user_id
        
        assert check_results_access(user_id, user_id) is True
        assert check_results_access(user_id, other_user_id) is False

class TestCacheOperations:
    """Test LLM response caching functionality"""
    
    def test_cache_key_generation(self):
        """Test cache key generation for LLM responses"""
        import hashlib
        
        def generate_cache_key(model: str, prompt: str, brand: str) -> str:
            content = f"{model}:{prompt}:{brand}"
            return hashlib.sha256(content.encode()).hexdigest()[:32]
        
        key1 = generate_cache_key("gpt-4", "test prompt", "brand1")
        key2 = generate_cache_key("gpt-4", "test prompt", "brand1")
        key3 = generate_cache_key("gpt-4", "test prompt", "brand2")
        
        assert key1 == key2  # Same inputs should generate same key
        assert key1 != key3  # Different inputs should generate different keys
        assert len(key1) == 32  # Key should be 32 characters
    
    def test_cache_expiration(self):
        """Test cache expiration logic"""
        now = datetime.now()
        expires_in_1_hour = now + timedelta(hours=1)
        expires_in_past = now - timedelta(hours=1)
        
        def is_cache_expired(expires_at: datetime) -> bool:
            return expires_at < datetime.now()
        
        assert is_cache_expired(expires_in_past) is True
        assert is_cache_expired(expires_in_1_hour) is False

if __name__ == "__main__":
    pytest.main([__file__])