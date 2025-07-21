"""
Integration tests for the Website Audit API
Enhanced with comprehensive error handling, caching, and history tracking tests
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime, timedelta

from main import app
from services.web_scraper import WebScraperService
from models.database import ScanStatus, ScanType

# Create test client
client = TestClient(app)

# Sample audit result for mocking
SAMPLE_AUDIT_RESULT = {
    "domain": "https://example.com",
    "status_code": 200,
    "schema_org": {
        "found": True,
        "count": 2,
        "types": ["Organization", "Product"],
        "high_value_schemas": {
            "organization": True,
            "product": True,
            "faq": False,
            "breadcrumb": False,
            "article": False
        },
        "property_count": 15
    },
    "meta_tags": {
        "title": "Example Website",
        "title_length": 15,
        "description": "This is an example website description",
        "description_length": 35,
        "completeness": {
            "basic": 0.8,
            "social": 0.6,
            "overall": 0.7
        }
    },
    "content_structure": {
        "headings": {"h1": 1, "h2": 3, "h3": 2},
        "heading_hierarchy_score": 0.9,
        "word_count": 1200,
        "faq_count": 1
    },
    "technical_factors": {
        "ssl_enabled": True,
        "mobile_friendly": True
    },
    "component_scores": {
        "schema_score": 75,
        "meta_score": 65,
        "content_score": 80,
        "technical_score": 90
    },
    "llm_friendly_score": 78,
    "recommendations": [
        {
            "priority": "medium",
            "category": "schema",
            "issue": "Missing FAQ schema",
            "recommendation": "Add FAQPage schema for better visibility",
            "implementation": "Implement JSON-LD with FAQPage schema for your FAQ section"
        },
        {
            "priority": "medium",
            "category": "meta",
            "issue": "Short title",
            "recommendation": "Expand title to 50-60 characters",
            "implementation": "Create a more descriptive title that includes key information"
        }
    ],
    "timestamp": datetime.now().isoformat()
}

# Mock authentication token
MOCK_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItaWQiLCJleHAiOjE3MTY5MzkyMDB9.this_is_a_mock_token_for_testing"

# Mock user profile
MOCK_PROFILE = {
    "id": "test-user-id",
    "first_name": "Test",
    "last_name": "User",
    "company_name": "Test Company",
    "subscription_tier": "pro",
    "scans_remaining": 10,
    "scans_used": 5,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
}

@pytest.fixture
def mock_auth():
    """Mock authentication middleware"""
    with patch("middleware.auth_middleware.get_current_user_profile") as mock_auth:
        mock_auth.return_value = MOCK_PROFILE
        yield mock_auth

@pytest.fixture
def mock_verify_quota():
    """Mock scan quota verification"""
    with patch("middleware.auth_middleware.verify_scan_quota") as mock_quota:
        mock_quota.return_value = MOCK_PROFILE
        yield mock_quota

@pytest.fixture
def mock_db_service():
    """Mock database service"""
    with patch("services.database_service.db_service") as mock_db:
        # Mock scan object
        mock_scan = MagicMock()
        mock_scan.id = "test-scan-id"
        mock_scan.scan_type = ScanType.AUDIT
        mock_scan.status = ScanStatus.COMPLETED
        mock_scan.started_at = datetime.now()
        mock_scan.completed_at = datetime.now()
        mock_scan.metadata = {"domain": "https://example.com"}
        mock_scan.error_message = None
        
        # Mock create_scan
        mock_db.create_scan = AsyncMock(return_value=mock_scan)
        
        # Mock update_scan_usage
        mock_db.update_scan_usage = AsyncMock(return_value=None)
        
        # Mock update_scan
        mock_db.update_scan = AsyncMock(return_value=None)
        
        # Mock create_audit_result
        mock_db.create_audit_result = AsyncMock(return_value="test-audit-result-id")
        
        # Mock get_user_scans
        mock_db.get_user_scans = AsyncMock(return_value=[mock_scan])
        
        # Mock get_scan
        mock_db.get_scan = AsyncMock(return_value=mock_scan)
        
        # Mock audit result
        mock_audit_result = MagicMock()
        mock_audit_result.overall_score = 78
        mock_audit_result.schema_score = 75
        mock_audit_result.meta_score = 65
        mock_audit_result.content_score = 80
        mock_audit_result.technical_score = 90
        mock_audit_result.recommendations = SAMPLE_AUDIT_RESULT["recommendations"]
        
        # Mock get_audit_result
        mock_db.get_audit_result = AsyncMock(return_value=mock_audit_result)
        
        yield mock_db

@pytest.fixture
def mock_web_scraper():
    """Mock web scraper service"""
    with patch.object(WebScraperService, "audit_website") as mock_audit:
        mock_audit.return_value = SAMPLE_AUDIT_RESULT
        yield mock_audit

@pytest.fixture
def mock_cache_service():
    """Mock cache service"""
    with patch("services.cache_service.CacheService") as MockCache:
        mock_cache = MagicMock()
        
        # Mock get method to return None (cache miss)
        mock_cache.get = AsyncMock(return_value=None)
        
        # Mock set method
        mock_cache.set = AsyncMock(return_value=True)
        
        MockCache.return_value = mock_cache
        yield mock_cache

class TestWebsiteAuditAPI:
    """Test cases for Website Audit API"""
    
    @pytest.mark.asyncio
    async def test_audit_visibility_success(self, mock_auth, mock_verify_quota, mock_db_service, 
                                     mock_web_scraper, mock_cache_service):
        """Test successful website audit"""
        # Setup request
        request_data = {
            "domain": "https://example.com"
        }
        
        # Make request
        response = client.post(
            "/api/audit/visibility",
            json=request_data,
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check basic structure
        assert data["scan_id"] == "test-scan-id"
        assert data["domain"] == "https://example.com"
        assert data["overall_score"] == 78
        assert data["status"] == "completed"
        assert data["scans_remaining"] == 9  # 10 - 1
        assert data["cached"] is False
        
        # Check component scores
        assert "component_scores" in data
        assert data["component_scores"]["schema_score"] == 75
        assert data["component_scores"]["meta_score"] == 65
        assert data["component_scores"]["content_score"] == 80
        assert data["component_scores"]["technical_score"] == 90
        
        # Check recommendations
        assert "recommendations" in data
        assert len(data["recommendations"]) == 2
        assert data["recommendations"][0]["priority"] == "medium"
        assert data["recommendations"][0]["category"] == "schema"
        
        # Check audit data
        assert "audit_data" in data
        assert "schema_org" in data["audit_data"]
        assert "meta_tags" in data["audit_data"]
        assert "content_structure" in data["audit_data"]
        assert "technical_factors" in data["audit_data"]
        
        # Check timestamp
        assert "timestamp" in data
        
        # Verify service calls
        mock_web_scraper.assert_called_once_with("https://example.com")
        mock_db_service.create_scan.assert_called_once()
        mock_db_service.update_scan_usage.assert_called_once()
        mock_db_service.update_scan.assert_called_once()
        mock_db_service.create_audit_result.assert_called_once()
        mock_cache_service.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_audit_visibility_cache_hit(self, mock_auth, mock_verify_quota, mock_db_service, 
                                       mock_web_scraper, mock_cache_service):
        """Test website audit with cache hit"""
        # Setup cache hit
        cached_result = {
            "scan_id": "cached-scan-id",
            "domain": "https://example.com",
            "overall_score": 78,
            "component_scores": SAMPLE_AUDIT_RESULT["component_scores"],
            "recommendations": SAMPLE_AUDIT_RESULT["recommendations"],
            "audit_data": {
                "schema_org": SAMPLE_AUDIT_RESULT["schema_org"],
                "meta_tags": SAMPLE_AUDIT_RESULT["meta_tags"],
                "content_structure": SAMPLE_AUDIT_RESULT["content_structure"],
                "technical_factors": SAMPLE_AUDIT_RESULT["technical_factors"]
            },
            "status": "completed",
            "scans_remaining": 10,
            "timestamp": SAMPLE_AUDIT_RESULT["timestamp"]
        }
        mock_cache_service.get = AsyncMock(return_value=cached_result)
        
        # Setup request
        request_data = {
            "domain": "https://example.com"
        }
        
        # Make request
        response = client.post(
            "/api/audit/visibility",
            json=request_data,
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check cache indicators
        assert data["cached"] is True
        assert data["scan_id"] == "cached-scan-id"
        assert "cache_timestamp" in data
        
        # Verify service calls
        mock_web_scraper.assert_not_called()  # Should not call web scraper
        mock_db_service.create_scan.assert_not_called()  # Should not create scan
        mock_db_service.update_scan_usage.assert_called_once()  # Should still update usage
        mock_db_service.update_scan.assert_not_called()  # Should not update scan
        mock_db_service.create_audit_result.assert_not_called()  # Should not create result
    
    @pytest.mark.asyncio
    async def test_audit_visibility_invalid_domain(self, mock_auth, mock_verify_quota):
        """Test website audit with invalid domain"""
        # Setup request with invalid domain
        request_data = {
            "domain": "invalid-domain"
        }
        
        # Make request
        response = client.post(
            "/api/audit/visibility",
            json=request_data,
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_audit_visibility_error_handling(self, mock_auth, mock_verify_quota, 
                                           mock_db_service, mock_web_scraper):
        """Test website audit error handling"""
        # Setup web scraper to raise exception
        mock_web_scraper.side_effect = Exception("Test error")
        
        # Setup request
        request_data = {
            "domain": "https://example.com"
        }
        
        # Make request
        response = client.post(
            "/api/audit/visibility",
            json=request_data,
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Test error" in data["detail"]
        
        # Verify service calls
        mock_web_scraper.assert_called_once()
        mock_db_service.create_scan.assert_called_once()
        mock_db_service.update_scan_usage.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_audit_visibility_unauthorized(self):
        """Test website audit without authentication"""
        # Setup request without auth token
        request_data = {
            "domain": "https://example.com"
        }
        
        # Make request
        response = client.post(
            "/api/audit/visibility",
            json=request_data
        )
        
        # Verify response
        assert response.status_code == 401  # Unauthorized
    
    @pytest.mark.asyncio
    async def test_audit_visibility_domain_normalization(self, mock_auth, mock_verify_quota, 
                                                mock_db_service, mock_web_scraper, mock_cache_service):
        """Test domain normalization in audit requests"""
        # Setup request with domain without protocol
        request_data = {
            "domain": "example.com"
        }
        
        # Make request
        response = client.post(
            "/api/audit/visibility",
            json=request_data,
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check that domain was normalized to https
        assert data["domain"] == "https://example.com"
        
        # Verify web scraper was called with normalized domain
        mock_web_scraper.assert_called_once_with("https://example.com")
    
    @pytest.mark.asyncio
    async def test_audit_visibility_connection_error(self, mock_auth, mock_verify_quota, 
                                            mock_db_service, mock_web_scraper, mock_cache_service):
        """Test audit with connection error handling"""
        # Setup web scraper to raise connection error
        mock_web_scraper.side_effect = Exception("Connection error: Unable to connect")
        
        # Setup request
        request_data = {
            "domain": "https://unreachable.com"
        }
        
        # Make request
        response = client.post(
            "/api/audit/visibility",
            json=request_data,
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200  # Should return 200 with error details
        data = response.json()
        
        # Check error handling
        assert data["status"] == "failed"
        assert data["overall_score"] == 0
        assert "error" in data
        assert data["error_type"] == "connection_error"
        assert "Unable to connect" in data["error"]
        
        # Check recommendations include error guidance
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["priority"] == "high"
        assert data["recommendations"][0]["category"] == "technical"
        
        # Verify scan was updated with error
        mock_db_service.update_scan.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_audit_visibility_timeout_error(self, mock_auth, mock_verify_quota, 
                                          mock_db_service, mock_web_scraper, mock_cache_service):
        """Test audit with timeout error handling"""
        # Setup web scraper to raise timeout error
        mock_web_scraper.side_effect = Exception("Timeout error: Request timed out")
        
        # Setup request
        request_data = {
            "domain": "https://slow-website.com"
        }
        
        # Make request
        response = client.post(
            "/api/audit/visibility",
            json=request_data,
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check timeout-specific error handling
        assert data["status"] == "failed"
        assert data["error_type"] == "timeout_error"
        assert "timed out" in data["error"]
        assert "slow or temporarily unavailable" in data["error"]
    
    @pytest.mark.asyncio
    async def test_audit_visibility_http_error(self, mock_auth, mock_verify_quota, 
                                      mock_db_service, mock_web_scraper, mock_cache_service):
        """Test audit with HTTP error handling"""
        # Setup web scraper to raise HTTP error
        mock_web_scraper.side_effect = Exception("HTTP 404 error: Page not found")
        
        # Setup request
        request_data = {
            "domain": "https://example.com/nonexistent"
        }
        
        # Make request
        response = client.post(
            "/api/audit/visibility",
            json=request_data,
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check HTTP-specific error handling
        assert data["status"] == "failed"
        assert data["error_type"] == "http_error"
        assert "returned an error" in data["error"]
        assert "correct URL" in data["error"]
    
    @pytest.mark.asyncio
    async def test_audit_visibility_ssl_error(self, mock_auth, mock_verify_quota, 
                                     mock_db_service, mock_web_scraper, mock_cache_service):
        """Test audit with SSL certificate error handling"""
        # Setup web scraper to raise SSL error
        mock_web_scraper.side_effect = Exception("SSL certificate verification failed")
        
        # Setup request
        request_data = {
            "domain": "https://invalid-ssl.com"
        }
        
        # Make request
        response = client.post(
            "/api/audit/visibility",
            json=request_data,
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check SSL-specific error handling
        assert data["status"] == "failed"
        assert data["error_type"] == "ssl_error"
        assert "certificate issue" in data["error"]
        assert "security configuration" in data["error"]
    
    @pytest.mark.asyncio
    async def test_audit_visibility_cache_ttl(self, mock_auth, mock_verify_quota, 
                                     mock_db_service, mock_web_scraper, mock_cache_service):
        """Test that audit results are cached with 6-hour TTL"""
        # Setup request
        request_data = {
            "domain": "https://example.com"
        }
        
        # Make request
        response = client.post(
            "/api/audit/visibility",
            json=request_data,
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Verify cache was set with 6-hour TTL
        mock_cache_service.set.assert_called_once()
        call_args = mock_cache_service.set.call_args
        assert call_args[0][4] == 6  # TTL should be 6 hours

class TestAuditHistoryAPI:
    """Test cases for Audit History API endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_audit_history_success(self, mock_auth, mock_db_service):
        """Test successful audit history retrieval"""
        # Make request
        response = client.get(
            "/api/audit/history",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "audit_history" in data
        assert "total_count" in data
        assert "limit" in data
        assert data["limit"] == 50  # Default limit
        
        # Verify database calls
        mock_db_service.get_user_scans.assert_called_once_with("test-user-id", 50)
        mock_db_service.get_audit_result.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_audit_history_with_domain_filter(self, mock_auth, mock_db_service):
        """Test audit history with domain filtering"""
        # Make request with domain filter
        response = client.get(
            "/api/audit/history?domain=example.com&limit=20",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check filtering
        assert data["filtered_domain"] == "https://example.com"  # Should be normalized
        assert data["limit"] == 20
    
    @pytest.mark.asyncio
    async def test_get_audit_history_unauthorized(self):
        """Test audit history without authentication"""
        # Make request without auth token
        response = client.get("/api/audit/history")
        
        # Verify response
        assert response.status_code == 401  # Unauthorized
    
    @pytest.mark.asyncio
    async def test_get_audit_history_empty(self, mock_auth, mock_db_service):
        """Test audit history with no results"""
        # Mock empty scan list
        mock_db_service.get_user_scans = AsyncMock(return_value=[])
        
        # Make request
        response = client.get(
            "/api/audit/history",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check empty results
        assert data["audit_history"] == []
        assert data["total_count"] == 0
    
    @pytest.mark.asyncio
    async def test_compare_audits_success(self, mock_auth, mock_db_service):
        """Test successful audit comparison"""
        # Setup second scan for comparison
        mock_scan_2 = MagicMock()
        mock_scan_2.id = "test-scan-id-2"
        mock_scan_2.scan_type = ScanType.AUDIT
        mock_scan_2.started_at = datetime.now() + timedelta(days=7)
        mock_scan_2.metadata = {"domain": "https://example.com"}
        
        # Setup second audit result
        mock_audit_result_2 = MagicMock()
        mock_audit_result_2.overall_score = 85  # Improved score
        mock_audit_result_2.schema_score = 80
        mock_audit_result_2.meta_score = 70
        mock_audit_result_2.content_score = 85
        mock_audit_result_2.technical_score = 95
        mock_audit_result_2.recommendations = []  # Fewer recommendations
        
        # Mock database calls for comparison
        mock_db_service.get_scan = AsyncMock(side_effect=[
            mock_db_service.get_scan.return_value,  # First scan
            mock_scan_2  # Second scan
        ])
        mock_db_service.get_audit_result = AsyncMock(side_effect=[
            mock_db_service.get_audit_result.return_value,  # First result
            mock_audit_result_2  # Second result
        ])
        
        # Make request
        response = client.get(
            "/api/audit/compare/test-scan-id/test-scan-id-2",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check comparison structure
        assert "comparison" in data
        comparison = data["comparison"]
        
        assert "scan_1" in comparison
        assert "scan_2" in comparison
        assert "score_changes" in comparison
        assert "recommendation_analysis" in comparison
        assert "summary" in comparison
        
        # Check score changes
        score_changes = comparison["score_changes"]
        assert score_changes["overall_score"]["change"] == 7  # 85 - 78
        assert score_changes["overall_score"]["change_percentage"] > 0
        
        # Check summary
        summary = comparison["summary"]
        assert summary["overall_improvement"] is True
    
    @pytest.mark.asyncio
    async def test_compare_audits_not_found(self, mock_auth, mock_db_service):
        """Test audit comparison with non-existent scan"""
        # Mock database to return None for second scan
        mock_db_service.get_scan = AsyncMock(side_effect=[
            mock_db_service.get_scan.return_value,  # First scan exists
            None  # Second scan doesn't exist
        ])
        
        # Make request
        response = client.get(
            "/api/audit/compare/test-scan-id/nonexistent-scan-id",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_compare_audits_unauthorized(self):
        """Test audit comparison without authentication"""
        # Make request without auth token
        response = client.get("/api/audit/compare/scan-1/scan-2")
        
        # Verify response
        assert response.status_code == 401  # Unauthorized
    
    @pytest.mark.asyncio
    async def test_compare_audits_invalid_scan_type(self, mock_auth, mock_db_service):
        """Test audit comparison with non-audit scan"""
        # Mock second scan as non-audit type
        mock_scan_2 = MagicMock()
        mock_scan_2.id = "test-scan-id-2"
        mock_scan_2.scan_type = ScanType.VISIBILITY  # Not an audit scan
        
        # Mock database calls
        mock_db_service.get_scan = AsyncMock(side_effect=[
            mock_db_service.get_scan.return_value,  # First scan is audit
            mock_scan_2  # Second scan is not audit
        ])
        
        # Make request
        response = client.get(
            "/api/audit/compare/test-scan-id/test-scan-id-2",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "must be website audits" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_get_domain_audit_history_success(self, mock_auth, mock_db_service):
        """Test domain-specific audit history"""
        # Make request
        response = client.get(
            "/api/audit/domain-history/example.com",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert data["domain"] == "https://example.com"  # Should be normalized
        assert "audit_history" in data
        assert "trend_analysis" in data
        assert "recommendations" in data
        
        # Check trend analysis
        trend_analysis = data["trend_analysis"]
        assert "total_audits" in trend_analysis
        assert "score_trend" in trend_analysis
    
    @pytest.mark.asyncio
    async def test_get_domain_audit_history_no_data(self, mock_auth, mock_db_service):
        """Test domain audit history with no data"""
        # Mock empty scan list
        mock_db_service.get_user_scans = AsyncMock(return_value=[])
        
        # Make request
        response = client.get(
            "/api/audit/domain-history/newdomain.com",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check no data response
        assert data["audit_history"] == []
        assert data["trend_analysis"]["total_audits"] == 0
        assert data["trend_analysis"]["score_trend"] == "no_data"
    
    @pytest.mark.asyncio
    async def test_get_domain_audit_history_unauthorized(self):
        """Test domain audit history without authentication"""
        # Make request without auth token
        response = client.get("/api/audit/domain-history/example.com")
        
        # Verify response
        assert response.status_code == 401  # Unauthorized
    
    @pytest.mark.asyncio
    async def test_get_domain_audit_history_with_trend(self, mock_auth, mock_db_service):
        """Test domain audit history with trend analysis"""
        # Setup multiple scans with different dates and scores
        mock_scan_1 = MagicMock()
        mock_scan_1.id = "test-scan-id-1"
        mock_scan_1.scan_type = ScanType.AUDIT
        mock_scan_1.started_at = datetime.now() - timedelta(days=14)
        mock_scan_1.metadata = {"domain": "https://example.com"}
        
        mock_scan_2 = MagicMock()
        mock_scan_2.id = "test-scan-id-2"
        mock_scan_2.scan_type = ScanType.AUDIT
        mock_scan_2.started_at = datetime.now() - timedelta(days=7)
        mock_scan_2.metadata = {"domain": "https://example.com"}
        
        mock_scan_3 = MagicMock()
        mock_scan_3.id = "test-scan-id-3"
        mock_scan_3.scan_type = ScanType.AUDIT
        mock_scan_3.started_at = datetime.now()
        mock_scan_3.metadata = {"domain": "https://example.com"}
        
        # Setup audit results with improving scores
        mock_audit_result_1 = MagicMock()
        mock_audit_result_1.overall_score = 65
        mock_audit_result_1.recommendations = []
        
        mock_audit_result_2 = MagicMock()
        mock_audit_result_2.overall_score = 72
        mock_audit_result_2.recommendations = []
        
        mock_audit_result_3 = MagicMock()
        mock_audit_result_3.overall_score = 78
        mock_audit_result_3.recommendations = SAMPLE_AUDIT_RESULT["recommendations"]
        
        # Mock database calls
        mock_db_service.get_user_scans = AsyncMock(return_value=[
            mock_scan_3, mock_scan_2, mock_scan_1  # Newest first
        ])
        
        mock_db_service.get_audit_result = AsyncMock(side_effect=[
            mock_audit_result_3,  # Latest result
            mock_audit_result_2,
            mock_audit_result_1
        ])
        
        # Make request
        response = client.get(
            "/api/audit/domain-history/example.com",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check trend analysis
        trend_analysis = data["trend_analysis"]
        assert trend_analysis["score_trend"] == "improving"
        assert trend_analysis["total_audits"] == 3
        assert trend_analysis["average_score"] == 71.67  # (65 + 72 + 78) / 3
        assert trend_analysis["best_score"] == 78
        assert trend_analysis["worst_score"] == 65
        assert trend_analysis["latest_score"] == 78
        assert trend_analysis["first_score"] == 65
        assert trend_analysis["score_change"] == 13  # 78 - 65
        assert trend_analysis["score_change_percentage"] == 20.0  # (78 - 65) / 65 * 100

class TestAuditHistoryAPI:
    """Test cases for Audit History API endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_audit_history_success(self, mock_auth, mock_db_service):
        """Test successful audit history retrieval"""
        # Make request
        response = client.get(
            "/api/audit/history",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "audit_history" in data
        assert "total_count" in data
        assert "limit" in data
        assert data["limit"] == 50  # Default limit
        
        # Verify database calls
        mock_db_service.get_user_scans.assert_called_once_with("test-user-id", 50)
        mock_db_service.get_audit_result.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_audit_history_with_domain_filter(self, mock_auth, mock_db_service):
        """Test audit history with domain filtering"""
        # Make request with domain filter
        response = client.get(
            "/api/audit/history?domain=example.com&limit=20",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check filtering
        assert data["filtered_domain"] == "https://example.com"  # Should be normalized
        assert data["limit"] == 20
    
    @pytest.mark.asyncio
    async def test_compare_audits_success(self, mock_auth, mock_db_service):
        """Test successful audit comparison"""
        # Setup second scan for comparison
        mock_scan_2 = MagicMock()
        mock_scan_2.id = "test-scan-id-2"
        mock_scan_2.scan_type = ScanType.AUDIT
        mock_scan_2.started_at = datetime.now() + timedelta(days=7)
        mock_scan_2.metadata = {"domain": "https://example.com"}
        
        # Setup second audit result
        mock_audit_result_2 = MagicMock()
        mock_audit_result_2.overall_score = 85  # Improved score
        mock_audit_result_2.schema_score = 80
        mock_audit_result_2.meta_score = 70
        mock_audit_result_2.content_score = 85
        mock_audit_result_2.technical_score = 95
        mock_audit_result_2.recommendations = []  # Fewer recommendations
        
        # Mock database calls for comparison
        mock_db_service.get_scan.side_effect = [
            mock_db_service.get_scan.return_value,  # First scan
            mock_scan_2  # Second scan
        ]
        mock_db_service.get_audit_result.side_effect = [
            mock_db_service.get_audit_result.return_value,  # First result
            mock_audit_result_2  # Second result
        ]
        
        # Make request
        response = client.get(
            "/api/audit/compare/test-scan-id/test-scan-id-2",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check comparison structure
        assert "comparison" in data
        comparison = data["comparison"]
        
        assert "scan_1" in comparison
        assert "scan_2" in comparison
        assert "score_changes" in comparison
        assert "recommendation_analysis" in comparison
        assert "summary" in comparison
        
        # Check score changes
        score_changes = comparison["score_changes"]
        assert score_changes["overall_score"]["change"] == 7  # 85 - 78
        assert score_changes["overall_score"]["change_percentage"] > 0
        
        # Check summary
        summary = comparison["summary"]
        assert summary["overall_improvement"] is True
    
    @pytest.mark.asyncio
    async def test_compare_audits_not_found(self, mock_auth, mock_db_service):
        """Test audit comparison with non-existent scan"""
        # Mock database to return None for second scan
        mock_db_service.get_scan.side_effect = [
            mock_db_service.get_scan.return_value,  # First scan exists
            None  # Second scan doesn't exist
        ]
        
        # Make request
        response = client.get(
            "/api/audit/compare/test-scan-id/nonexistent-scan-id",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_get_domain_audit_history_success(self, mock_auth, mock_db_service):
        """Test domain-specific audit history"""
        # Make request
        response = client.get(
            "/api/audit/domain-history/example.com",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert data["domain"] == "https://example.com"  # Should be normalized
        assert "audit_history" in data
        assert "trend_analysis" in data
        assert "recommendations" in data
        
        # Check trend analysis
        trend_analysis = data["trend_analysis"]
        assert "total_audits" in trend_analysis
        assert "score_trend" in trend_analysis
        assert "average_score" in trend_analysis
        assert "best_score" in trend_analysis
        assert "latest_score" in trend_analysis
    
    @pytest.mark.asyncio
    async def test_get_domain_audit_history_no_data(self, mock_auth, mock_db_service):
        """Test domain audit history with no data"""
        # Mock empty scan list
        mock_db_service.get_user_scans = AsyncMock(return_value=[])
        
        # Make request
        response = client.get(
            "/api/audit/domain-history/newdomain.com",
            headers={"Authorization": f"Bearer {MOCK_TOKEN}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check no data response
        assert data["audit_history"] == []
        assert data["trend_analysis"]["total_audits"] == 0
        assert data["trend_analysis"]["score_trend"] == "no_data"