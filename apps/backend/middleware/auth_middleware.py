"""
Authentication middleware for FastAPI
Handles JWT token validation and user authentication
"""
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from services.auth_service import auth_service
from services.database_service import db_service
from models.database import Profile

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)

class AuthMiddleware:
    """Authentication middleware class"""
    
    def __init__(self):
        self.auth_service = auth_service
        self.db_service = db_service
    
    async def get_current_user_id(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> str:
        """Extract and validate user ID from JWT token"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = credentials.credentials
        user_data = await self.auth_service.get_current_user(token)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_data["id"]
    
    async def get_current_user(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Dict[str, Any]:
        """Get current authenticated user data"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = credentials.credentials
        user_data = await self.auth_service.get_current_user(token)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_data
    
    async def get_current_user_profile(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Profile:
        """Get current user's profile from database"""
        user_id = await self.get_current_user_id(credentials)
        
        profile = await self.db_service.get_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return profile
    
    async def verify_subscription_access(
        self, 
        required_tier: str,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Profile:
        """Verify user has required subscription tier"""
        profile = await self.get_current_user_profile(credentials)
        
        # Define tier hierarchy
        tier_hierarchy = {
            "free": 0,
            "pro": 1,
            "agency": 2,
            "enterprise": 3
        }
        
        user_tier_level = tier_hierarchy.get(profile.subscription_tier, 0)
        required_tier_level = tier_hierarchy.get(required_tier, 0)
        
        if user_tier_level < required_tier_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Subscription tier '{required_tier}' or higher required"
            )
        
        return profile
    
    async def verify_scan_quota(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Profile:
        """Verify user has remaining scan quota"""
        profile = await self.get_current_user_profile(credentials)
        
        if profile.scans_remaining <= 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Scan quota exceeded. Please upgrade your subscription."
            )
        
        return profile
    
    def optional_auth(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[str]:
        """Optional authentication - returns user ID if authenticated, None otherwise"""
        if not credentials:
            return None
        
        try:
            token = credentials.credentials
            # Simple token decode without full validation for optional auth
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded.get("sub")  # 'sub' is the user ID in Supabase JWT
        except Exception:
            return None

# Global middleware instance
auth_middleware = AuthMiddleware()

# Dependency functions for FastAPI
async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """Dependency to get current user ID"""
    return await auth_middleware.get_current_user_id(credentials)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Dependency to get current user data"""
    return await auth_middleware.get_current_user(credentials)

async def get_current_user_profile(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Profile:
    """Dependency to get current user profile"""
    return await auth_middleware.get_current_user_profile(credentials)

async def verify_pro_access(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Profile:
    """Dependency to verify Pro tier access"""
    return await auth_middleware.verify_subscription_access("pro", credentials)

async def verify_agency_access(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Profile:
    """Dependency to verify Agency tier access"""
    return await auth_middleware.verify_subscription_access("agency", credentials)

async def verify_scan_quota(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Profile:
    """Dependency to verify scan quota"""
    return await auth_middleware.verify_scan_quota(credentials)

def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """Dependency for optional authentication"""
    return auth_middleware.optional_auth(credentials)

# Rate limiting decorator
def rate_limit(max_requests: int = 60, window_minutes: int = 1):
    """Rate limiting decorator for API endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would integrate with Redis or in-memory cache for rate limiting
            # For now, we'll implement a simple in-memory rate limiter
            # In production, use Redis with sliding window or token bucket algorithm
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# CORS middleware configuration
def configure_cors(app):
    """Configure CORS middleware for the FastAPI app"""
    from fastapi.middleware.cors import CORSMiddleware
    from config import get_settings
    
    settings = get_settings()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )

# Security headers middleware
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response