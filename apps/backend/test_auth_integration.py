#!/usr/bin/env python3
"""
Simple integration test for authentication setup
"""
import os
import sys
from unittest.mock import patch, Mock

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all authentication modules can be imported"""
    try:
        from services.auth_service import auth_service
        from services.database_service import db_service
        from middleware.auth_middleware import auth_middleware
        from models.database import UserRegistration, UserLogin, Profile
        from database.supabase_client import get_supabase
        print("✓ All authentication modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_config_validation():
    """Test configuration validation"""
    try:
        # Mock environment variables for testing
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_KEY': 'test-key',
            'OPENAI_API_KEY': 'test-openai-key'
        }):
            from config import get_settings
            settings = get_settings()
            missing = settings.validate_required_settings()
            if not missing:
                print("✓ Configuration validation passed")
                return True
            else:
                print(f"✗ Missing required settings: {missing}")
                return False
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_models():
    """Test Pydantic models"""
    try:
        from models.database import UserRegistration, UserLogin, Profile, SubscriptionTier
        
        # Test UserRegistration model
        registration = UserRegistration(
            email="test@example.com",
            password="securepassword123",
            first_name="John",
            last_name="Doe"
        )
        assert registration.email == "test@example.com"
        
        # Test UserLogin model
        login = UserLogin(
            email="test@example.com",
            password="securepassword123"
        )
        assert login.email == "test@example.com"
        
        print("✓ Pydantic models validation passed")
        return True
    except Exception as e:
        print(f"✗ Model validation error: {e}")
        return False

def test_supabase_client():
    """Test Supabase client initialization"""
    try:
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_KEY': 'test-service-key'
        }):
            from database.supabase_client import SupabaseClient
            
            # Test singleton pattern
            client1 = SupabaseClient()
            client2 = SupabaseClient()
            assert client1 is client2
            
            print("✓ Supabase client initialization passed")
            return True
    except Exception as e:
        print(f"✗ Supabase client error: {e}")
        return False

def test_auth_service():
    """Test authentication service"""
    try:
        with patch('services.auth_service.get_supabase') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            from services.auth_service import AuthService
            auth_service = AuthService()
            
            # Test service initialization
            assert auth_service.supabase is not None
            
            print("✓ Authentication service initialization passed")
            return True
    except Exception as e:
        print(f"✗ Authentication service error: {e}")
        return False

def test_database_service():
    """Test database service"""
    try:
        with patch('services.database_service.get_supabase') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            from services.database_service import DatabaseService
            db_service = DatabaseService()
            
            # Test service initialization
            assert db_service.supabase is not None
            
            print("✓ Database service initialization passed")
            return True
    except Exception as e:
        print(f"✗ Database service error: {e}")
        return False

def test_cache_service():
    """Test cache service"""
    try:
        with patch('services.cache_service.get_supabase') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            from services.cache_service import CacheService
            cache_service = CacheService()
            
            # Test service initialization
            assert cache_service.supabase is not None
            
            # Test cache key generation
            cache_key = cache_service.generate_cache_key(
                "gpt-4", "test prompt", "test brand"
            )
            assert len(cache_key) == 32
            
            print("✓ Cache service initialization passed")
            return True
    except Exception as e:
        print(f"✗ Cache service error: {e}")
        return False

def main():
    """Run all tests"""
    print("Running Authentication Integration Tests...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config_validation,
        test_models,
        test_supabase_client,
        test_auth_service,
        test_database_service,
        test_cache_service
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All authentication integration tests passed!")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)