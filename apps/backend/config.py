"""
Configuration settings for the LLMO backend
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings"""
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Application Settings
    APP_NAME: str = "LLMO API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS Settings
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "https://localhost:3000",
    ]
    
    # Cache Settings
    CACHE_TTL_HOURS: int = int(os.getenv("CACHE_TTL_HOURS", "24"))
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Subscription Limits
    FREE_TIER_SCANS: int = int(os.getenv("FREE_TIER_SCANS", "1"))
    PRO_TIER_SCANS: int = int(os.getenv("PRO_TIER_SCANS", "10"))
    AGENCY_TIER_SCANS: int = int(os.getenv("AGENCY_TIER_SCANS", "50"))
    
    def validate_required_settings(self) -> list:
        """Validate that required settings are present"""
        missing = []
        
        if not self.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_SERVICE_KEY:
            missing.append("SUPABASE_SERVICE_KEY")
        if not self.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        
        return missing

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings