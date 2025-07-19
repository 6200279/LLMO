"""
LLM Service for interacting with various LLM providers
"""
import openai
from typing import List, Dict, Optional
import os

class LLMService:
    def __init__(self):
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    async def query_openai(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """Query OpenAI GPT models"""
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error querying OpenAI: {str(e)}"
    
    async def simulate_brand_prompts(self, brand_name: str, prompts: List[str]) -> List[Dict]:
        """Simulate prompts to check brand mentions"""
        results = []
        
        for prompt in prompts:
            # Add brand context to prompt
            enhanced_prompt = f"{prompt} (Please provide specific tool/service recommendations)"
            
            response = await self.query_openai(enhanced_prompt)
            
            # Check if brand is mentioned
            brand_mentioned = brand_name.lower() in response.lower()
            
            results.append({
                "prompt": prompt,
                "response": response,
                "brand_mentioned": brand_mentioned,
                "response_length": len(response)
            })
        
        return results