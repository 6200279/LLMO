"""
Supabase Authentication Service
Handles user registration, login, email verification, and password reset
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, status

from database.supabase_client import get_supabase
from models.database import (
    UserRegistration, UserLogin, AuthResponse, TokenRefresh,
    Profile, ProfileCreate
)
from services.database_service import db_service
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class AuthService:
    """Service class for authentication operations using Supabase Auth"""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    async def register_user(self, registration_data: UserRegistration) -> AuthResponse:
        """Register a new user with Supabase Auth"""
        try:
            # Register user with Supabase Auth
            auth_response = self.supabase.auth.sign_up({
                "email": registration_data.email,
                "password": registration_data.password,
                "options": {
                    "data": {
                        "first_name": registration_data.first_name or "",
                        "last_name": registration_data.last_name or "",
                        "company_name": registration_data.company_name or ""
                    }
                }
            })
            
            if auth_response.user is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User registration failed"
                )
            
            # Create user profile (this will be handled by the database trigger)
            # But we can also ensure it exists
            user_id = auth_response.user.id
            
            try:
                # Check if profile already exists (created by trigger)
                existing_profile = await db_service.get_profile(user_id)
                if not existing_profile:
                    # Create profile if trigger didn't work
                    profile_data = ProfileCreate(
                        first_name=registration_data.first_name,
                        last_name=registration_data.last_name,
                        company_name=registration_data.company_name
                    )
                    await db_service.create_profile(user_id, profile_data)
            except Exception as profile_error:
                logger.warning(f"Profile creation warning for user {user_id}: {profile_error}")
                # Don't fail registration if profile creation fails
            
            return AuthResponse(
                access_token=auth_response.session.access_token if auth_response.session else "",
                refresh_token=auth_response.session.refresh_token if auth_response.session else "",
                user=self._format_user_data(auth_response.user),
                expires_in=auth_response.session.expires_in if auth_response.session else 3600
            )
            
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            if "already registered" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {str(e)}"
            )
    
    async def authenticate_user(self, login_data: UserLogin) -> AuthResponse:
        """Authenticate user with email and password"""
        try:
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": login_data.email,
                "password": login_data.password
            })
            
            if auth_response.user is None or auth_response.session is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            return AuthResponse(
                access_token=auth_response.session.access_token,
                refresh_token=auth_response.session.refresh_token,
                user=self._format_user_data(auth_response.user),
                expires_in=auth_response.session.expires_in
            )
            
        except Exception as e:
            logger.error(f"User authentication failed: {e}")
            if "invalid" in str(e).lower() or "credentials" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Authentication failed: {str(e)}"
            )
    
    async def refresh_token(self, token_data: TokenRefresh) -> AuthResponse:
        """Refresh access token using refresh token"""
        try:
            auth_response = self.supabase.auth.refresh_session(token_data.refresh_token)
            
            if auth_response.session is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            return AuthResponse(
                access_token=auth_response.session.access_token,
                refresh_token=auth_response.session.refresh_token,
                user=self._format_user_data(auth_response.user) if auth_response.user else {},
                expires_in=auth_response.session.expires_in
            )
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed"
            )
    
    async def verify_email(self, token: str) -> bool:
        """Verify user email with verification token"""
        try:
            # Supabase handles email verification automatically
            # This method can be used for custom verification logic if needed
            auth_response = self.supabase.auth.verify_otp({
                "token": token,
                "type": "email"
            })
            
            return auth_response.user is not None
            
        except Exception as e:
            logger.error(f"Email verification failed: {e}")
            return False
    
    async def reset_password(self, email: str) -> bool:
        """Send password reset email"""
        try:
            self.supabase.auth.reset_password_email(email)
            return True
            
        except Exception as e:
            logger.error(f"Password reset failed for {email}: {e}")
            return False
    
    async def update_password(self, access_token: str, new_password: str) -> bool:
        """Update user password"""
        try:
            # Set the session with the access token
            self.supabase.auth.set_session(access_token, "")
            
            auth_response = self.supabase.auth.update_user({
                "password": new_password
            })
            
            return auth_response.user is not None
            
        except Exception as e:
            logger.error(f"Password update failed: {e}")
            return False
    
    async def get_current_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get current user from access token"""
        try:
            # Verify and decode the JWT token
            user_data = self._decode_jwt_token(access_token)
            if not user_data:
                return None
            
            # Get user from Supabase
            self.supabase.auth.set_session(access_token, "")
            auth_response = self.supabase.auth.get_user()
            
            if auth_response.user:
                return self._format_user_data(auth_response.user)
            
            return None
            
        except Exception as e:
            logger.error(f"Get current user failed: {e}")
            return None
    
    async def sign_out(self, access_token: str) -> bool:
        """Sign out user and invalidate session"""
        try:
            self.supabase.auth.set_session(access_token, "")
            self.supabase.auth.sign_out()
            return True
            
        except Exception as e:
            logger.error(f"Sign out failed: {e}")
            return False
    
    async def update_user_metadata(self, access_token: str, metadata: Dict[str, Any]) -> bool:
        """Update user metadata"""
        try:
            self.supabase.auth.set_session(access_token, "")
            
            auth_response = self.supabase.auth.update_user({
                "data": metadata
            })
            
            return auth_response.user is not None
            
        except Exception as e:
            logger.error(f"User metadata update failed: {e}")
            return False
    
    def _format_user_data(self, user) -> Dict[str, Any]:
        """Format Supabase user data for API response"""
        if not user:
            return {}
        
        return {
            "id": user.id,
            "email": user.email,
            "email_confirmed_at": user.email_confirmed_at,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "user_metadata": user.user_metadata or {},
            "app_metadata": user.app_metadata or {}
        }
    
    def _decode_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode JWT token without verification (for user ID extraction)"""
        try:
            # Decode without verification to extract user info
            # Supabase will handle token verification
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded
        except Exception as e:
            logger.error(f"JWT decode failed: {e}")
            return None
    
    def _is_token_expired(self, token: str) -> bool:
        """Check if JWT token is expired"""
        try:
            decoded = self._decode_jwt_token(token)
            if not decoded or 'exp' not in decoded:
                return True
            
            exp_timestamp = decoded['exp']
            current_timestamp = datetime.now().timestamp()
            
            return current_timestamp >= exp_timestamp
            
        except Exception:
            return True

# Global auth service instance
auth_service = AuthService()