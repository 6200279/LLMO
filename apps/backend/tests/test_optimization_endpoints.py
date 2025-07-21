"""
Tests for Optimization API Endpoints

This module tests the optimization API endpoints including:
- /api/optimize/schema - Schema markup generation endpoint
- /api/optimize/content - Content optimization endpoint  
- /api/optimize/history - Optimization history endpoint
"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

# Import the FastAPI app
from main import app

class TestOptimizationEndpoints:
    """Test cases for optimization API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer mock_token"}
    
    @pytest.fixture
    def sample_schema_request(self):
        """Sample schema optimization request"""
        return {
            "brand_name": "TechCorp",
            "domain": "https://techcorp.com",
            "industry": "technology",
            "description": "Leading software solutions provider",
            "schema_type": "organization",
            "additional_data": {
                "phone": "+1-555-0123",
                "email": "contact@techcorp.com",
                "city": "San Francisco",
                "state": "CA",
                "country": "US"
            }
        }
    
    @pytest.fixture
    def sample_content_request(self):
        """Sample content optimization request"""
        return {
            "brand_name": "TechCorp",
            "domain": "https://techcorp.com",
            "industry": "technology",
            "description": "Leading software solutions provider",
            "content_type": "meta_tags",
            "target_keywords": ["software", "solutions", "technology"],
            "target_audience": "businesses"
        }

class TestSchemaOptimizationEndpoint(TestOptimizationEndpoints):
    """Test /api/optimize/schema endpoint"""
    
    @patch('services.database_service.db_service')
    @patch('middleware.auth_middleware.verify_scan_quota')
    def test_schema_optimization_success(self, mock_verify_quota, mock_db_service, client, sample_schema_request, mock_auth_headers):
        """Test successful schema optimization"""
        # Mock authentication and quota verification
        mock_profile = AsyncMock()
        mock_profile.id = "user123"
        mock_profile.scans_remaining = 5
        mock_verify_quota.return_value = mock_profile
        
        # Mock database operations
        mock_db_service.update_scan_usage = AsyncMock()
        mock_db_service.create_scan = AsyncMock(return_value="scan123")
        
        response = client.post(
            "/api/optimize/schema",
            json=sample_schema_request,
            headers=mock_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["optimization_type"] == "schema_organization"
        assert data["brand_name"] == "TechCorp"
        assert data["domain"] == "https://techcorp.com"
        assert "generated_content" in data
        assert "recommendations" in data
        assert "compliance_score" in data
        assert "scan_id" in data
        assert "scans_remaining" in data
        
        # Check generated content structure
        content = data["generated_content"]
        assert "schema_markup" in content
        assert "html_implementation" in content
        assert "schema_type" in content
        
        # Verify schema markup
        schema = content["schema_markup"]
        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "Organization"
        assert schema["name"] == "TechCorp"
        
        # Verify database calls
        mock_db_service.update_scan_usage.assert_called_once_with("user123")
        mock_db_service.create_scan.assert_called_once()
    
    def test_schema_optimization_invalid_request(self, client, mock_auth_headers):
        """Test schema optimization with invalid request data"""
        invalid_request = {
            "brand_name": "",  # Invalid: empty brand name
            "domain": "invalid-domain",  # Invalid: no protocol
            "schema_type": "invalid_type"  # Invalid: unsupported type
        }
        
        with patch('middleware.auth_middleware.verify_scan_quota') as mock_verify_quota:
            mock_profile = AsyncMock()
            mock_profile.id = "user123"
            mock_verify_quota.return_value = mock_profile
            
            response = client.post(
                "/api/optimize/schema",
                json=invalid_request,
                headers=mock_auth_headers
            )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid request data" in response.json()["detail"]
    
    def test_schema_optimization_unauthorized(self, client, sample_schema_request):
        """Test schema optimization without authentication"""
        response = client.post(
            "/api/optimize/schema",
            json=sample_schema_request
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch('services.database_service.db_service')
    @patch('middleware.auth_middleware.verify_scan_quota')
    def test_schema_optimization_product_type(self, mock_verify_quota, mock_db_service, client, mock_auth_headers):
        """Test schema optimization for product type"""
        # Mock authentication
        mock_profile = AsyncMock()
        mock_profile.id = "user123"
        mock_profile.scans_remaining = 5
        mock_verify_quota.return_value = mock_profile
        
        # Mock database operations
        mock_db_service.update_scan_usage = AsyncMock()
        mock_db_service.create_scan = AsyncMock(return_value="scan123")
        
        product_request = {
            "brand_name": "TechCorp",
            "domain": "https://techcorp.com",
            "industry": "technology",
            "description": "Leading software solutions provider",
            "schema_type": "product",
            "additional_data": {
                "product_name": "TechSuite Pro",
                "product_description": "Professional software suite",
                "price": "99.99",
                "currency": "USD"
            }
        }
        
        response = client.post(
            "/api/optimize/schema",
            json=product_request,
            headers=mock_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["optimization_type"] == "schema_product"
        
        # Check product-specific schema
        schema = data["generated_content"]["schema_markup"]
        assert schema["@type"] == "Product"
        assert schema["name"] == "TechSuite Pro"
        assert "offers" in schema

class TestContentOptimizationEndpoint(TestOptimizationEndpoints):
    """Test /api/optimize/content endpoint"""
    
    @patch('services.database_service.db_service')
    @patch('middleware.auth_middleware.verify_scan_quota')
    def test_content_optimization_meta_tags(self, mock_verify_quota, mock_db_service, client, sample_content_request, mock_auth_headers):
        """Test content optimization for meta tags"""
        # Mock authentication
        mock_profile = AsyncMock()
        mock_profile.id = "user123"
        mock_profile.scans_remaining = 5
        mock_verify_quota.return_value = mock_profile
        
        # Mock database operations
        mock_db_service.update_scan_usage = AsyncMock()
        mock_db_service.create_scan = AsyncMock(return_value="scan123")
        
        response = client.post(
            "/api/optimize/content",
            json=sample_content_request,
            headers=mock_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["optimization_type"] == "meta_tags"
        assert data["brand_name"] == "TechCorp"
        
        # Check generated content
        content = data["generated_content"]
        assert "title_options" in content
        assert "description_options" in content
        assert "open_graph_tags" in content
        assert "twitter_tags" in content
        assert "html_implementation" in content
        
        # Verify title options
        titles = content["title_options"]
        assert len(titles) > 0
        assert all("TechCorp" in title for title in titles)
        
        # Verify Open Graph tags
        og_tags = content["open_graph_tags"]
        assert og_tags["og:title"]
        assert og_tags["og:url"] == "https://techcorp.com"
    
    @patch('services.database_service.db_service')
    @patch('middleware.auth_middleware.verify_scan_quota')
    def test_content_optimization_faq(self, mock_verify_quota, mock_db_service, client, mock_auth_headers):
        """Test content optimization for FAQ"""
        # Mock authentication
        mock_profile = AsyncMock()
        mock_profile.id = "user123"
        mock_profile.scans_remaining = 5
        mock_verify_quota.return_value = mock_profile
        
        # Mock database operations
        mock_db_service.update_scan_usage = AsyncMock()
        mock_db_service.create_scan = AsyncMock(return_value="scan123")
        
        faq_request = {
            "brand_name": "TechCorp",
            "domain": "https://techcorp.com",
            "industry": "technology",
            "description": "Leading software solutions provider",
            "content_type": "faq"
        }
        
        response = client.post(
            "/api/optimize/content",
            json=faq_request,
            headers=mock_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["optimization_type"] == "faq_content"
        
        # Check FAQ content
        content = data["generated_content"]
        assert "faq_items" in content
        assert "schema_markup" in content
        assert "html_implementation" in content
        
        # Verify FAQ items
        faq_items = content["faq_items"]
        assert len(faq_items) > 0
        
        for item in faq_items:
            assert "question" in item
            assert "answer" in item
            assert "TechCorp" in item["question"]
        
        # Verify FAQ schema
        schema = content["schema_markup"]
        assert schema["@type"] == "FAQPage"
        assert "mainEntity" in schema
    
    @patch('services.database_service.db_service')
    @patch('middleware.auth_middleware.verify_scan_quota')
    def test_content_optimization_landing_page(self, mock_verify_quota, mock_db_service, client, mock_auth_headers):
        """Test content optimization for landing page"""
        # Mock authentication
        mock_profile = AsyncMock()
        mock_profile.id = "user123"
        mock_profile.scans_remaining = 5
        mock_verify_quota.return_value = mock_profile
        
        # Mock database operations
        mock_db_service.update_scan_usage = AsyncMock()
        mock_db_service.create_scan = AsyncMock(return_value="scan123")
        
        landing_page_request = {
            "brand_name": "TechCorp",
            "domain": "https://techcorp.com",
            "industry": "technology",
            "description": "Leading software solutions provider",
            "content_type": "landing_page",
            "target_keywords": ["software", "solutions"],
            "target_audience": "businesses"
        }
        
        response = client.post(
            "/api/optimize/content",
            json=landing_page_request,
            headers=mock_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["optimization_type"] == "landing_page"
        
        # Check landing page content
        content = data["generated_content"]
        assert "hero_section" in content
        assert "features_section" in content
        assert "benefits_section" in content
        assert "cta_section" in content
        assert "full_template" in content
        
        # Verify hero section
        hero = content["hero_section"]
        assert "headline" in hero
        assert "TechCorp" in hero["headline"]
        
        # Verify features section
        features = content["features_section"]
        assert len(features) >= 3
        
        for feature in features:
            assert "title" in feature
            assert "description" in feature
    
    def test_content_optimization_invalid_type(self, client, mock_auth_headers):
        """Test content optimization with invalid content type"""
        invalid_request = {
            "brand_name": "TechCorp",
            "domain": "https://techcorp.com",
            "content_type": "invalid_type"
        }
        
        with patch('middleware.auth_middleware.verify_scan_quota') as mock_verify_quota:
            mock_profile = AsyncMock()
            mock_profile.id = "user123"
            mock_verify_quota.return_value = mock_profile
            
            response = client.post(
                "/api/optimize/content",
                json=invalid_request,
                headers=mock_auth_headers
            )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

class TestOptimizationHistoryEndpoint(TestOptimizationEndpoints):
    """Test /api/optimize/history endpoint"""
    
    @patch('services.database_service.db_service')
    @patch('middleware.auth_middleware.get_current_user_id')
    def test_get_optimization_history(self, mock_get_user_id, mock_db_service, client, mock_auth_headers):
        """Test getting optimization history"""
        # Mock authentication
        mock_get_user_id.return_value = "user123"
        
        # Mock database response
        from models.database import Scan, ScanType, ScanStatus
        from datetime import datetime
        
        mock_scans = [
            Scan(
                id="scan1",
                user_id="user123",
                brand_id="brand1",
                scan_type=ScanType.OPTIMIZATION,
                status=ScanStatus.COMPLETED,
                progress=100,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                metadata={
                    "brand_name": "TechCorp",
                    "optimization_type": "schema",
                    "schema_type": "organization",
                    "compliance_score": 85
                },
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            Scan(
                id="scan2",
                user_id="user123",
                brand_id="brand2",
                scan_type=ScanType.OPTIMIZATION,
                status=ScanStatus.COMPLETED,
                progress=100,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                metadata={
                    "brand_name": "HealthCorp",
                    "optimization_type": "content",
                    "content_type": "meta_tags",
                    "compliance_score": 92
                },
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        mock_db_service.get_user_scans = AsyncMock(return_value=mock_scans)
        
        response = client.get(
            "/api/optimize/history",
            headers=mock_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "optimization_history" in data
        assert "total_count" in data
        assert "limit" in data
        
        history = data["optimization_history"]
        assert len(history) == 2
        
        # Check first optimization record
        first_opt = history[0]  # Should be sorted by created_at desc
        assert "scan_id" in first_opt
        assert "brand_name" in first_opt
        assert "optimization_type" in first_opt
        assert "compliance_score" in first_opt
        assert "status" in first_opt
        assert "created_at" in first_opt
        
        # Verify database call
        mock_db_service.get_user_scans.assert_called_once_with("user123", 50)
    
    @patch('services.database_service.db_service')
    @patch('middleware.auth_middleware.get_current_user_id')
    def test_get_optimization_history_filtered(self, mock_get_user_id, mock_db_service, client, mock_auth_headers):
        """Test getting optimization history with type filter"""
        # Mock authentication
        mock_get_user_id.return_value = "user123"
        
        # Mock database response with mixed optimization types
        from models.database import Scan, ScanType, ScanStatus
        from datetime import datetime
        
        mock_scans = [
            Scan(
                id="scan1",
                user_id="user123",
                brand_id="brand1",
                scan_type=ScanType.OPTIMIZATION,
                status=ScanStatus.COMPLETED,
                progress=100,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                metadata={
                    "optimization_type": "schema",
                    "compliance_score": 85
                },
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            Scan(
                id="scan2",
                user_id="user123",
                brand_id="brand2",
                scan_type=ScanType.OPTIMIZATION,
                status=ScanStatus.COMPLETED,
                progress=100,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                metadata={
                    "optimization_type": "content",
                    "compliance_score": 92
                },
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        mock_db_service.get_user_scans = AsyncMock(return_value=mock_scans)
        
        # Filter for schema optimizations only
        response = client.get(
            "/api/optimize/history?optimization_type=schema",
            headers=mock_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        history = data["optimization_history"]
        
        # Should only return schema optimizations
        assert len(history) == 1
        assert history[0]["optimization_type"] == "schema"
        assert data["filtered_type"] == "schema"
    
    @patch('services.database_service.db_service')
    @patch('middleware.auth_middleware.get_current_user_id')
    def test_get_optimization_history_empty(self, mock_get_user_id, mock_db_service, client, mock_auth_headers):
        """Test getting optimization history when no optimizations exist"""
        # Mock authentication
        mock_get_user_id.return_value = "user123"
        
        # Mock empty database response
        mock_db_service.get_user_scans = AsyncMock(return_value=[])
        
        response = client.get(
            "/api/optimize/history",
            headers=mock_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["optimization_history"] == []
        assert data["total_count"] == 0
    
    def test_get_optimization_history_unauthorized(self, client):
        """Test getting optimization history without authentication"""
        response = client.get("/api/optimize/history")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestOptimizationEndpointsIntegration(TestOptimizationEndpoints):
    """Integration tests for optimization endpoints"""
    
    @patch('services.database_service.db_service')
    @patch('middleware.auth_middleware.verify_scan_quota')
    def test_complete_optimization_workflow(self, mock_verify_quota, mock_db_service, client, mock_auth_headers):
        """Test complete optimization workflow from request to history"""
        # Mock authentication
        mock_profile = AsyncMock()
        mock_profile.id = "user123"
        mock_profile.scans_remaining = 5
        mock_verify_quota.return_value = mock_profile
        
        # Mock database operations
        mock_db_service.update_scan_usage = AsyncMock()
        mock_db_service.create_scan = AsyncMock(return_value="scan123")
        
        # Step 1: Create schema optimization
        schema_request = {
            "brand_name": "TestCorp",
            "domain": "https://testcorp.com",
            "industry": "technology",
            "schema_type": "organization"
        }
        
        schema_response = client.post(
            "/api/optimize/schema",
            json=schema_request,
            headers=mock_auth_headers
        )
        
        assert schema_response.status_code == status.HTTP_200_OK
        schema_data = schema_response.json()
        assert schema_data["scan_id"] == "scan123"
        
        # Step 2: Create content optimization
        content_request = {
            "brand_name": "TestCorp",
            "domain": "https://testcorp.com",
            "industry": "technology",
            "content_type": "meta_tags"
        }
        
        mock_db_service.create_scan = AsyncMock(return_value="scan124")
        
        content_response = client.post(
            "/api/optimize/content",
            json=content_request,
            headers=mock_auth_headers
        )
        
        assert content_response.status_code == status.HTTP_200_OK
        content_data = content_response.json()
        assert content_data["scan_id"] == "scan124"
        
        # Verify database interactions
        assert mock_db_service.update_scan_usage.call_count == 2
        assert mock_db_service.create_scan.call_count == 2
    
    @patch('services.database_service.db_service')
    @patch('middleware.auth_middleware.verify_scan_quota')
    def test_optimization_quota_enforcement(self, mock_verify_quota, mock_db_service, client, mock_auth_headers):
        """Test that optimization endpoints enforce scan quotas"""
        # Mock authentication with no remaining scans
        mock_profile = AsyncMock()
        mock_profile.id = "user123"
        mock_profile.scans_remaining = 0
        mock_verify_quota.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Scan quota exceeded"
        )
        
        schema_request = {
            "brand_name": "TestCorp",
            "domain": "https://testcorp.com",
            "schema_type": "organization"
        }
        
        response = client.post(
            "/api/optimize/schema",
            json=schema_request,
            headers=mock_auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "quota" in response.json()["detail"].lower()

if __name__ == "__main__":
    pytest.main([__file__])