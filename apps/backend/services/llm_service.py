"""
LLM Service for interacting with various LLM providers
"""
from typing import List, Dict, Optional, Any, Tuple
import os
import re
import json
import logging
import asyncio
import hashlib
from collections import Counter
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize
from services.llm_provider import LLMProvider, OpenAIProvider, AnthropicProvider
from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('punkt')
    nltk.download('vader_lexicon')

class LLMService:
    """Service for interacting with LLM providers and analyzing responses"""
    
    def __init__(self):
        """Initialize LLM service with available providers"""
        self.providers = {}
        
        # Initialize OpenAI provider if API key is available
        if settings.OPENAI_API_KEY:
            self.providers["openai"] = OpenAIProvider()
        
        # Initialize Anthropic provider if API key is available
        if settings.ANTHROPIC_API_KEY:
            self.providers["anthropic"] = AnthropicProvider()
        
        # Initialize sentiment analyzer
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
    
    def get_provider(self, provider_name: str) -> LLMProvider:
        """Get a provider by name"""
        provider = self.providers.get(provider_name.lower())
        if not provider:
            raise ValueError(f"Provider '{provider_name}' not found or not configured")
        return provider
    
    def get_available_providers(self) -> List[str]:
        """Get a list of available provider names"""
        return list(self.providers.keys())
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get a dictionary of available models by provider"""
        models = {}
        for name, provider in self.providers.items():
            models[name] = provider.get_available_models()
        return models
    
    async def query_llm(self, prompt: str, provider_name: str = "openai", **kwargs) -> str:
        """Query an LLM with a prompt using the specified provider"""
        provider = self.get_provider(provider_name)
        return await provider.query(prompt, **kwargs)
    
    async def query_brand_visibility(
        self, 
        brand_name: str, 
        domain: str, 
        keywords: List[str], 
        model: str = "gpt-3.5-turbo",
        provider_name: str = "openai"
    ) -> Dict[str, Any]:
        """
        Query LLM for brand visibility analysis
        
        Args:
            brand_name: Name of the brand to analyze
            domain: Website domain of the brand
            keywords: List of keywords related to the brand
            model: LLM model to use
            provider_name: Provider to use (openai or anthropic)
            
        Returns:
            Dictionary with visibility analysis results
        """
        # Create a prompt that asks about products/services in the brand's industry
        industry_terms = ", ".join(keywords[:5]) if keywords else "products or services"
        
        prompts = [
            f"What are the best {industry_terms} available today?",
            f"Can you recommend some top {industry_terms} for someone looking to buy?",
            f"I'm researching {industry_terms}. What options should I consider?",
            f"What companies are known for excellent {industry_terms}?",
            f"If I need {industry_terms}, what are my best options?"
        ]
        
        results = []
        for prompt in prompts:
            response = await self.query_llm(prompt, provider_name=provider_name, model=model)
            
            # Analyze the response for brand mentions
            mention_analysis = self.detect_brand_mentions(response, brand_name)
            
            results.append({
                "prompt": prompt,
                "response": response,
                "brand_mentioned": mention_analysis["mentioned"],
                "mention_count": mention_analysis["count"],
                "mention_contexts": mention_analysis["contexts"],
                "sentiment_score": mention_analysis["sentiment_score"]
            })
        
        # Calculate overall visibility score
        visibility_score = self.calculate_visibility_score(results, brand_name)
        
        return {
            "brand_name": brand_name,
            "domain": domain,
            "model": model,
            "provider": provider_name,
            "results": results,
            "visibility_score": visibility_score,
            "mention_count": sum(r["mention_count"] for r in results),
            "average_sentiment": sum(r["sentiment_score"] for r in results if r["brand_mentioned"]) / 
                               max(1, sum(1 for r in results if r["brand_mentioned"]))
        }
    
    async def simulate_brand_prompts(
        self, 
        brand_name: str, 
        prompts: List[str],
        provider_name: str = "openai",
        model: str = "gpt-3.5-turbo",
        competitors: List[str] = None,
        batch_size: int = 5
    ) -> List[Dict]:
        """
        Simulate prompts to check brand mentions
        
        Args:
            brand_name: Name of the brand to check for
            prompts: List of prompts to test
            provider_name: Provider to use (openai or anthropic)
            model: LLM model to use
            competitors: Optional list of competitor brands to track
            batch_size: Number of prompts to process in parallel
            
        Returns:
            List of results with brand mention analysis
        """
        results = []
        competitors = competitors or []
        
        # Process prompts in batches for better performance
        for i in range(0, len(prompts), batch_size):
            batch_prompts = prompts[i:i+batch_size]
            batch_tasks = []
            
            for prompt in batch_prompts:
                # Add brand context to prompt
                enhanced_prompt = f"{prompt} (Please provide specific tool/service recommendations)"
                
                # Create task for this prompt
                task = self.query_llm(enhanced_prompt, provider_name=provider_name, model=model)
                batch_tasks.append((prompt, task))
            
            # Wait for all tasks in this batch to complete
            for prompt, task in batch_tasks:
                try:
                    response = await task
                    
                    # Analyze the response for brand mentions
                    mention_analysis = self.detect_brand_mentions(response, brand_name)
                    
                    # Track competitor mentions if competitors are provided
                    competitor_mentions = []
                    if competitors:
                        for competitor in competitors:
                            comp_analysis = self.detect_brand_mentions(response, competitor)
                            if comp_analysis["mentioned"]:
                                competitor_mentions.append({
                                    "competitor": competitor,
                                    "count": comp_analysis["count"],
                                    "sentiment": comp_analysis["sentiment_score"]
                                })
                    
                    results.append({
                        "prompt": prompt,
                        "response": response,
                        "brand_mentioned": mention_analysis["mentioned"],
                        "mention_count": mention_analysis["count"],
                        "mention_contexts": mention_analysis["contexts"],
                        "sentiment_score": mention_analysis["sentiment_score"],
                        "competitor_mentions": competitor_mentions
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing prompt '{prompt}': {e}")
                    results.append({
                        "prompt": prompt,
                        "error": str(e),
                        "brand_mentioned": False,
                        "mention_count": 0,
                        "mention_contexts": [],
                        "sentiment_score": 0.0,
                        "competitor_mentions": []
                    })
        
        return results
        
    async def get_standardized_prompts(
        self,
        brand_name: str,
        industry: str = None,
        product_category: str = None,
        competitors: List[str] = None
    ) -> List[str]:
        """
        Get standardized industry prompts for a brand
        
        Args:
            brand_name: Name of the brand
            industry: Industry category
            product_category: Product category
            competitors: List of competitor brands
            
        Returns:
            List of standardized prompts
        """
        from services.standard_prompts import get_standard_prompts, get_comparison_prompts
        
        prompts = []
        
        # Get standard prompts for the industry and product category
        standard_prompts = get_standard_prompts(industry, product_category)
        prompts.extend(standard_prompts)
        
        # Get comparison prompts if competitors are provided
        if competitors:
            comparison_prompts = get_comparison_prompts(brand_name, competitors)
            prompts.extend(comparison_prompts)
        
        return prompts
    
    async def analyze_competitors(
        self, 
        brand_name: str, 
        competitors: List[str], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze brand visibility compared to competitors
        
        Args:
            brand_name: Name of the brand to analyze
            competitors: List of competitor brand names
            context: Additional context for the analysis
            
        Returns:
            Dictionary with competitor analysis results
        """
        industry_terms = ", ".join(context.get("keywords", [])[:5]) if context.get("keywords") else "products or services"
        
        prompts = [
            f"What are the best {industry_terms} available today?",
            f"Can you recommend some top {industry_terms} for someone looking to buy?",
            f"I'm researching {industry_terms}. What options should I consider?",
            f"What companies are known for excellent {industry_terms}?",
            f"If I need {industry_terms}, what are my best options?"
        ]
        
        # Query each provider and model
        all_results = {}
        for provider_name in self.get_available_providers():
            provider = self.get_provider(provider_name)
            for model in provider.get_available_models()[:2]:  # Limit to 2 models per provider
                results = []
                
                for prompt in prompts:
                    response = await self.query_llm(prompt, provider_name=provider_name, model=model)
                    
                    # Check for brand and competitor mentions
                    brand_analysis = self.detect_brand_mentions(response, brand_name)
                    competitor_analyses = {
                        competitor: self.detect_brand_mentions(response, competitor)
                        for competitor in competitors
                    }
                    
                    results.append({
                        "prompt": prompt,
                        "response": response,
                        "brand_analysis": brand_analysis,
                        "competitor_analyses": competitor_analyses
                    })
                
                all_results[f"{provider_name}:{model}"] = results
        
        # Aggregate results
        brand_mentions = 0
        brand_sentiment = 0
        competitor_mentions = {competitor: 0 for competitor in competitors}
        competitor_sentiment = {competitor: 0 for competitor in competitors}
        
        for model, results in all_results.items():
            for result in results:
                if result["brand_analysis"]["mentioned"]:
                    brand_mentions += result["brand_analysis"]["count"]
                    brand_sentiment += result["brand_analysis"]["sentiment_score"]
                
                for competitor, analysis in result["competitor_analyses"].items():
                    if analysis["mentioned"]:
                        competitor_mentions[competitor] += analysis["count"]
                        competitor_sentiment[competitor] += analysis["sentiment_score"]
        
        # Calculate scores
        total_mentions = brand_mentions + sum(competitor_mentions.values())
        if total_mentions == 0:
            total_mentions = 1  # Avoid division by zero
            
        brand_share = (brand_mentions / total_mentions) * 100
        competitor_shares = {
            competitor: (mentions / total_mentions) * 100
            for competitor, mentions in competitor_mentions.items()
        }
        
        # Calculate average sentiment
        brand_avg_sentiment = brand_sentiment / max(1, brand_mentions)
        competitor_avg_sentiment = {
            competitor: sentiment / max(1, competitor_mentions[competitor])
            for competitor, sentiment in competitor_sentiment.items()
        }
        
        return {
            "brand_name": brand_name,
            "brand_mentions": brand_mentions,
            "brand_share": brand_share,
            "brand_sentiment": brand_avg_sentiment,
            "competitors": {
                competitor: {
                    "mentions": mentions,
                    "share": competitor_shares[competitor],
                    "sentiment": competitor_avg_sentiment[competitor]
                }
                for competitor, mentions in competitor_mentions.items()
            },
            "total_mentions": total_mentions,
            "models_used": list(all_results.keys())
        }
    
    def detect_brand_mentions(self, text: str, brand_name: str) -> Dict[str, Any]:
        """
        Detect brand mentions in text with context and sentiment analysis
        
        Args:
            text: Text to analyze
            brand_name: Brand name to look for
            
        Returns:
            Dictionary with mention analysis results
        """
        if not text or not brand_name:
            return {
                "mentioned": False,
                "count": 0,
                "contexts": [],
                "sentiment_score": 0.0
            }
        
        # Normalize text and brand name for case-insensitive matching
        text_lower = text.lower()
        brand_lower = brand_name.lower()
        
        # Count mentions
        count = text_lower.count(brand_lower)
        
        # If no mentions, return early
        if count == 0:
            return {
                "mentioned": False,
                "count": 0,
                "contexts": [],
                "sentiment_score": 0.0
            }
        
        # Extract sentences containing the brand name
        sentences = sent_tokenize(text)
        brand_sentences = [s for s in sentences if brand_lower in s.lower()]
        
        # Extract context (sentence before, sentence with mention, sentence after)
        contexts = []
        for i, sentence in enumerate(sentences):
            if brand_lower in sentence.lower():
                context = {
                    "sentence": sentence,
                    "previous": sentences[i-1] if i > 0 else "",
                    "next": sentences[i+1] if i < len(sentences)-1 else ""
                }
                contexts.append(context)
        
        # Analyze sentiment for each mention context
        sentiment_scores = []
        for context in contexts:
            # Analyze the sentence containing the mention and surrounding sentences
            context_text = f"{context['previous']} {context['sentence']} {context['next']}".strip()
            sentiment = self.sentiment_analyzer.polarity_scores(context_text)
            sentiment_scores.append(sentiment["compound"])
        
        # Calculate average sentiment score
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        
        return {
            "mentioned": True,
            "count": count,
            "contexts": contexts,
            "sentiment_score": avg_sentiment
        }
    
    def calculate_visibility_score(self, results: List[Dict[str, Any]], brand_name: str) -> int:
        """
        Calculate visibility score based on mention frequency and context
        
        Args:
            results: List of query results with mention analysis
            brand_name: Brand name that was analyzed
            
        Returns:
            Visibility score from 0-100
        """
        # Base score components
        mention_score = 0
        sentiment_score = 0
        context_score = 0
        
        # Count total mentions
        total_mentions = sum(r["mention_count"] for r in results)
        
        # Calculate mention score (max 40 points)
        # 0 mentions = 0, 1-2 mentions = 10, 3-5 mentions = 20, 6-9 mentions = 30, 10+ mentions = 40
        if total_mentions == 0:
            mention_score = 0
        elif total_mentions <= 2:
            mention_score = 10
        elif total_mentions <= 5:
            mention_score = 20
        elif total_mentions <= 9:
            mention_score = 30
        else:
            mention_score = 40
        
        # Calculate sentiment score (max 30 points)
        # Average sentiment from -1 to 1, scaled to 0-30
        avg_sentiment = sum(r["sentiment_score"] for r in results if r["brand_mentioned"]) / \
                      max(1, sum(1 for r in results if r["brand_mentioned"]))
        sentiment_score = int((avg_sentiment + 1) / 2 * 30)
        
        # Calculate context score (max 30 points)
        # Based on position in response and surrounding context
        mentioned_results = [r for r in results if r["brand_mentioned"]]
        if mentioned_results:
            # Check if brand is mentioned first in any response
            first_mentions = sum(1 for r in mentioned_results if any(
                brand_name.lower() in c["sentence"].lower() and 
                c["previous"] == "" for c in r["mention_contexts"]
            ))
            
            # Check if brand is mentioned with positive descriptors
            positive_contexts = sum(1 for r in mentioned_results for c in r["mention_contexts"] 
                                if self.sentiment_analyzer.polarity_scores(c["sentence"])["compound"] > 0.5)
            
            # Calculate context score
            context_score = min(30, (first_mentions * 10) + (positive_contexts * 5))
        
        # Calculate total score (0-100)
        total_score = mention_score + sentiment_score + context_score
        
        # Ensure score is within 0-100 range
        return max(0, min(100, total_score))