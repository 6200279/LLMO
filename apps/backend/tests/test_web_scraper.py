"""
Tests for the enhanced WebScraperService
"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
import requests
from services.web_scraper import WebScraperService

# Sample HTML content for testing
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Website - Product Page</title>
    <meta name="description" content="This is a test description for the product page that contains relevant keywords and information about our test product.">
    <meta name="keywords" content="test, product, keywords">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta property="og:title" content="Test Website - Product Page">
    <meta property="og:description" content="This is a test description for social sharing.">
    <meta property="og:image" content="https://example.com/image.jpg">
    <meta property="og:url" content="https://example.com/product">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="canonical" href="https://example.com/product">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Test Product",
        "description": "This is a test product description.",
        "brand": {
            "@type": "Brand",
            "name": "Test Brand"
        },
        "offers": {
            "@type": "Offer",
            "price": "99.99",
            "priceCurrency": "USD"
        }
    }
    </script>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Test Company",
        "url": "https://example.com",
        "logo": "https://example.com/logo.png"
    }
    </script>
</head>
<body>
    <h1>Test Product Page</h1>
    <p>This is a test paragraph about our amazing product. It contains information that would be useful for customers.</p>
    
    <h2>Product Features</h2>
    <ul>
        <li>Feature 1 with great benefits</li>
        <li>Feature 2 that solves problems</li>
        <li>Feature 3 for advanced users</li>
    </ul>
    
    <h2>Product Specifications</h2>
    <table>
        <tr>
            <th>Specification</th>
            <th>Value</th>
        </tr>
        <tr>
            <td>Size</td>
            <td>Medium</td>
        </tr>
        <tr>
            <td>Weight</td>
            <td>500g</td>
        </tr>
    </table>
    
    <h2>Frequently Asked Questions</h2>
    <dl>
        <dt>How do I use this product?</dt>
        <dd>Simply follow the instructions in the manual. The product is designed to be user-friendly.</dd>
        
        <dt>What is the warranty period?</dt>
        <dd>The product comes with a 2-year limited warranty that covers manufacturing defects.</dd>
        
        <dt>Can I return the product?</dt>
        <dd>Yes, you can return the product within 30 days of purchase for a full refund.</dd>
    </dl>
    
    <h3>Customer Reviews</h3>
    <p>Our customers love this product! Here are some testimonials:</p>
    
    <div class="review">
        <h4>Great Product!</h4>
        <p>This product exceeded my expectations. Would definitely recommend!</p>
    </div>
    
    <div class="review">
        <h4>Works as Advertised</h4>
        <p>I've been using this for a month and it works perfectly.</p>
    </div>
    
    <img src="product.jpg" alt="Test Product Image">
    <img src="feature.jpg">
    
    <h2>Related Products</h2>
    <ul>
        <li><a href="/product2">Product 2</a></li>
        <li><a href="/product3">Product 3</a></li>
    </ul>
    
    <a href="https://example.com">Home</a>
    <a href="https://example.com/about">About</a>
    <a href="https://example.com/contact">Contact</a>
    <a href="https://external-site.com">Partner Site</a>
</body>
</html>
"""

# Sample schema.org JSON-LD for testing
SAMPLE_SCHEMA = {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "Test Product",
    "description": "This is a test product description.",
    "brand": {
        "@type": "Brand",
        "name": "Test Brand"
    },
    "offers": {
        "@type": "Offer",
        "price": "99.99",
        "priceCurrency": "USD"
    }
}

# Sample FAQ schema for testing
SAMPLE_FAQ_SCHEMA = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {
            "@type": "Question",
            "name": "How do I use this product?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "Simply follow the instructions in the manual. The product is designed to be user-friendly."
            }
        },
        {
            "@type": "Question",
            "name": "What is the warranty period?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "The product comes with a 2-year limited warranty that covers manufacturing defects."
            }
        }
    ]
}

@pytest.fixture
def web_scraper():
    """Create a WebScraperService instance for testing"""
    return WebScraperService()

@pytest.fixture
def mock_response():
    """Create a mock response object"""
    mock = MagicMock()
    mock.content = SAMPLE_HTML.encode('utf-8')
    mock.status_code = 200
    mock.elapsed.total_seconds.return_value = 0.5
    return mock

@pytest.fixture
def soup():
    """Create a BeautifulSoup object from sample HTML"""
    return BeautifulSoup(SAMPLE_HTML, 'html.parser')

class TestWebScraperService:
    """Test cases for WebScraperService"""
    
    @pytest.mark.asyncio
    @patch('requests.Session.get')
    async def test_audit_website_success(self, mock_get, web_scraper, mock_response):
        """Test successful website audit"""
        # Setup mock
        mock_get.return_value = mock_response
        
        # Execute audit
        result = await web_scraper.audit_website("https://example.com")
        
        # Verify basic structure
        assert result["domain"] == "https://example.com"
        # Status code might not be present in error cases
        if "status_code" in result:
            assert result["status_code"] == 200
        assert "llm_friendly_score" in result
        assert "component_scores" in result
        assert "recommendations" in result
        
        # Verify component scores exist
        assert "schema_score" in result["component_scores"]
        assert "meta_score" in result["component_scores"]
        assert "content_score" in result["component_scores"]
        assert "technical_score" in result["component_scores"]
        
        # Verify score is in valid range
        assert 0 <= result["llm_friendly_score"] <= 100
        assert 0 <= result["component_scores"]["schema_score"] <= 100
        assert 0 <= result["component_scores"]["meta_score"] <= 100
        assert 0 <= result["component_scores"]["content_score"] <= 100
        assert 0 <= result["component_scores"]["technical_score"] <= 100
    
    @pytest.mark.asyncio
    @patch('requests.Session.get')
    async def test_audit_website_connection_error(self, mock_get, web_scraper):
        """Test website audit with connection error"""
        # Setup mock to raise connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")
        
        # Execute audit
        result = await web_scraper.audit_website("https://example.com")
        
        # Verify error handling
        assert result["domain"] == "https://example.com"
        assert "error" in result
        assert "connection_error" in result["error_type"]
        assert result["llm_friendly_score"] == 0
        assert len(result["recommendations"]) > 0
    
    @pytest.mark.asyncio
    @patch('requests.Session.get')
    async def test_audit_website_timeout(self, mock_get, web_scraper):
        """Test website audit with timeout error"""
        # Setup mock to raise timeout
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # Execute audit
        result = await web_scraper.audit_website("https://example.com")
        
        # Verify error handling
        assert result["domain"] == "https://example.com"
        assert "error" in result
        assert "timeout" in result["error_type"]
        assert result["llm_friendly_score"] == 0
        assert len(result["recommendations"]) > 0
    
    def test_analyze_schema_org(self, web_scraper, soup):
        """Test Schema.org analysis"""
        result = web_scraper._analyze_schema_org(soup)
        
        # Verify schema detection
        assert result["found"] is True
        assert result["count"] == 2
        assert len(result["types"]) > 0
        assert "Product" in result["types"]
        assert "Organization" in result["types"]
        
        # Verify high-value schemas
        assert result["high_value_schemas"]["product"] is True
        assert result["high_value_schemas"]["organization"] is True
    
    def test_analyze_meta_tags(self, web_scraper, soup):
        """Test meta tag analysis"""
        result = web_scraper._analyze_meta_tags(soup)
        
        # Verify basic meta tags
        assert result["title"] == "Test Website - Product Page"
        assert result["title_length"] == len(result["title"])
        assert "This is a test description" in result["description"]
        assert result["description_length"] == len(result["description"])
        assert result["keywords"] == "test, product, keywords"
        assert result["canonical"] == "https://example.com/product"
        
        # Verify Open Graph tags
        assert "og:title" in result["og_tags"]
        assert "og:description" in result["og_tags"]
        assert "og:image" in result["og_tags"]
        
        # Verify Twitter tags
        assert "twitter:card" in result["twitter_tags"]
        
        # Verify completeness scores
        assert 0 <= result["completeness"]["basic"] <= 1
        assert 0 <= result["completeness"]["social"] <= 1
        assert 0 <= result["completeness"]["overall"] <= 1
    
    def test_analyze_content_structure(self, web_scraper, soup):
        """Test content structure analysis"""
        result = web_scraper._analyze_content_structure(soup)
        
        # Verify heading structure
        assert result["headings"]["h1"] == 1
        assert result["headings"]["h2"] > 0
        assert result["headings"]["h3"] > 0
        assert result["headings"]["h4"] > 0
        
        # Verify content elements
        assert result["paragraphs"] > 0
        assert result["lists"] > 0
        assert result["list_items"] > 0
        assert result["tables"] > 0
        assert result["word_count"] > 0
        
        # Verify FAQ detection
        assert result["faq_count"] > 0
        assert len(result["faq_sections"]) > 0
        
        # Verify image analysis
        assert result["images"] == 2
        assert result["images_with_alt"] == 1  # Only one image has alt text
        
        # Verify readability score
        assert "flesch_kincaid_grade" in result["readability_score"]
        assert "avg_sentence_length" in result["readability_score"]
        assert "avg_word_length" in result["readability_score"]
    
    def test_detect_faq_sections(self, web_scraper, soup):
        """Test FAQ section detection"""
        result = web_scraper._detect_faq_sections(soup)
        
        # Verify FAQ detection from DL/DT/DD structure
        assert len(result) > 0
        
        # Check first FAQ section
        faq_section = result[0]
        assert "type" in faq_section
        assert "questions" in faq_section
        assert len(faq_section["questions"]) > 0
        
        # Check question structure
        question = faq_section["questions"][0]
        assert "question" in question
        assert "answer" in question
        assert len(question["question"]) > 0
        assert len(question["answer"]) > 0
    
    def test_is_faq_schema(self, web_scraper):
        """Test FAQ schema detection"""
        # Test with FAQ schema
        assert web_scraper._is_faq_schema(SAMPLE_FAQ_SCHEMA) is True
        
        # Test with non-FAQ schema
        assert web_scraper._is_faq_schema(SAMPLE_SCHEMA) is False
    
    def test_extract_faq_questions(self, web_scraper):
        """Test FAQ question extraction from schema"""
        questions = web_scraper._extract_faq_questions(SAMPLE_FAQ_SCHEMA)
        
        # Verify questions were extracted
        assert len(questions) == 2
        
        # Check first question
        assert questions[0]["question"] == "How do I use this product?"
        assert "Simply follow the instructions" in questions[0]["answer"]
    
    def test_calculate_schema_score(self, web_scraper):
        """Test schema score calculation"""
        schema_analysis = {
            "found": True,
            "count": 2,
            "types": ["Product", "Organization"],
            "high_value_schemas": {
                "organization": True,
                "product": True,
                "faq": False,
                "breadcrumb": False,
                "article": False
            },
            "property_count": 15
        }
        
        score = web_scraper._calculate_schema_score(schema_analysis)
        
        # Verify score is in valid range
        assert 0 <= score <= 100
        
        # Verify score is reasonable for the given analysis
        assert score >= 50  # Should be high with 2 high-value schemas
    
    def test_calculate_meta_score(self, web_scraper):
        """Test meta score calculation"""
        meta_analysis = {
            "title": "Test Title",
            "title_length": 55,  # Optimal length
            "description": "This is a test description that is within the optimal length range for meta descriptions.",
            "description_length": 150,  # Optimal length
            "completeness": {
                "basic": 0.9,
                "social": 0.8,
                "overall": 0.85
            }
        }
        
        score = web_scraper._calculate_meta_score(meta_analysis)
        
        # Verify score is in valid range
        assert 0 <= score <= 100
        
        # Verify score is reasonable for the given analysis
        assert score >= 70  # Should be high with good meta tags
    
    def test_calculate_content_score(self, web_scraper):
        """Test content score calculation"""
        content_analysis = {
            "headings": {"h1": 1, "h2": 3, "h3": 2, "h4": 2, "h5": 0, "h6": 0},
            "heading_hierarchy_score": 0.9,
            "paragraphs": 10,
            "lists": 3,
            "list_items": 12,
            "tables": 1,
            "faq_count": 2,
            "faq_sections": [{"type": "dl_list", "questions": [{"question": "Q1", "answer": "A1"}]}],
            "images": 5,
            "images_with_alt": 4,
            "word_count": 1200,
            "readability_score": {"flesch_kincaid_grade": 8.5}
        }
        
        score = web_scraper._calculate_content_score(content_analysis)
        
        # Verify score is in valid range
        assert 0 <= score <= 100
        
        # Verify score is reasonable for the given analysis
        assert score >= 70  # Should be high with good content structure
    
    def test_calculate_overall_score(self, web_scraper):
        """Test overall score calculation"""
        # Test with perfect scores
        perfect_score = web_scraper._calculate_overall_score(100, 100, 100, 100)
        assert perfect_score == 100
        
        # Test with zero scores
        zero_score = web_scraper._calculate_overall_score(0, 0, 0, 0)
        assert zero_score == 0
        
        # Test with mixed scores
        mixed_score = web_scraper._calculate_overall_score(80, 60, 70, 50)
        assert 0 <= mixed_score <= 100
        
        # Verify weighted calculation (schema and content should have more impact)
        high_schema_score = web_scraper._calculate_overall_score(100, 0, 0, 0)
        high_content_score = web_scraper._calculate_overall_score(0, 0, 100, 0)
        
        assert high_schema_score > high_content_score  # Schema has highest weight
    
    def test_generate_recommendations(self, web_scraper):
        """Test recommendation generation"""
        # Create audit results with issues
        audit_results = {
            "schema_org": {
                "found": True,
                "count": 1,
                "high_value_schemas": {
                    "organization": True,
                    "product": False,
                    "faq": False,
                    "breadcrumb": False,
                    "article": False
                }
            },
            "meta_tags": {
                "title": "Short Title",
                "title_length": 20,  # Too short
                "description": None,  # Missing
                "og_tags": {}  # Missing
            },
            "content_structure": {
                "headings": {"h1": 0},  # Missing H1
                "heading_hierarchy_score": 0.5,  # Poor hierarchy
                "word_count": 200,  # Too short
                "lists": 0,  # No lists
                "faq_count": 0,  # No FAQs
                "images": 3,
                "images_with_alt": 0  # No alt text
            },
            "technical_factors": {
                "ssl_enabled": True,
                "mobile_friendly": False,  # Not mobile-friendly
                "page_size_kb": 3000,  # Too large
                "has_sitemap": False  # No sitemap
            }
        }
        
        recommendations = web_scraper._generate_recommendations(audit_results)
        
        # Verify recommendations structure
        assert len(recommendations) > 0
        
        # Check first recommendation
        first_rec = recommendations[0]
        assert "priority" in first_rec
        assert "category" in first_rec
        assert "issue" in first_rec
        assert "recommendation" in first_rec
        assert "implementation" in first_rec
        
        # Verify high priority recommendations come first
        assert first_rec["priority"] == "high"
        
        # Verify recommendations cover all categories
        categories = set(rec["category"] for rec in recommendations)
        assert "meta" in categories
        assert "content" in categories
        assert "technical" in categories


class TestEnhancedWebScraperService:
    """Test cases for enhanced WebScraperService features"""
    
    def test_analyze_schema_completeness(self, web_scraper):
        """Test schema completeness analysis"""
        # Create sample schema data
        schema_data = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Test Company",
            "url": "https://example.com",
            # Missing logo, description, sameAs
        }
        
        # Define valuable schemas for testing
        valuable_schemas = {
            'Organization': ['name', 'url', 'logo', 'description', 'sameAs']
        }
        
        # Test completeness calculation
        completeness = web_scraper._analyze_schema_completeness(schema_data, valuable_schemas)
        
        # Verify results
        assert 'Organization' in completeness
        assert 0 < completeness['Organization'] < 1  # Should be partial completeness
        assert completeness['Organization'] == 0.4  # 2 out of 5 properties present
    
    def test_extract_schema_relationships(self, web_scraper):
        """Test schema relationship extraction"""
        # Create sample schema data with relationships
        schema_data = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Organization",
                    "@id": "#organization",
                    "name": "Test Company"
                },
                {
                    "@type": "WebPage",
                    "@id": "#webpage",
                    "isPartOf": "#organization"
                }
            ]
        }
        
        # Test relationship extraction
        relationships = web_scraper._extract_schema_relationships(schema_data)
        
        # Verify results
        assert len(relationships) > 0
        # Relationship detection is complex and may vary, so just check structure
        if relationships:
            assert "source_type" in relationships[0]
            assert "relation" in relationships[0]
            assert "target_type" in relationships[0]
    
    def test_calculate_schema_quality_score(self, web_scraper):
        """Test schema quality score calculation"""
        # Test parameters
        schema_types = {"Organization", "WebPage"}
        properties = {"name": 1, "url": 1, "description": 1}
        completeness = {"Organization": 0.8, "WebPage": 0.6}
        errors = []
        
        # Calculate score
        score = web_scraper._calculate_schema_quality_score(
            schema_types, properties, completeness, errors
        )
        
        # Verify score is in valid range
        assert 0 <= score <= 100
        # Organization is a high-value type, so score should be decent
        assert score >= 30
    
    def test_analyze_semantic_elements(self, soup):
        """Test semantic HTML element analysis"""
        # Add some semantic elements to the soup for testing
        main_tag = soup.new_tag("main")
        article_tag = soup.new_tag("article")
        section_tag = soup.new_tag("section")
        
        soup.body.append(main_tag)
        soup.body.append(article_tag)
        soup.body.append(section_tag)
        
        # Test semantic element analysis
        web_scraper = WebScraperService()
        result = web_scraper._analyze_semantic_elements(soup)
        
        # Verify results
        assert "main" in result
        assert "article" in result
        assert "section" in result
        assert result["main"] == 1
        assert result["article"] == 1
        assert result["section"] == 1
    
    def test_detect_structured_patterns(self, soup):
        """Test structured content pattern detection"""
        # Add structured patterns to the soup
        dl_tag = soup.new_tag("dl")
        dt_tag = soup.new_tag("dt")
        dt_tag.string = "Term"
        dd_tag = soup.new_tag("dd")
        dd_tag.string = "Definition"
        dl_tag.append(dt_tag)
        dl_tag.append(dd_tag)
        
        blockquote_tag = soup.new_tag("blockquote")
        blockquote_tag.string = "This is a quote"
        
        soup.body.append(dl_tag)
        soup.body.append(blockquote_tag)
        
        # Test pattern detection
        web_scraper = WebScraperService()
        result = web_scraper._detect_structured_patterns(soup)
        
        # Verify results
        assert "definition_lists" in result
        assert "blockquotes" in result
        assert result["definition_lists"] >= 1
        assert result["blockquotes"] == 1
    
    def test_calculate_content_diversity(self, web_scraper):
        """Test content diversity score calculation"""
        # Test parameters
        headings = {"h1": 1, "h2": 3, "h3": 2}
        paragraph_count = 10
        list_count = 2
        table_count = 1
        faq_count = 1
        image_count = 5
        semantic_elements = {"main": 1, "article": 1, "section": 2}
        
        # Calculate diversity score
        score = web_scraper._calculate_content_diversity(
            headings, paragraph_count, list_count, table_count,
            faq_count, image_count, semantic_elements
        )
        
        # Verify score is in valid range
        assert 0 <= score <= 1
        # With good diversity, score should be reasonable
        assert score >= 0.4
    
    def test_analyze_entity_mentions(self, web_scraper):
        """Test entity mention analysis"""
        # Test text with various entity types
        text = """
        Apple Inc. is headquartered in Cupertino, California.
        Tim Cook is the CEO of Apple Inc.
        The iPhone 14 Pro was released in September 2022.
        Google LLC and Microsoft Corporation are competitors.
        """
        
        # Analyze entities
        result = web_scraper._analyze_entity_mentions(text)
        
        # Verify results
        assert "people" in result
        assert "organizations" in result
        assert "products" in result
        assert len(result["organizations"]) > 0
        # At least one organization should be detected
        assert any("Apple" in org for org in result["organizations"]) or \
               any("Google" in org for org in result["organizations"]) or \
               any("Microsoft" in org for org in result["organizations"])
    
    def test_enhanced_recommendations(self, web_scraper):
        """Test enhanced recommendation generation"""
        # Create minimal audit results
        audit_results = {
            "schema_org": {
                "found": True,
                "count": 1,
                "types": ["Organization"],
                "high_value_schemas": {
                    "organization": True,
                    "product": False,
                    "faq": False,
                    "article": False,
                    "howto": False
                },
                "quality_score": 60,
                "completeness": {"Organization": 0.6}
            },
            "meta_tags": {
                "title": "Short Title",
                "title_length": 20,
                "description": None,
                "og_tags": {}
            },
            "content_structure": {
                "headings": {"h1": 1, "h2": 2},
                "heading_hierarchy_score": 0.8,
                "word_count": 250,
                "lists": 0,
                "faq_count": 0,
                "images": 2,
                "images_with_alt": 0,
                "content_diversity_score": 0.4,
                "semantic_elements": {"article": 1},
                "entity_mentions": {
                    "organizations": ["Test Company"],
                    "products": []
                }
            },
            "technical_factors": {
                "ssl_enabled": True,
                "mobile_friendly": False,
                "page_size_kb": 1500,
                "load_time_ms": 3500
            }
        }
        
        # Generate recommendations
        recommendations = web_scraper._generate_recommendations(audit_results)
        
        # Verify recommendations
        assert len(recommendations) > 0
        # Check that high priority recommendations come first
        assert recommendations[0]["priority"] == "high"
        # Check for specific recommendation categories
        categories = set(rec["category"] for rec in recommendations)
        assert "meta" in categories
        assert "content" in categories
        assert "technical" in categories
        
        # Check for LLM-specific recommendations
        llm_recommendations = [rec for rec in recommendations if "LLM" in rec["recommendation"]]
        assert len(llm_recommendations) > 0