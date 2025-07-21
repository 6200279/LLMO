"""
Tests for Optimization Service

This module tests the optimization service functionality including:
- Schema markup generation (Organization, Product, FAQ, Service)
- Meta tag optimization with industry-specific recommendations
- FAQ content generation based on LLM query patterns
- Landing page content templates
- Schema.org compliance validation
"""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

from services.optimization_service import (
    OptimizationService,
    SchemaOptimizationRequest,
    ContentOptimizationRequest,
    OptimizationResult,
    SCHEMA_TEMPLATES,
    INDUSTRY_FAQ_PATTERNS,
    META_TAG_TEMPLATES
)

class TestOptimizationService:
    """Test cases for OptimizationService"""
    
    @pytest.fixture
    def optimization_service(self):
        """Create optimization service instance for testing"""
        return OptimizationService()
    
    @pytest.fixture
    def sample_schema_request(self):
        """Sample schema optimization request"""
        return SchemaOptimizationRequest(
            brand_name="TechCorp",
            domain="https://techcorp.com",
            industry="technology",
            description="Leading software solutions provider",
            schema_type="organization",
            additional_data={
                "founding_date": "2020-01-01",
                "phone": "+1-555-0123",
                "email": "contact@techcorp.com",
                "city": "San Francisco",
                "state": "CA",
                "country": "US"
            }
        )
    
    @pytest.fixture
    def sample_content_request(self):
        """Sample content optimization request"""
        return ContentOptimizationRequest(
            brand_name="TechCorp",
            domain="https://techcorp.com",
            industry="technology",
            description="Leading software solutions provider",
            content_type="meta_tags",
            target_keywords=["software", "solutions", "technology"],
            target_audience="businesses"
        )

class TestSchemaGeneration(TestOptimizationService):
    """Test schema markup generation functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_organization_schema(self, optimization_service, sample_schema_request):
        """Test organization schema generation"""
        result = await optimization_service.generate_schema_markup(sample_schema_request)
        
        assert isinstance(result, OptimizationResult)
        assert result.optimization_type == "schema_organization"
        assert result.brand_name == "TechCorp"
        assert result.domain == "https://techcorp.com"
        assert result.compliance_score > 0
        
        # Check generated schema
        schema = result.generated_content["schema_markup"]
        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "Organization"
        assert schema["name"] == "TechCorp"
        assert schema["url"] == "https://techcorp.com"
        assert schema["description"] == "Leading software solutions provider"
        
        # Check contact information
        assert "contactPoint" in schema
        assert schema["contactPoint"]["telephone"] == "+1-555-0123"
        assert schema["contactPoint"]["email"] == "contact@techcorp.com"
        
        # Check address
        assert "address" in schema
        assert schema["address"]["addressLocality"] == "San Francisco"
        assert schema["address"]["addressRegion"] == "CA"
        assert schema["address"]["addressCountry"] == "US"
        
        # Check HTML implementation
        html_impl = result.generated_content["html_implementation"]
        assert '<script type="application/ld+json">' in html_impl
        assert '"@type": "Organization"' in html_impl
        
        # Check recommendations
        assert len(result.recommendations) > 0
        assert any(rec["category"] == "implementation" for rec in result.recommendations)
    
    @pytest.mark.asyncio
    async def test_generate_product_schema(self, optimization_service):
        """Test product schema generation"""
        request = SchemaOptimizationRequest(
            brand_name="TechCorp",
            domain="https://techcorp.com",
            industry="technology",
            description="Leading software solutions provider",
            schema_type="product",
            additional_data={
                "product_name": "TechSuite Pro",
                "product_description": "Professional software suite for businesses",
                "price": "99.99",
                "currency": "USD",
                "rating_value": "4.5",
                "review_count": "150"
            }
        )
        
        result = await optimization_service.generate_schema_markup(request)
        
        assert result.optimization_type == "schema_product"
        
        # Check generated schema
        schema = result.generated_content["schema_markup"]
        assert schema["@type"] == "Product"
        assert schema["name"] == "TechSuite Pro"
        assert schema["description"] == "Professional software suite for businesses"
        assert schema["brand"]["name"] == "TechCorp"
        
        # Check offers
        assert "offers" in schema
        assert schema["offers"]["price"] == "99.99"
        assert schema["offers"]["priceCurrency"] == "USD"
        
        # Check ratings
        assert "aggregateRating" in schema
        assert schema["aggregateRating"]["ratingValue"] == "4.5"
        assert schema["aggregateRating"]["reviewCount"] == "150"
    
    @pytest.mark.asyncio
    async def test_generate_service_schema(self, optimization_service):
        """Test service schema generation"""
        request = SchemaOptimizationRequest(
            brand_name="TechCorp",
            domain="https://techcorp.com",
            industry="technology",
            description="Leading software solutions provider",
            schema_type="service",
            additional_data={
                "service_name": "Software Consulting",
                "service_description": "Expert software consulting services",
                "service_area": "United States",
                "price": "150",
                "currency": "USD"
            }
        )
        
        result = await optimization_service.generate_schema_markup(request)
        
        assert result.optimization_type == "schema_service"
        
        # Check generated schema
        schema = result.generated_content["schema_markup"]
        assert schema["@type"] == "Service"
        assert schema["name"] == "Software Consulting"
        assert schema["description"] == "Expert software consulting services"
        assert schema["areaServed"] == "United States"
        assert schema["serviceType"] == "technology"
    
    @pytest.mark.asyncio
    async def test_invalid_schema_type(self, optimization_service):
        """Test handling of invalid schema type"""
        request = SchemaOptimizationRequest(
            brand_name="TechCorp",
            domain="https://techcorp.com",
            schema_type="invalid_type"
        )
        
        with pytest.raises(ValueError, match="Unsupported schema type"):
            await optimization_service.generate_schema_markup(request)
    
    @pytest.mark.asyncio
    async def test_schema_compliance_validation(self, optimization_service):
        """Test schema compliance scoring"""
        # Test with complete data
        complete_schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "TechCorp",
            "description": "Leading software solutions",
            "url": "https://techcorp.com",
            "address": {"@type": "PostalAddress"},
            "contactPoint": {"@type": "ContactPoint"}
        }
        
        score = await optimization_service._validate_schema_compliance(complete_schema)
        assert score >= 80  # Should have high compliance
        
        # Test with minimal data
        minimal_schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "TechCorp"
        }
        
        score = await optimization_service._validate_schema_compliance(minimal_schema)
        assert score < 80  # Should have lower compliance

class TestMetaTagOptimization(TestOptimizationService):
    """Test meta tag optimization functionality"""
    
    @pytest.mark.asyncio
    async def test_optimize_meta_tags_technology(self, optimization_service, sample_content_request):
        """Test meta tag optimization for technology industry"""
        result = await optimization_service.optimize_meta_tags(sample_content_request)
        
        assert isinstance(result, OptimizationResult)
        assert result.optimization_type == "meta_tags"
        assert result.brand_name == "TechCorp"
        
        # Check generated content
        content = result.generated_content
        assert "title_options" in content
        assert "description_options" in content
        assert "open_graph_tags" in content
        assert "twitter_tags" in content
        assert "html_implementation" in content
        
        # Check title options
        titles = content["title_options"]
        assert len(titles) > 0
        assert all("TechCorp" in title for title in titles)
        assert all(len(title) <= 60 for title in titles)  # SEO best practice
        
        # Check description options
        descriptions = content["description_options"]
        assert len(descriptions) > 0
        assert all("TechCorp" in desc for desc in descriptions)
        assert all(len(desc) <= 160 for desc in descriptions)  # SEO best practice
        
        # Check Open Graph tags
        og_tags = content["open_graph_tags"]
        assert og_tags["og:title"]
        assert og_tags["og:description"]
        assert og_tags["og:url"] == "https://techcorp.com"
        assert og_tags["og:type"] == "website"
        assert og_tags["og:site_name"] == "TechCorp"
        
        # Check Twitter Card tags
        twitter_tags = content["twitter_tags"]
        assert twitter_tags["twitter:card"] == "summary_large_image"
        assert twitter_tags["twitter:title"]
        assert twitter_tags["twitter:description"]
        
        # Check HTML implementation
        html_impl = content["html_implementation"]
        assert "<title>" in html_impl
        assert '<meta name="description"' in html_impl
        assert '<meta property="og:' in html_impl
        assert '<meta name="twitter:' in html_impl
    
    @pytest.mark.asyncio
    async def test_optimize_meta_tags_healthcare(self, optimization_service):
        """Test meta tag optimization for healthcare industry"""
        request = ContentOptimizationRequest(
            brand_name="HealthCare Plus",
            domain="https://healthcareplus.com",
            industry="healthcare",
            description="Comprehensive healthcare services",
            content_type="meta_tags",
            target_keywords=["cardiology", "pediatrics", "emergency care"]
        )
        
        result = await optimization_service.optimize_meta_tags(request)
        
        # Check industry-specific patterns
        titles = result.generated_content["title_options"]
        assert any("Healthcare" in title for title in titles)
        
        descriptions = result.generated_content["description_options"]
        assert any("healthcare" in desc.lower() for desc in descriptions)
        assert any("cardiology" in desc for desc in descriptions)
    
    @pytest.mark.asyncio
    async def test_meta_compliance_scoring(self, optimization_service):
        """Test meta tag compliance scoring"""
        # Test optimal meta tags
        optimal_titles = ["TechCorp - Leading Software Solutions"]  # 35 chars
        optimal_descriptions = ["TechCorp provides advanced software technology for businesses. Specializing in software, solutions. Try free today!"]  # 125 chars
        optimal_og = {
            "og:title": "TechCorp - Leading Software Solutions",
            "og:description": "Advanced software technology",
            "og:url": "https://techcorp.com",
            "og:type": "website"
        }
        optimal_twitter = {
            "twitter:card": "summary_large_image",
            "twitter:title": "TechCorp - Leading Software Solutions",
            "twitter:description": "Advanced software technology"
        }
        
        score = await optimization_service._calculate_meta_compliance_score(
            optimal_titles, optimal_descriptions, optimal_og, optimal_twitter
        )
        assert score >= 90  # Should have high compliance
        
        # Test suboptimal meta tags
        long_titles = ["TechCorp - Leading Software Solutions Provider with Advanced Technology and Expert Support Services"]  # Too long
        long_descriptions = ["TechCorp provides advanced software technology for businesses and enterprises with comprehensive solutions and expert support services that help organizations achieve their goals and improve their operations through innovative technology solutions."]  # Too long
        minimal_og = {"og:title": "TechCorp"}
        minimal_twitter = {"twitter:card": "summary"}
        
        score = await optimization_service._calculate_meta_compliance_score(
            long_titles, long_descriptions, minimal_og, minimal_twitter
        )
        assert score < 70  # Should have lower compliance

class TestFAQGeneration(TestOptimizationService):
    """Test FAQ content generation functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_faq_content_technology(self, optimization_service):
        """Test FAQ generation for technology industry"""
        request = ContentOptimizationRequest(
            brand_name="TechCorp",
            domain="https://techcorp.com",
            industry="technology",
            description="Leading software solutions provider",
            content_type="faq"
        )
        
        result = await optimization_service.generate_faq_content(request)
        
        assert result.optimization_type == "faq_content"
        assert result.brand_name == "TechCorp"
        
        # Check generated content
        content = result.generated_content
        assert "faq_items" in content
        assert "schema_markup" in content
        assert "html_implementation" in content
        
        # Check FAQ items
        faq_items = content["faq_items"]
        assert len(faq_items) == len(INDUSTRY_FAQ_PATTERNS["technology"])
        
        for item in faq_items:
            assert "question" in item
            assert "answer" in item
            assert "TechCorp" in item["question"]
            assert "TechCorp" in item["answer"]
            assert len(item["answer"]) > 50  # Substantial answers
        
        # Check schema markup
        schema = content["schema_markup"]
        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "FAQPage"
        assert "mainEntity" in schema
        assert len(schema["mainEntity"]) == len(faq_items)
        
        for i, entity in enumerate(schema["mainEntity"]):
            assert entity["@type"] == "Question"
            assert entity["name"] == faq_items[i]["question"]
            assert entity["acceptedAnswer"]["@type"] == "Answer"
            assert entity["acceptedAnswer"]["text"] == faq_items[i]["answer"]
        
        # Check HTML implementation
        html_impl = content["html_implementation"]
        assert '<script type="application/ld+json">' in html_impl
        assert '"@type": "FAQPage"' in html_impl
        assert '<div class="faq-section">' in html_impl
        assert '<h2>Frequently Asked Questions</h2>' in html_impl
        
        # Check that all FAQ items are in HTML
        for item in faq_items:
            assert item["question"] in html_impl
            assert item["answer"] in html_impl
    
    @pytest.mark.asyncio
    async def test_generate_faq_content_healthcare(self, optimization_service):
        """Test FAQ generation for healthcare industry"""
        request = ContentOptimizationRequest(
            brand_name="HealthCare Plus",
            domain="https://healthcareplus.com",
            industry="healthcare",
            description="Comprehensive healthcare services",
            content_type="faq"
        )
        
        result = await optimization_service.generate_faq_content(request)
        
        # Check industry-specific questions
        faq_items = result.generated_content["faq_items"]
        questions = [item["question"] for item in faq_items]
        
        assert any("HIPAA" in question for question in questions)
        assert any("appointment" in question for question in questions)
        assert any("insurance" in question for question in questions)
    
    @pytest.mark.asyncio
    async def test_generate_faq_content_default_industry(self, optimization_service):
        """Test FAQ generation for default/unknown industry"""
        request = ContentOptimizationRequest(
            brand_name="GenericCorp",
            domain="https://genericcorp.com",
            industry="unknown",
            description="Quality services provider",
            content_type="faq"
        )
        
        result = await optimization_service.generate_faq_content(request)
        
        # Should use default FAQ patterns
        faq_items = result.generated_content["faq_items"]
        assert len(faq_items) == len(INDUSTRY_FAQ_PATTERNS["default"])
        
        questions = [item["question"] for item in faq_items]
        assert any("What is GenericCorp?" in question for question in questions)
        assert any("How does GenericCorp work?" in question for question in questions)
    
    @pytest.mark.asyncio
    async def test_faq_answer_generation_patterns(self, optimization_service):
        """Test FAQ answer generation for different question patterns"""
        request = ContentOptimizationRequest(
            brand_name="TestCorp",
            domain="https://testcorp.com",
            industry="technology",
            description="Software testing solutions",
            content_type="faq"
        )
        
        # Test different question patterns
        test_cases = [
            ("What is TestCorp?", "TestCorp is a leading technology company"),
            ("How does TestCorp work?", "TestCorp works by providing comprehensive"),
            ("What are TestCorp's pricing plans?", "TestCorp offers competitive pricing"),
            ("How can I contact TestCorp?", "You can contact TestCorp through our website"),
            ("Where is TestCorp located?", "TestCorp serves clients in multiple locations"),
            ("How experienced is TestCorp?", "TestCorp has extensive experience"),
            ("How do I get started with TestCorp?", "Getting started with TestCorp is easy")
        ]
        
        for question, expected_start in test_cases:
            answer = await optimization_service._generate_faq_answer(question, request)
            assert answer.startswith(expected_start), f"Question: {question}, Answer: {answer}"
            assert "TestCorp" in answer
            assert "https://testcorp.com" in answer

class TestLandingPageGeneration(TestOptimizationService):
    """Test landing page content generation functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_landing_page_content(self, optimization_service):
        """Test complete landing page generation"""
        request = ContentOptimizationRequest(
            brand_name="TechCorp",
            domain="https://techcorp.com",
            industry="technology",
            description="Leading software solutions provider",
            content_type="landing_page",
            target_keywords=["software", "solutions", "consulting"],
            target_audience="businesses"
        )
        
        result = await optimization_service.generate_landing_page_content(request)
        
        assert result.optimization_type == "landing_page"
        assert result.brand_name == "TechCorp"
        
        # Check generated content structure
        content = result.generated_content
        assert "hero_section" in content
        assert "features_section" in content
        assert "benefits_section" in content
        assert "cta_section" in content
        assert "full_template" in content
        
        # Check hero section
        hero = content["hero_section"]
        assert "headline" in hero
        assert "subheadline" in hero
        assert "cta_text" in hero
        assert "cta_url" in hero
        assert "TechCorp" in hero["headline"]
        assert hero["cta_url"] == "https://techcorp.com/contact"
        
        # Check features section
        features = content["features_section"]
        assert isinstance(features, list)
        assert len(features) >= 3
        
        for feature in features:
            assert "title" in feature
            assert "description" in feature
            assert "TechCorp" in feature["description"]
        
        # Check that target keywords are used in features
        feature_text = " ".join([f["title"] + " " + f["description"] for f in features])
        for keyword in request.target_keywords:
            assert keyword.lower() in feature_text.lower()
        
        # Check benefits section
        benefits = content["benefits_section"]
        assert isinstance(benefits, list)
        assert len(benefits) >= 3
        
        for benefit in benefits:
            assert isinstance(benefit, str)
            assert len(benefit) > 20  # Substantial benefits
        
        # Check CTA section
        cta = content["cta_section"]
        assert "headline" in cta
        assert "description" in cta
        assert "primary_cta" in cta
        assert "secondary_cta" in cta
        assert "primary_url" in cta
        assert "secondary_url" in cta
        assert "TechCorp" in cta["headline"]
        assert cta["primary_url"] == "https://techcorp.com/contact"
        assert cta["secondary_url"] == "https://techcorp.com/about"
        
        # Check full template
        full_template = content["full_template"]
        assert "<!-- Hero Section -->" in full_template
        assert "<!-- Features Section -->" in full_template
        assert "<!-- Benefits Section -->" in full_template
        assert "<!-- Call to Action Section -->" in full_template
        assert hero["headline"] in full_template
        assert cta["headline"] in full_template
    
    @pytest.mark.asyncio
    async def test_landing_page_compliance_scoring(self, optimization_service):
        """Test landing page compliance scoring"""
        # Test complete content
        complete_content = {
            "hero_section": {
                "headline": "Welcome to TechCorp Solutions",
                "subheadline": "Leading software solutions provider with comprehensive services"
            },
            "features_section": [
                {"title": "Feature 1", "description": "Description 1"},
                {"title": "Feature 2", "description": "Description 2"},
                {"title": "Feature 3", "description": "Description 3"}
            ],
            "benefits_section": [
                "Benefit 1", "Benefit 2", "Benefit 3", "Benefit 4"
            ],
            "cta_section": {
                "headline": "Ready to Get Started?",
                "description": "Contact us today to learn more about our services"
            }
        }
        
        score = await optimization_service._calculate_landing_page_compliance(complete_content)
        assert score >= 90  # Should have high compliance
        
        # Test minimal content
        minimal_content = {
            "hero_section": {"headline": "Hi"},
            "features_section": [],
            "benefits_section": [],
            "cta_section": {}
        }
        
        score = await optimization_service._calculate_landing_page_compliance(minimal_content)
        assert score < 50  # Should have low compliance

class TestOptimizationRecommendations(TestOptimizationService):
    """Test optimization recommendation generation"""
    
    @pytest.mark.asyncio
    async def test_schema_recommendations(self, optimization_service):
        """Test schema optimization recommendations"""
        recommendations = await optimization_service._generate_schema_recommendations("organization", 85)
        
        assert len(recommendations) > 0
        
        # Check recommendation structure
        for rec in recommendations:
            assert "priority" in rec
            assert "category" in rec
            assert "recommendation" in rec
            assert "implementation" in rec
            assert rec["priority"] in ["high", "medium", "low"]
        
        # Should have implementation recommendation
        assert any(rec["category"] == "implementation" for rec in recommendations)
        
        # Test low compliance score recommendations
        low_score_recs = await optimization_service._generate_schema_recommendations("organization", 60)
        assert any(rec["category"] == "data_quality" for rec in low_score_recs)
    
    @pytest.mark.asyncio
    async def test_meta_recommendations(self, optimization_service):
        """Test meta tag optimization recommendations"""
        # Test with long title
        long_titles = ["This is a very long title that exceeds the recommended 60 character limit for SEO optimization"]
        short_descriptions = ["Short description"]
        
        recommendations = await optimization_service._generate_meta_recommendations(
            long_titles, short_descriptions, 70
        )
        
        # Should recommend shortening title
        assert any("Shorten title tag" in rec["recommendation"] for rec in recommendations)
        
        # Test with long description
        short_titles = ["Short Title"]
        long_descriptions = ["This is a very long meta description that exceeds the recommended 160 character limit for SEO optimization and should be shortened for better search engine results"]
        
        recommendations = await optimization_service._generate_meta_recommendations(
            short_titles, long_descriptions, 70
        )
        
        # Should recommend shortening description
        assert any("Shorten meta description" in rec["recommendation"] for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_faq_recommendations(self, optimization_service):
        """Test FAQ optimization recommendations"""
        faq_items = [
            {"question": "What is TechCorp?", "answer": "TechCorp is a software company."},
            {"question": "How does TechCorp work?", "answer": "TechCorp provides solutions."}
        ]
        
        recommendations = await optimization_service._generate_faq_recommendations(faq_items, 85)
        
        assert len(recommendations) > 0
        
        # Should have implementation recommendation
        assert any(rec["category"] == "implementation" for rec in recommendations)
        
        # Should have content optimization recommendation
        assert any(rec["category"] == "content_optimization" for rec in recommendations)
        
        # Check that number of FAQ items is mentioned
        assert any(str(len(faq_items)) in rec["recommendation"] for rec in recommendations)

class TestOptimizationServiceIntegration(TestOptimizationService):
    """Integration tests for optimization service"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_schema_optimization(self, optimization_service):
        """Test complete schema optimization workflow"""
        request = SchemaOptimizationRequest(
            brand_name="E-Commerce Store",
            domain="https://ecommercestore.com",
            industry="retail",
            description="Online retail store with quality products",
            schema_type="organization",
            additional_data={
                "phone": "+1-555-0199",
                "email": "info@ecommercestore.com",
                "social_profiles": [
                    "https://facebook.com/ecommercestore",
                    "https://twitter.com/ecommercestore"
                ]
            }
        )
        
        result = await optimization_service.generate_schema_markup(request)
        
        # Verify complete workflow
        assert result.optimization_type == "schema_organization"
        assert result.compliance_score > 0
        assert len(result.recommendations) > 0
        assert result.timestamp
        
        # Verify schema quality
        schema = result.generated_content["schema_markup"]
        assert schema["name"] == "E-Commerce Store"
        assert schema["industry"] == "retail"
        assert len(schema["sameAs"]) == 2
        
        # Verify HTML implementation is valid JSON-LD
        html_impl = result.generated_content["html_implementation"]
        assert html_impl.startswith('<script type="application/ld+json">')
        assert html_impl.endswith('</script>')
        
        # Extract and validate JSON
        json_start = html_impl.find('{')
        json_end = html_impl.rfind('}') + 1
        json_content = html_impl[json_start:json_end]
        parsed_json = json.loads(json_content)
        assert parsed_json["@type"] == "Organization"
    
    @pytest.mark.asyncio
    async def test_end_to_end_content_optimization(self, optimization_service):
        """Test complete content optimization workflow"""
        request = ContentOptimizationRequest(
            brand_name="Digital Agency",
            domain="https://digitalagency.com",
            industry="marketing",
            description="Full-service digital marketing agency",
            content_type="meta_tags",
            target_keywords=["digital marketing", "SEO", "social media"],
            target_audience="small businesses"
        )
        
        result = await optimization_service.optimize_meta_tags(request)
        
        # Verify complete workflow
        assert result.optimization_type == "meta_tags"
        assert result.compliance_score > 0
        assert len(result.recommendations) > 0
        
        # Verify content quality
        content = result.generated_content
        
        # Check that target keywords are incorporated
        all_text = " ".join([
            " ".join(content["title_options"]),
            " ".join(content["description_options"])
        ]).lower()
        
        for keyword in request.target_keywords:
            # Keywords might be modified (e.g., "digital marketing" -> "marketing")
            keyword_parts = keyword.lower().split()
            assert any(part in all_text for part in keyword_parts)
        
        # Verify HTML implementation is valid
        html_impl = content["html_implementation"]
        assert "<title>" in html_impl
        assert 'name="description"' in html_impl
        assert 'property="og:' in html_impl
        assert 'name="twitter:' in html_impl

if __name__ == "__main__":
    pytest.main([__file__])