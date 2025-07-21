"""
Abstract LLM provider interface and implementations for multiple AI services
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import os
import openai
import anthropic
import logging
import hashlib
import json
import re
from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def query(self, prompt: str, **kwargs) -> str:
        """Query the LLM with a prompt and return the response"""
        pass
    
    @abstractmethod
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for the provider"""
        pass
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """Validate that the API key is valid"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get a list of available models from this provider"""
        pass
    
    def generate_cache_key(self, prompt: str, model: str) -> str:
        """Generate a cache key for a prompt and model"""
        # Create a hash of the prompt and model to use as a cache key
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        return f"{self.__class__.__name__}:{model}:{prompt_hash}"


class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation"""
    
    def __init__(self):
        """Initialize the OpenAI provider with API key"""
        self.api_key = settings.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=self.api_key)
        self.available_models = ["gpt-3.5-turbo", "gpt-4"]
    
    async def query(self, prompt: str, **kwargs) -> str:
        """Query OpenAI models with a prompt"""
        try:
            model = kwargs.get("model", "gpt-3.5-turbo")
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 500)
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error querying OpenAI: {str(e)}")
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for OpenAI"""
        # Note: OpenAI doesn't provide a direct usage stats API
        # This would need to be implemented with custom tracking
        return {
            "provider": "OpenAI",
            "available": True,
            "tracking_supported": False
        }
    
    async def validate_api_key(self) -> bool:
        """Validate OpenAI API key"""
        try:
            # Make a minimal API call to validate the key
            self.client.models.list(limit=1)
            return True
        except Exception as e:
            logger.error(f"OpenAI API key validation failed: {str(e)}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get available OpenAI models"""
        return self.available_models


class AnthropicProvider(LLMProvider):
    """Anthropic API provider implementation"""
    
    def __init__(self):
        """Initialize the Anthropic provider with API key"""
        self.api_key = settings.ANTHROPIC_API_KEY
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.available_models = ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
    
    async def query(self, prompt: str, **kwargs) -> str:
        """Query Anthropic Claude models with a prompt"""
        try:
            model = kwargs.get("model", "claude-3-sonnet-20240229")
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 500)
            
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error querying Anthropic: {str(e)}")
            raise Exception(f"Anthropic API error: {str(e)}")
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for Anthropic"""
        # Note: Anthropic doesn't provide a direct usage stats API
        return {
            "provider": "Anthropic",
            "available": True,
            "tracking_supported": False
        }
    
    async def validate_api_key(self) -> bool:
        """Validate Anthropic API key"""
        try:
            # Make a minimal API call to validate the key
            self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[
                    {"role": "user", "content": "Hello"}
                ]
            )
            return True
        except Exception as e:
            logger.error(f"Anthropic API key validation failed: {str(e)}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get available Anthropic models"""
        return self.available_models