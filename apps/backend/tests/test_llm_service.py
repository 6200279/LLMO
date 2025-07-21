"""
Tests for LLM service and provider implementations
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from services.llm_service import LLMService
from services.llm_provider import OpenAIProvider, AnthropicProvider

# Sample test responses
SAMPLE_RESPONSE_WITH_BRAND = """
When looking for project management software, there are several excellent options to consider:

1. Asana - A popular task management tool with a clean interface
2. Trello - Visual kanban-style project management
3. Monday.com - Highly customizable project management platform
4. Jira - Robust tool especially good for software development
5. ClickUp - Feature-rich platform with good free tier options

Each of these tools has different strengths. Asana is particularly good for team collaboration and has excellent integration options.
"""

SAMPLE_RESPONSE_WITHOUT_BRAND = """
When looking for project management software, there are several excellent options to consider:

1. Trello - Visual kanban-style project management
2. Monday.com - Highly customizable project management platform
3. Jira - Robust tool especially good for software development
4. ClickUp - Feature-rich platform with good free tier options
5. Notion - All-in-one workspace for notes and project management

Each of these tools has different strengths depending on your specific needs.
"""

@pytest.fixture
def llm_service():
    """Create a LLM service instance for testing"""
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_openai_key",
        "ANTHROPIC_API_KEY": "test_anthropic_key"
    }):
        service = LLMService()
        return service

@pytest.fixture
def mock_openai_provider():
    """Create a mock OpenAI provider"""
    with patch("services.llm_provider.OpenAIProvider") as mock:
        provider = mock.return_value
        provider.query.return_value = "Mock OpenAI response"
        provider.get_available_models.return_value = ["gpt-3.5-turbo", "gpt-4"]
        provider.validate_api_key.return_value = True
        yield provider

@pytest.fixture
def mock_anthropic_provider():
    """Create a mock Anthropic provider"""
    with patch("services.llm_provider.AnthropicProvider") as mock:
        provider = mock.return_value
        provider.query.return_value = "Mock Anthropic response"
        provider.get_available_models.return_value = ["claude-3-opus-20240229", "claude-3-sonnet-20240229"]
        provider.validate_api_key.return_value = True
        yield provider

class TestLLMProviders:
    """Tests for LLM provider implementations"""
    
    @pytest.mark.asyncio
    async def test_openai_provider_query(self, mock_openai_provider):
        """Test OpenAI provider query method"""
        provider = OpenAIProvider()
        
        # Mock the OpenAI client
        provider.client = MagicMock()
        provider.client.chat.completions.create.return_value.choices[0].message.content = "Test response"
        
        response = await provider.query("Test prompt")
        
        assert response == "Test response"
        provider.client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_anthropic_provider_query(self, mock_anthropic_provider):
        """Test Anthropic provider query method"""
        provider = AnthropicProvider()
        
        # Mock the Anthropic client
        provider.client = MagicMock()
        provider.client.messages.create.return_value.content[0].text = "Test response"
        
        response = await provider.query("Test prompt")
        
        assert response == "Test response"
        provider.client.messages.create.assert_called_once()
    
    def test_provider_cache_key_generation(self):
        """Test cache key generation"""
        provider = OpenAIProvider()
        
        key1 = provider.generate_cache_key("Test prompt", "gpt-3.5-turbo")
        key2 = provider.generate_cache_key("Test prompt", "gpt-4")
        key3 = provider.generate_cache_key("Different prompt", "gpt-3.5-turbo")
        
        # Same prompt, different models should have different keys
        assert key1 != key2
        
        # Different prompts, same model should have different keys
        assert key1 != key3

class TestLLMService:
    """Tests for LLM service implementation"""
    
    def test_get_available_providers(self, llm_service):
        """Test getting available providers"""
        providers = llm_service.get_available_providers()
        
        assert "openai" in providers
        assert "anthropic" in providers
    
    def test_get_available_models(self, llm_service):
        """Test getting available models"""
        models = llm_service.get_available_models()
        
        assert "openai" in models
        assert "anthropic" in models
        assert isinstance(models["openai"], list)
        assert isinstance(models["anthropic"], list)
    
    @pytest.mark.asyncio
    async def test_query_llm(self, llm_service, mock_openai_provider, mock_anthropic_provider):
        """Test querying LLM with different providers"""
        # Replace the actual providers with mocks
        llm_service.providers["openai"] = mock_openai_provider
        llm_service.providers["anthropic"] = mock_anthropic_provider
        
        openai_response = await llm_service.query_llm("Test prompt", provider_name="openai")
        anthropic_response = await llm_service.query_llm("Test prompt", provider_name="anthropic")
        
        assert openai_response == "Mock OpenAI response"
        assert anthropic_response == "Mock Anthropic response"
        
        mock_openai_provider.query.assert_called_once()
        mock_anthropic_provider.query.assert_called_once()
    
    def test_detect_brand_mentions_with_brand(self, llm_service):
        """Test brand mention detection with brand present"""
        result = llm_service.detect_brand_mentions(SAMPLE_RESPONSE_WITH_BRAND, "Asana")
        
        assert result["mentioned"] is True
        assert result["count"] == 2  # Mentioned twice in the sample
        assert len(result["contexts"]) > 0
        assert isinstance(result["sentiment_score"], float)
    
    def test_detect_brand_mentions_without_brand(self, llm_service):
        """Test brand mention detection with brand absent"""
        result = llm_service.detect_brand_mentions(SAMPLE_RESPONSE_WITHOUT_BRAND, "Asana")
        
        assert result["mentioned"] is False
        assert result["count"] == 0
        assert len(result["contexts"]) == 0
    
    def test_calculate_visibility_score(self, llm_service):
        """Test visibility score calculation"""
        # Test with no mentions
        no_mentions = [
            {"brand_mentioned": False, "mention_count": 0, "sentiment_score": 0, "mention_contexts": []}
        ]
        score_none = llm_service.calculate_visibility_score(no_mentions, "TestBrand")
        assert score_none == 0
        
        # Test with few mentions
        few_mentions = [
            {
                "brand_mentioned": True, 
                "mention_count": 2, 
                "sentiment_score": 0.5,
                "mention_contexts": [
                    {"sentence": "TestBrand is good.", "previous": "", "next": "It has features."}
                ]
            }
        ]
        score_few = llm_service.calculate_visibility_score(few_mentions, "TestBrand")
        assert 0 < score_few < 100
        
        # Test with many mentions and positive sentiment
        many_mentions = [
            {
                "brand_mentioned": True, 
                "mention_count": 5, 
                "sentiment_score": 0.8,
                "mention_contexts": [
                    {"sentence": "TestBrand is excellent.", "previous": "", "next": "It has many features."},
                    {"sentence": "I recommend TestBrand.", "previous": "For project management.", "next": ""}
                ]
            },
            {
                "brand_mentioned": True, 
                "mention_count": 7, 
                "sentiment_score": 0.9,
                "mention_contexts": [
                    {"sentence": "TestBrand is the best.", "previous": "", "next": "Nothing compares."}
                ]
            }
        ]
        score_many = llm_service.calculate_visibility_score(many_mentions, "TestBrand")
        assert score_many > score_few
    
    @pytest.mark.asyncio
    async def test_simulate_brand_prompts(self, llm_service):
        """Test simulating brand prompts"""
        # Mock the query_llm method
        llm_service.query_llm = MagicMock()
        llm_service.query_llm.return_value = SAMPLE_RESPONSE_WITH_BRAND
        
        results = await llm_service.simulate_brand_prompts(
            "Asana", 
            ["What are the best project management tools?"]
        )
        
        assert len(results) == 1
        assert results[0]["brand_mentioned"] is True
        assert results[0]["mention_count"] > 0
        assert len(results[0]["mention_contexts"]) > 0
        assert isinstance(results[0]["sentiment_score"], float)