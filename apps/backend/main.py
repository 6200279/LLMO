from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import logging

# Import services and models
from services.auth_service import auth_service
from services.database_service import db_service
from middleware.auth_middleware import (
    get_current_user_id, get_current_user_profile, 
    verify_scan_quota, add_security_headers
)
from models.database import (
    UserRegistration, UserLogin, AuthResponse, TokenRefresh,
    Profile, ProfileUpdate, ScanRequest, PromptSimulationRequest, 
    VisibilityAuditRequest, ErrorResponse
)
from services.llm_provider import OpenAIProvider, AnthropicProvider
from config import get_settings
from database.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Validate required settings on startup
missing_settings = settings.validate_required_settings()
if missing_settings:
    logger.error(f"Missing required settings: {missing_settings}")
    raise ValueError(f"Missing required environment variables: {', '.join(missing_settings)}")

app = FastAPI(
    title="LLMO API", 
    description="LLM Optimization Engine API", 
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add security headers middleware
app.middleware("http")(add_security_headers)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to request state for tracking"""
    import uuid
    
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Add request ID to response headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Health check endpoints
@app.get("/")
async def root():
    return {"message": "LLMO API is running", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    """Comprehensive health check including database connectivity"""
    try:
        # Check Supabase connectivity
        supabase_client = get_supabase_client()
        db_healthy = await supabase_client.health_check()
        
        return {
            "status": "healthy" if db_healthy else "degraded",
            "service": "LLMO API",
            "version": "1.0.0",
            "database": "connected" if db_healthy else "disconnected",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "LLMO API",
            "error": str(e)
        }

# Authentication endpoints
@app.post("/api/auth/register", response_model=AuthResponse)
async def register(registration_data: UserRegistration):
    """Register a new user"""
    try:
        return await auth_service.register_user(registration_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(login_data: UserLogin):
    """Authenticate user and return tokens"""
    try:
        return await auth_service.authenticate_user(login_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@app.post("/api/auth/refresh", response_model=AuthResponse)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token"""
    try:
        return await auth_service.refresh_token(token_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@app.post("/api/auth/logout")
async def logout(current_user_id: str = Depends(get_current_user_id)):
    """Logout user and invalidate session"""
    try:
        # Note: Supabase handles session invalidation automatically
        # This endpoint is for client-side cleanup
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@app.post("/api/auth/reset-password")
async def reset_password(email_data: Dict[str, str]):
    """Send password reset email"""
    try:
        email = email_data.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        success = await auth_service.reset_password(email)
        if success:
            return {"message": "Password reset email sent"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset failed"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

@app.post("/api/auth/verify-email")
async def verify_email(token_data: Dict[str, str]):
    """Verify user email with token"""
    try:
        token = token_data.get("token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token is required"
            )
        
        success = await auth_service.verify_email(token)
        if success:
            return {"message": "Email verified successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email verification failed"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )

# User profile endpoints
@app.get("/api/user/profile", response_model=Profile)
async def get_profile(current_profile: Profile = Depends(get_current_user_profile)):
    """Get current user profile"""
    return current_profile

@app.put("/api/user/profile", response_model=Profile)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update user profile"""
    try:
        return await db_service.update_profile(current_user_id, profile_data)
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

# Protected scan endpoints (require authentication and quota)
@app.post("/api/scan/visibility")
async def scan_visibility(
    request: ScanRequest,
    current_profile: Profile = Depends(verify_scan_quota)
):
    """LLM Visibility Scanner endpoint"""
    try:
        # Import here to avoid circular imports
        from services.llm_service import LLMService
        from services.cache_service import CacheService
        
        # Initialize services
        llm_service = LLMService()
        cache_service = CacheService()
        
        # Create cache key
        cache_key = f"visibility_scan:{request.brand_name}:{request.domain}"
        
        # Check cache first
        cached_result = await cache_service.get_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for visibility scan: {request.brand_name}")
            
            # Update scan usage
            await db_service.update_scan_usage(current_profile.id)
            
            # Return cached result with updated scans_remaining
            cached_result["scans_remaining"] = current_profile.scans_remaining - 1
            cached_result["cached"] = True
            return cached_result
        
        # Create a new scan record
        scan_data = {
            "user_id": current_profile.id,
            "brand_name": request.brand_name,
            "domain": request.domain,
            "scan_type": "visibility",
            "status": "processing"
        }
        scan_id = await db_service.create_scan(scan_data)
        
        # Update scan usage
        await db_service.update_scan_usage(current_profile.id)
        
        # Query each available provider and model
        results = {}
        providers = llm_service.get_available_providers()
        
        for provider_name in providers:
            provider = llm_service.get_provider(provider_name)
            for model in provider.get_available_models()[:1]:  # Just use first model for each provider in MVP
                try:
                    result = await llm_service.query_brand_visibility(
                        request.brand_name,
                        request.domain,
                        request.keywords,
                        model=model,
                        provider_name=provider_name
                    )
                    results[f"{provider_name}:{model}"] = result
                except Exception as e:
                    logger.error(f"Error querying {provider_name} with {model}: {e}")
                    results[f"{provider_name}:{model}"] = {
                        "error": str(e),
                        "status": "failed"
                    }
        
        # Calculate overall visibility score (average of all model scores)
        valid_scores = [
            r["visibility_score"] for r in results.values() 
            if isinstance(r, dict) and "visibility_score" in r
        ]
        
        overall_score = int(sum(valid_scores) / max(1, len(valid_scores)))
        
        # Prepare response
        response = {
            "scan_id": scan_id,
            "brand_name": request.brand_name,
            "domain": request.domain,
            "score": overall_score,
            "model_results": results,
            "status": "completed",
            "scans_remaining": current_profile.scans_remaining - 1
        }
        
        # Cache the result
        await cache_service.set_cache(cache_key, response, ttl_hours=settings.CACHE_TTL_HOURS)
        
        # Update scan record
        await db_service.update_scan(scan_id, {
            "status": "completed",
            "progress": 100,
            "completed_at": "now()",
            "metadata": {"score": overall_score}
        })
        
        return response
    except Exception as e:
        logger.error(f"Visibility scan error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Visibility scan failed: {str(e)}"
        )

@app.post("/api/simulate/prompts")
async def simulate_prompts(
    request: PromptSimulationRequest,
    current_profile: Profile = Depends(verify_scan_quota)
):
    """Prompt Simulation Engine endpoint"""
    try:
        # Import here to avoid circular imports
        from services.llm_service import LLMService
        from services.cache_service import CacheService
        
        # Initialize services
        llm_service = LLMService()
        cache_service = CacheService()
        
        # Create cache key based on brand name and prompts
        prompt_hash = "-".join([p[:20] for p in request.prompts[:3]])
        cache_key = f"prompt_sim:{request.brand_name}:{prompt_hash}"
        
        # Check cache first
        cached_result = await cache_service.get_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for prompt simulation: {request.brand_name}")
            
            # Update scan usage
            await db_service.update_scan_usage(current_profile.id)
            
            # Return cached result with updated scans_remaining
            cached_result["scans_remaining"] = current_profile.scans_remaining - 1
            cached_result["cached"] = True
            return cached_result
        
        # Create a new scan record
        scan_data = {
            "user_id": current_profile.id,
            "brand_name": request.brand_name,
            "scan_type": "simulation",
            "status": "processing"
        }
        scan_id = await db_service.create_scan(scan_data)
        
        # Update scan usage
        await db_service.update_scan_usage(current_profile.id)
        
        # Combine standard and custom prompts
        all_prompts = request.prompts + request.custom_prompts
        
        # Simulate prompts
        results = await llm_service.simulate_brand_prompts(
            request.brand_name,
            all_prompts,
            provider_name="openai",  # Default to OpenAI for MVP
            model="gpt-3.5-turbo"    # Default to GPT-3.5 for MVP
        )
        
        # Calculate mention statistics
        mention_count = sum(1 for r in results if r["brand_mentioned"])
        mention_percentage = (mention_count / len(results)) * 100 if results else 0
        
        # Calculate average sentiment for mentions
        sentiment_scores = [r["sentiment_score"] for r in results if r["brand_mentioned"]]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        # Prepare response
        response = {
            "scan_id": scan_id,
            "brand_name": request.brand_name,
            "results": results,
            "stats": {
                "total_prompts": len(results),
                "mention_count": mention_count,
                "mention_percentage": mention_percentage,
                "average_sentiment": avg_sentiment
            },
            "status": "completed",
            "scans_remaining": current_profile.scans_remaining - 1
        }
        
        # Cache the result
        await cache_service.set_cache(cache_key, response, ttl_hours=settings.CACHE_TTL_HOURS)
        
        # Update scan record
        await db_service.update_scan(scan_id, {
            "status": "completed",
            "progress": 100,
            "completed_at": "now()",
            "metadata": {
                "mention_count": mention_count,
                "mention_percentage": mention_percentage
            }
        })
        
        return response
    except Exception as e:
        logger.error(f"Prompt simulation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prompt simulation failed: {str(e)}"
        )

@app.post("/api/audit/visibility")
async def audit_visibility(
    request: VisibilityAuditRequest,
    current_profile: Profile = Depends(verify_scan_quota)
):
    """
    Website Visibility Audit endpoint - Analyzes website for LLM-friendly content and structure
    
    Features:
    - Domain validation with comprehensive error handling
    - 6-hour result caching for performance optimization
    - Audit history tracking and comparison
    - Detailed error reporting for website access issues
    """
    try:
        # Import here to avoid circular imports
        from services.web_scraper import WebScraperService
        from services.cache_service import CacheService
        
        # Initialize services
        web_scraper = WebScraperService()
        cache_service = CacheService()
        
        # Enhanced domain validation
        domain = request.domain.strip()
        
        # Normalize domain format
        if not domain.startswith(('http://', 'https://')):
            domain = f"https://{domain}"
        
        # Additional domain validation
        from urllib.parse import urlparse
        try:
            parsed = urlparse(domain)
            if not parsed.netloc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid domain format. Please provide a valid domain (e.g., example.com or https://example.com)"
                )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid domain format. Please provide a valid domain (e.g., example.com or https://example.com)"
            )
        
        # Create cache key for 6-hour TTL
        cache_key = f"audit:{domain}"
        
        # Check cache first (6-hour TTL)
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for website audit: {domain}")
            
            # Update scan usage
            await db_service.update_scan_usage(current_profile.id)
            
            # Return cached result with updated scans_remaining
            cached_result["scans_remaining"] = current_profile.scans_remaining - 1
            cached_result["cached"] = True
            cached_result["cache_timestamp"] = cached_result.get("timestamp")
            return cached_result
        
        # Create a new scan record for tracking
        scan_data = ScanCreate(
            brand_id=None,  # Audit scans don't require brand
            scan_type=ScanType.AUDIT,
            metadata={"domain": domain}
        )
        scan_id = await db_service.create_scan(current_profile.id, scan_data)
        
        # Update scan usage
        await db_service.update_scan_usage(current_profile.id)
        
        # Perform website audit with comprehensive error handling
        try:
            audit_results = await web_scraper.audit_website(domain)
        except Exception as audit_error:
            # Handle specific audit errors
            error_message = str(audit_error)
            error_type = "audit_error"
            
            # Classify error types for better user experience
            if "Connection" in error_message or "connection" in error_message.lower():
                error_type = "connection_error"
                user_message = f"Unable to connect to {domain}. Please check if the website is accessible and try again."
            elif "Timeout" in error_message or "timeout" in error_message.lower():
                error_type = "timeout_error"
                user_message = f"Request to {domain} timed out. The website may be slow or temporarily unavailable."
            elif "HTTP" in error_message and ("404" in error_message or "403" in error_message or "500" in error_message):
                error_type = "http_error"
                user_message = f"Website returned an error. Please check if {domain} is the correct URL."
            elif "SSL" in error_message or "certificate" in error_message.lower():
                error_type = "ssl_error"
                user_message = f"SSL certificate issue with {domain}. The website may have security configuration problems."
            else:
                error_type = "unknown_error"
                user_message = f"Unable to analyze {domain}. Please try again or contact support if the issue persists."
            
            # Update scan record with error
            await db_service.update_scan(scan_id.id, ScanUpdate(
                status=ScanStatus.FAILED,
                progress=100,
                error_message=error_message
            ))
            
            # Return error response with helpful information
            error_response = {
                "scan_id": scan_id.id,
                "domain": domain,
                "status": "failed",
                "error": user_message,
                "error_type": error_type,
                "error_details": error_message,
                "overall_score": 0,
                "component_scores": {
                    "schema_score": 0,
                    "meta_score": 0,
                    "content_score": 0,
                    "technical_score": 0
                },
                "recommendations": [{
                    "priority": "high",
                    "category": "technical",
                    "issue": f"Website access failed: {error_type.replace('_', ' ').title()}",
                    "recommendation": user_message,
                    "implementation": "Resolve the website access issue before running another audit"
                }],
                "scans_remaining": current_profile.scans_remaining - 1,
                "timestamp": datetime.now().isoformat()
            }
            
            return error_response
        
        # Extract scores and data from successful audit
        overall_score = audit_results.get("llm_friendly_score", 0)
        component_scores = audit_results.get("component_scores", {})
        recommendations = audit_results.get("recommendations", [])
        
        # Prepare comprehensive response
        response = {
            "scan_id": scan_id.id,
            "domain": domain,
            "overall_score": overall_score,
            "component_scores": component_scores,
            "recommendations": recommendations,
            "audit_data": {
                "schema_org": audit_results.get("schema_org", {}),
                "meta_tags": audit_results.get("meta_tags", {}),
                "content_structure": audit_results.get("content_structure", {}),
                "technical_factors": audit_results.get("technical_factors", {})
            },
            "status": "completed" if "error" not in audit_results else "failed",
            "scans_remaining": current_profile.scans_remaining - 1,
            "timestamp": audit_results.get("timestamp", datetime.now().isoformat()),
            "cached": False
        }
        
        # Add error information if present in audit results
        if "error" in audit_results:
            response["error"] = audit_results["error"]
            response["error_type"] = audit_results.get("error_type", "unknown_error")
        
        # Cache the result with 6-hour TTL
        await cache_service.set(
            cache_key, 
            response, 
            "website_audit",
            f"Audit for {domain}",
            6  # 6-hour TTL as specified in requirements
        )
        
        # Update scan record with completion status
        scan_status = ScanStatus.COMPLETED if "error" not in audit_results else ScanStatus.FAILED
        await db_service.update_scan(scan_id.id, ScanUpdate(
            status=scan_status,
            progress=100,
            metadata={
                "overall_score": overall_score,
                "schema_score": component_scores.get("schema_score", 0),
                "meta_score": component_scores.get("meta_score", 0),
                "content_score": component_scores.get("content_score", 0),
                "technical_score": component_scores.get("technical_score", 0),
                "domain": domain
            }
        ))
        
        # Store audit result in database for history tracking and comparison
        audit_result_data = AuditResultCreate(
            scan_id=scan_id.id,
            overall_score=overall_score,
            schema_score=component_scores.get("schema_score", 0),
            meta_score=component_scores.get("meta_score", 0),
            content_score=component_scores.get("content_score", 0),
            technical_score=component_scores.get("technical_score", 0),
            recommendations=recommendations,
            technical_details=audit_results.get("technical_factors", {}),
            audit_data={
                "schema_org": audit_results.get("schema_org", {}),
                "meta_tags": audit_results.get("meta_tags", {}),
                "content_structure": audit_results.get("content_structure", {}),
                "raw_audit_data": audit_results  # Store complete audit data for future analysis
            }
        )
        
        await db_service.create_audit_result(audit_result_data)
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors)
        raise
    except Exception as e:
        logger.error(f"Visibility audit error for domain {request.domain}: {e}")
        
        # Provide user-friendly error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Website audit failed due to an internal error. Please try again or contact support if the issue persists."
        )

@app.get("/api/audit/history")
async def get_audit_history(
    domain: Optional[str] = None,
    limit: int = 50,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get audit history for the current user
    
    Features:
    - Filter by domain (optional)
    - Paginated results with configurable limit
    - Includes audit scores and timestamps for comparison
    """
    try:
        # Get user's audit scans
        scans = await db_service.get_user_scans(current_user_id, limit)
        
        # Filter for audit scans only
        audit_scans = [scan for scan in scans if scan.scan_type == ScanType.AUDIT]
        
        # Further filter by domain if specified
        if domain:
            # Normalize domain for comparison
            if not domain.startswith(('http://', 'https://')):
                domain = f"https://{domain}"
            
            audit_scans = [
                scan for scan in audit_scans 
                if scan.metadata and scan.metadata.get("domain") == domain
            ]
        
        # Get audit results for each scan
        audit_history = []
        for scan in audit_scans:
            try:
                audit_result = await db_service.get_audit_result(scan.id)
                
                history_item = {
                    "scan_id": scan.id,
                    "domain": scan.metadata.get("domain") if scan.metadata else "Unknown",
                    "overall_score": audit_result.overall_score if audit_result else 0,
                    "component_scores": {
                        "schema_score": audit_result.schema_score if audit_result else 0,
                        "meta_score": audit_result.meta_score if audit_result else 0,
                        "content_score": audit_result.content_score if audit_result else 0,
                        "technical_score": audit_result.technical_score if audit_result else 0
                    } if audit_result else {},
                    "status": scan.status.value,
                    "created_at": scan.started_at.isoformat(),
                    "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                    "error_message": scan.error_message
                }
                
                audit_history.append(history_item)
            except Exception as e:
                logger.error(f"Error getting audit result for scan {scan.id}: {e}")
                # Continue with next scan
        
        # Sort by created_at (newest first)
        audit_history.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "audit_history": audit_history,
            "total_count": len(audit_history),
            "filtered_domain": domain if domain else None,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting audit history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit history"
        )

@app.get("/api/audit/compare/{scan_id_1}/{scan_id_2}")
async def compare_audits(
    scan_id_1: str,
    scan_id_2: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Compare two website audits to track improvements
    
    Features:
    - Score comparison with change percentage
    - Recommendation analysis
    - Improvement summary
    """
    try:
        # Get both scans and verify ownership
        scan_1 = await db_service.get_scan(scan_id_1, current_user_id)
        if not scan_1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan {scan_id_1} not found"
            )
        
        scan_2 = await db_service.get_scan(scan_id_2, current_user_id)
        if not scan_2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan {scan_id_2} not found"
            )
        
        # Verify both are audit scans
        if scan_1.scan_type != ScanType.AUDIT or scan_2.scan_type != ScanType.AUDIT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both scans must be website audits"
            )
        
        # Get audit results
        audit_1 = await db_service.get_audit_result(scan_id_1)
        audit_2 = await db_service.get_audit_result(scan_id_2)
        
        if not audit_1 or not audit_2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit results not found for one or both scans"
            )
        
        # Calculate score changes
        score_changes = {
            "overall_score": {
                "before": audit_1.overall_score,
                "after": audit_2.overall_score,
                "change": audit_2.overall_score - audit_1.overall_score,
                "change_percentage": calculate_percentage_change(audit_1.overall_score, audit_2.overall_score)
            },
            "schema_score": {
                "before": audit_1.schema_score,
                "after": audit_2.schema_score,
                "change": audit_2.schema_score - audit_1.schema_score,
                "change_percentage": calculate_percentage_change(audit_1.schema_score, audit_2.schema_score)
            },
            "meta_score": {
                "before": audit_1.meta_score,
                "after": audit_2.meta_score,
                "change": audit_2.meta_score - audit_1.meta_score,
                "change_percentage": calculate_percentage_change(audit_1.meta_score, audit_2.meta_score)
            },
            "content_score": {
                "before": audit_1.content_score,
                "after": audit_2.content_score,
                "change": audit_2.content_score - audit_1.content_score,
                "change_percentage": calculate_percentage_change(audit_1.content_score, audit_2.content_score)
            },
            "technical_score": {
                "before": audit_1.technical_score,
                "after": audit_2.technical_score,
                "change": audit_2.technical_score - audit_1.technical_score,
                "change_percentage": calculate_percentage_change(audit_1.technical_score, audit_2.technical_score)
            }
        }
        
        # Analyze recommendations
        recommendations_1 = audit_1.recommendations
        recommendations_2 = audit_2.recommendations
        
        # Count recommendations by priority
        priority_counts_1 = count_recommendations_by_priority(recommendations_1)
        priority_counts_2 = count_recommendations_by_priority(recommendations_2)
        
        # Count recommendations by category
        category_counts_1 = count_recommendations_by_category(recommendations_1)
        category_counts_2 = count_recommendations_by_category(recommendations_2)
        
        # Analyze resolved issues
        resolved_issues = analyze_resolved_issues(recommendations_1, recommendations_2)
        
        # Create recommendation analysis
        recommendation_analysis = {
            "priority_counts": {
                "before": priority_counts_1,
                "after": priority_counts_2,
                "change": {
                    "high": priority_counts_2.get("high", 0) - priority_counts_1.get("high", 0),
                    "medium": priority_counts_2.get("medium", 0) - priority_counts_1.get("medium", 0),
                    "low": priority_counts_2.get("low", 0) - priority_counts_1.get("low", 0)
                }
            },
            "category_counts": {
                "before": category_counts_1,
                "after": category_counts_2
            },
            "resolved_issues": resolved_issues,
            "total_recommendations": {
                "before": len(recommendations_1),
                "after": len(recommendations_2),
                "change": len(recommendations_2) - len(recommendations_1)
            }
        }
        
        # Generate summary
        overall_improvement = audit_2.overall_score > audit_1.overall_score
        score_improvement = score_changes["overall_score"]["change"]
        recommendation_improvement = recommendation_analysis["total_recommendations"]["change"] < 0
        
        summary = {
            "overall_improvement": overall_improvement,
            "score_improvement": score_improvement,
            "recommendation_improvement": recommendation_improvement,
            "summary_text": generate_comparison_summary(
                score_changes, 
                recommendation_analysis,
                scan_1.metadata.get("domain") if scan_1.metadata else "Unknown"
            )
        }
        
        # Prepare response
        return {
            "comparison": {
                "scan_1": {
                    "scan_id": scan_id_1,
                    "domain": scan_1.metadata.get("domain") if scan_1.metadata else "Unknown",
                    "created_at": scan_1.started_at.isoformat(),
                    "overall_score": audit_1.overall_score
                },
                "scan_2": {
                    "scan_id": scan_id_2,
                    "domain": scan_2.metadata.get("domain") if scan_2.metadata else "Unknown",
                    "created_at": scan_2.started_at.isoformat(),
                    "overall_score": audit_2.overall_score
                },
                "score_changes": score_changes,
                "recommendation_analysis": recommendation_analysis,
                "summary": summary
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing audits {scan_id_1} and {scan_id_2}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare audit results"
        )

@app.get("/api/audit/domain-history/{domain}")
async def get_domain_audit_history(
    domain: str,
    limit: int = 10,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get audit history for a specific domain with trend analysis
    
    Features:
    - Historical score tracking
    - Trend analysis
    - Improvement recommendations
    """
    try:
        # Normalize domain
        if not domain.startswith(('http://', 'https://')):
            domain = f"https://{domain}"
        
        # Get user's audit scans
        scans = await db_service.get_user_scans(current_user_id, 50)  # Get more to filter
        
        # Filter for audit scans for this domain
        domain_scans = [
            scan for scan in scans 
            if scan.scan_type == ScanType.AUDIT and 
            scan.metadata and 
            scan.metadata.get("domain") == domain
        ]
        
        # Sort by date (newest first)
        domain_scans.sort(key=lambda x: x.started_at, reverse=True)
        
        # Limit results
        domain_scans = domain_scans[:limit]
        
        # Get audit results for each scan
        audit_history = []
        scores = []
        
        for scan in domain_scans:
            try:
                audit_result = await db_service.get_audit_result(scan.id)
                
                if audit_result:
                    history_item = {
                        "scan_id": scan.id,
                        "overall_score": audit_result.overall_score,
                        "component_scores": {
                            "schema_score": audit_result.schema_score,
                            "meta_score": audit_result.meta_score,
                            "content_score": audit_result.content_score,
                            "technical_score": audit_result.technical_score
                        },
                        "created_at": scan.started_at.isoformat(),
                        "recommendations_count": len(audit_result.recommendations)
                    }
                    
                    audit_history.append(history_item)
                    scores.append(audit_result.overall_score)
            except Exception as e:
                logger.error(f"Error getting audit result for scan {scan.id}: {e}")
                # Continue with next scan
        
        # Generate trend analysis
        trend_analysis = {
            "total_audits": len(audit_history),
            "score_trend": "no_data"
        }
        
        if len(scores) >= 2:
            # Calculate trend
            first_score = scores[-1]  # Oldest
            last_score = scores[0]    # Newest
            
            if last_score > first_score:
                trend_analysis["score_trend"] = "improving"
            elif last_score < first_score:
                trend_analysis["score_trend"] = "declining"
            else:
                trend_analysis["score_trend"] = "stable"
                
            # Add statistics
            trend_analysis["average_score"] = sum(scores) / len(scores)
            trend_analysis["best_score"] = max(scores)
            trend_analysis["worst_score"] = min(scores)
            trend_analysis["latest_score"] = scores[0]
            trend_analysis["first_score"] = scores[-1]
            trend_analysis["score_change"] = last_score - first_score
            trend_analysis["score_change_percentage"] = calculate_percentage_change(first_score, last_score)
        
        # Get latest recommendations if available
        recommendations = []
        if audit_history:
            latest_scan_id = audit_history[0]["scan_id"]
            latest_audit = await db_service.get_audit_result(latest_scan_id)
            if latest_audit:
                recommendations = latest_audit.recommendations
        
        return {
            "domain": domain,
            "audit_history": audit_history,
            "trend_analysis": trend_analysis,
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Error getting domain audit history for {domain}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve domain audit history"
        )

# Helper functions for audit comparison
def calculate_percentage_change(before: int, after: int) -> float:
    """Calculate percentage change between two values"""
    if before == 0:
        return 100.0 if after > 0 else 0.0
    return ((after - before) / before) * 100

def count_recommendations_by_priority(recommendations: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count recommendations by priority"""
    counts = {"high": 0, "medium": 0, "low": 0}
    
    for rec in recommendations:
        priority = rec.get("priority", "").lower()
        if priority in counts:
            counts[priority] += 1
    
    return counts

def count_recommendations_by_category(recommendations: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count recommendations by category"""
    counts = {}
    
    for rec in recommendations:
        category = rec.get("category", "").lower()
        if category:
            counts[category] = counts.get(category, 0) + 1
    
    return counts

def analyze_resolved_issues(before_recs: List[Dict[str, Any]], after_recs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze which issues were resolved between audits"""
    # Extract issues from before recommendations
    before_issues = set()
    for rec in before_recs:
        issue = rec.get("issue", "")
        if issue:
            before_issues.add(issue.lower())
    
    # Extract issues from after recommendations
    after_issues = set()
    for rec in after_recs:
        issue = rec.get("issue", "")
        if issue:
            after_issues.add(issue.lower())
    
    # Find resolved issues
    resolved_issues = before_issues - after_issues
    new_issues = after_issues - before_issues
    
    return {
        "resolved_count": len(resolved_issues),
        "resolved_issues": list(resolved_issues),
        "new_issues_count": len(new_issues),
        "new_issues": list(new_issues)
    }

def generate_comparison_summary(
    score_changes: Dict[str, Any], 
    recommendation_analysis: Dict[str, Any],
    domain: str
) -> str:
    """Generate a human-readable summary of the comparison"""
    overall_change = score_changes["overall_score"]["change"]
    
    if overall_change > 0:
        summary = f"The website {domain} has improved its LLM-friendly score by {overall_change} points "
        summary += f"({score_changes['overall_score']['change_percentage']:.1f}%). "
    elif overall_change < 0:
        summary = f"The website {domain} has decreased its LLM-friendly score by {abs(overall_change)} points "
        summary += f"({abs(score_changes['overall_score']['change_percentage']):.1f}%). "
    else:
        summary = f"The website {domain} has maintained the same LLM-friendly score. "
    
    # Add component score changes
    improved_components = []
    declined_components = []
    
    for component in ["schema_score", "meta_score", "content_score", "technical_score"]:
        change = score_changes[component]["change"]
        if change > 5:  # Only mention significant changes
            improved_components.append(component.replace("_score", ""))
        elif change < -5:
            declined_components.append(component.replace("_score", ""))
    
    if improved_components:
        summary += f"Notable improvements in {', '.join(improved_components)}. "
    
    if declined_components:
        summary += f"Declines observed in {', '.join(declined_components)}. "
    
    # Add recommendation changes
    resolved_count = recommendation_analysis["resolved_issues"]["resolved_count"]
    new_issues_count = recommendation_analysis["resolved_issues"]["new_issues_count"]
    
    if resolved_count > 0:
        summary += f"{resolved_count} issues have been resolved. "
    
    if new_issues_count > 0:
        summary += f"{new_issues_count} new issues were identified. "
    
    # Add high priority recommendations
    high_priority_change = recommendation_analysis["priority_counts"]["change"]["high"]
    if high_priority_change < 0:
        summary += f"High priority issues reduced by {abs(high_priority_change)}. "
    elif high_priority_change > 0:
        summary += f"High priority issues increased by {high_priority_change}. "
    
    return summary

@app.get("/api/llm/providers")
async def get_llm_providers(current_user_id: str = Depends(get_current_user_id)):
    """Get available LLM providers and models"""
    try:
        # Import here to avoid circular imports
        from services.llm_service import LLMService
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Get available providers and models
        providers = llm_service.get_available_providers()
        models = llm_service.get_available_models()
        
        return {
            "providers": providers,
            "models": models,
            "default_provider": "openai",
            "default_model": "gpt-3.5-turbo"
        }
    except Exception as e:
        logger.error(f"Error getting LLM providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get LLM providers"
        )

@app.post("/api/llm/standard-prompts")
async def get_standard_prompts(
    request: Dict[str, Any],
    current_user_id: str = Depends(get_current_user_id)
):
    """Get standardized prompts for a brand and industry"""
    try:
        # Import here to avoid circular imports
        from services.llm_service import LLMService
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Extract parameters
        brand_name = request.get("brand_name")
        industry = request.get("industry")
        product_category = request.get("product_category")
        competitors = request.get("competitors", [])
        
        if not brand_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Brand name is required"
            )
        
        # Get standardized prompts
        prompts = await llm_service.get_standardized_prompts(
            brand_name,
            industry,
            product_category,
            competitors
        )
        
        return {
            "brand_name": brand_name,
            "industry": industry,
            "product_category": product_category,
            "prompts": prompts,
            "prompt_count": len(prompts)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting standard prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get standard prompts"
        )

@app.get("/api/audit/history")
async def get_audit_history(
    domain: Optional[str] = None,
    limit: int = 50,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get audit history for the current user
    
    Features:
    - Filter by domain (optional)
    - Paginated results with configurable limit
    - Includes audit scores and timestamps for comparison
    """
    try:
        # Get user's audit scans
        scans = await db_service.get_user_scans(current_user_id, limit)
        
        # Filter for audit scans only
        audit_scans = [scan for scan in scans if scan.scan_type == ScanType.AUDIT]
        
        # Further filter by domain if specified
        if domain:
            # Normalize domain for comparison
            if not domain.startswith(('http://', 'https://')):
                domain = f"https://{domain}"
            
            audit_scans = [
                scan for scan in audit_scans 
                if scan.metadata and scan.metadata.get("domain") == domain
            ]
        
        # Get audit results for each scan
        audit_history = []
        for scan in audit_scans:
            try:
                audit_result = await db_service.get_audit_result(scan.id)
                
                history_item = {
                    "scan_id": scan.id,
                    "domain": scan.metadata.get("domain") if scan.metadata else "Unknown",
                    "overall_score": audit_result.overall_score if audit_result else 0,
                    "component_scores": {
                        "schema_score": audit_result.schema_score if audit_result else 0,
                        "meta_score": audit_result.meta_score if audit_result else 0,
                        "content_score": audit_result.content_score if audit_result else 0,
                        "technical_score": audit_result.technical_score if audit_result else 0
                    } if audit_result else {},
                    "status": scan.status.value,
                    "created_at": scan.started_at.isoformat(),
                    "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                    "error_message": scan.error_message
                }
                
                audit_history.append(history_item)
                
            except Exception as e:
                logger.warning(f"Error getting audit result for scan {scan.id}: {e}")
                # Include scan even if result retrieval fails
                audit_history.append({
                    "scan_id": scan.id,
                    "domain": scan.metadata.get("domain") if scan.metadata else "Unknown",
                    "overall_score": 0,
                    "component_scores": {},
                    "status": scan.status.value,
                    "created_at": scan.started_at.isoformat(),
                    "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                    "error_message": scan.error_message or "Result data unavailable"
                })
        
        return {
            "audit_history": audit_history,
            "total_count": len(audit_history),
            "filtered_domain": domain,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting audit history for user {current_user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit history"
        )

@app.get("/api/audit/compare/{scan_id_1}/{scan_id_2}")
async def compare_audits(
    scan_id_1: str,
    scan_id_2: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Compare two audit results for the same or different domains
    
    Features:
    - Score comparison with change indicators
    - Recommendation differences
    - Timeline analysis
    """
    try:
        # Get both scans and verify ownership
        scan_1 = await db_service.get_scan(scan_id_1, current_user_id)
        scan_2 = await db_service.get_scan(scan_id_2, current_user_id)
        
        if not scan_1 or not scan_2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both audit scans not found"
            )
        
        if scan_1.scan_type != ScanType.AUDIT or scan_2.scan_type != ScanType.AUDIT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both scans must be audit scans"
            )
        
        # Get audit results
        result_1 = await db_service.get_audit_result(scan_id_1)
        result_2 = await db_service.get_audit_result(scan_id_2)
        
        if not result_1 or not result_2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit results not found for one or both scans"
            )
        
        # Calculate score changes
        score_changes = {
            "overall_score": {
                "before": result_1.overall_score,
                "after": result_2.overall_score,
                "change": result_2.overall_score - result_1.overall_score,
                "change_percentage": ((result_2.overall_score - result_1.overall_score) / max(result_1.overall_score, 1)) * 100
            },
            "schema_score": {
                "before": result_1.schema_score or 0,
                "after": result_2.schema_score or 0,
                "change": (result_2.schema_score or 0) - (result_1.schema_score or 0),
                "change_percentage": (((result_2.schema_score or 0) - (result_1.schema_score or 0)) / max(result_1.schema_score or 1, 1)) * 100
            },
            "meta_score": {
                "before": result_1.meta_score or 0,
                "after": result_2.meta_score or 0,
                "change": (result_2.meta_score or 0) - (result_1.meta_score or 0),
                "change_percentage": (((result_2.meta_score or 0) - (result_1.meta_score or 0)) / max(result_1.meta_score or 1, 1)) * 100
            },
            "content_score": {
                "before": result_1.content_score or 0,
                "after": result_2.content_score or 0,
                "change": (result_2.content_score or 0) - (result_1.content_score or 0),
                "change_percentage": (((result_2.content_score or 0) - (result_1.content_score or 0)) / max(result_1.content_score or 1, 1)) * 100
            },
            "technical_score": {
                "before": result_1.technical_score or 0,
                "after": result_2.technical_score or 0,
                "change": (result_2.technical_score or 0) - (result_1.technical_score or 0),
                "change_percentage": (((result_2.technical_score or 0) - (result_1.technical_score or 0)) / max(result_1.technical_score or 1, 1)) * 100
            }
        }
        
        # Analyze recommendation changes
        recommendations_1 = {rec.get("issue", ""): rec for rec in result_1.recommendations}
        recommendations_2 = {rec.get("issue", ""): rec for rec in result_2.recommendations}
        
        # Find resolved, new, and persistent recommendations
        resolved_recommendations = []
        new_recommendations = []
        persistent_recommendations = []
        
        for issue, rec in recommendations_1.items():
            if issue not in recommendations_2:
                resolved_recommendations.append(rec)
            else:
                persistent_recommendations.append({
                    "issue": issue,
                    "before": rec,
                    "after": recommendations_2[issue]
                })
        
        for issue, rec in recommendations_2.items():
            if issue not in recommendations_1:
                new_recommendations.append(rec)
        
        # Calculate time difference
        time_diff = scan_2.started_at - scan_1.started_at
        
        return {
            "comparison": {
                "scan_1": {
                    "scan_id": scan_id_1,
                    "domain": scan_1.metadata.get("domain") if scan_1.metadata else "Unknown",
                    "timestamp": scan_1.started_at.isoformat(),
                    "overall_score": result_1.overall_score
                },
                "scan_2": {
                    "scan_id": scan_id_2,
                    "domain": scan_2.metadata.get("domain") if scan_2.metadata else "Unknown",
                    "timestamp": scan_2.started_at.isoformat(),
                    "overall_score": result_2.overall_score
                },
                "time_difference_days": time_diff.days,
                "score_changes": score_changes,
                "recommendation_analysis": {
                    "resolved_count": len(resolved_recommendations),
                    "new_count": len(new_recommendations),
                    "persistent_count": len(persistent_recommendations),
                    "resolved_recommendations": resolved_recommendations,
                    "new_recommendations": new_recommendations,
                    "persistent_recommendations": persistent_recommendations
                },
                "summary": {
                    "overall_improvement": score_changes["overall_score"]["change"] > 0,
                    "best_improvement": max(score_changes.items(), key=lambda x: x[1]["change"])[0],
                    "needs_attention": min(score_changes.items(), key=lambda x: x[1]["change"])[0] if min(score_changes.values(), key=lambda x: x["change"])["change"] < 0 else None
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing audits {scan_id_1} and {scan_id_2}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare audit results"
        )

@app.get("/api/audit/domain-history/{domain}")
async def get_domain_audit_history(
    domain: str,
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get audit history for a specific domain with trend analysis
    
    Features:
    - Domain-specific audit timeline
    - Score trend analysis
    - Improvement recommendations based on history
    """
    try:
        # Normalize domain
        if not domain.startswith(('http://', 'https://')):
            domain = f"https://{domain}"
        
        # Get audit history for this domain
        all_scans = await db_service.get_user_scans(current_user_id, limit * 2)  # Get more to filter
        
        # Filter for audit scans of this domain
        domain_scans = [
            scan for scan in all_scans 
            if (scan.scan_type == ScanType.AUDIT and 
                scan.metadata and 
                scan.metadata.get("domain") == domain)
        ][:limit]
        
        if not domain_scans:
            return {
                "domain": domain,
                "audit_history": [],
                "trend_analysis": {
                    "total_audits": 0,
                    "score_trend": "no_data",
                    "average_score": 0,
                    "best_score": 0,
                    "latest_score": 0
                },
                "recommendations": []
            }
        
        # Get audit results and build history
        audit_history = []
        scores = []
        
        for scan in domain_scans:
            try:
                audit_result = await db_service.get_audit_result(scan.id)
                
                if audit_result:
                    history_item = {
                        "scan_id": scan.id,
                        "overall_score": audit_result.overall_score,
                        "component_scores": {
                            "schema_score": audit_result.schema_score or 0,
                            "meta_score": audit_result.meta_score or 0,
                            "content_score": audit_result.content_score or 0,
                            "technical_score": audit_result.technical_score or 0
                        },
                        "timestamp": scan.started_at.isoformat(),
                        "status": scan.status.value,
                        "recommendations_count": len(audit_result.recommendations)
                    }
                    
                    audit_history.append(history_item)
                    scores.append(audit_result.overall_score)
                    
            except Exception as e:
                logger.warning(f"Error getting audit result for scan {scan.id}: {e}")
        
        # Analyze trends
        trend_analysis = {
            "total_audits": len(audit_history),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "best_score": max(scores) if scores else 0,
            "latest_score": scores[0] if scores else 0,  # Most recent first
            "score_trend": "improving" if len(scores) >= 2 and scores[0] > scores[-1] else 
                          "declining" if len(scores) >= 2 and scores[0] < scores[-1] else "stable"
        }
        
        # Generate recommendations based on history
        recommendations = []
        if len(audit_history) >= 2:
            latest = audit_history[0]
            previous = audit_history[1]
            
            # Check for declining scores
            for component, latest_score in latest["component_scores"].items():
                previous_score = previous["component_scores"].get(component, 0)
                if latest_score < previous_score:
                    recommendations.append({
                        "priority": "medium",
                        "category": component.replace("_score", ""),
                        "issue": f"{component.replace('_', ' ').title()} has declined",
                        "recommendation": f"Focus on improving {component.replace('_score', '').replace('_', ' ')} elements",
                        "score_change": latest_score - previous_score
                    })
        
        return {
            "domain": domain,
            "audit_history": audit_history,
            "trend_analysis": trend_analysis,
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Error getting domain audit history for {domain}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve domain audit history"
        )

@app.post("/api/analyze/competitors")
async def analyze_competitors(
    request: Dict[str, Any],
    current_profile: Profile = Depends(verify_scan_quota)
):
    """Analyze brand visibility compared to competitors"""
    try:
        # Import here to avoid circular imports
        from services.llm_service import LLMService
        from services.cache_service import CacheService
        
        # Initialize services
        llm_service = LLMService()
        cache_service = CacheService()
        
        # Extract parameters
        brand_name = request.get("brand_name")
        competitors = request.get("competitors", [])
        context = request.get("context", {})
        
        if not brand_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Brand name is required"
            )
        
        if not competitors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one competitor is required"
            )
        
        # Create cache key
        competitors_hash = "-".join(sorted(competitors)[:3])
        cache_key = f"competitor_analysis:{brand_name}:{competitors_hash}"
        
        # Check cache first
        cached_result = await cache_service.get_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for competitor analysis: {brand_name}")
            
            # Update scan usage
            await db_service.update_scan_usage(current_profile.id)
            
            # Return cached result with updated scans_remaining
            cached_result["scans_remaining"] = current_profile.scans_remaining - 1
            cached_result["cached"] = True
            return cached_result
        
        # Create a new scan record
        scan_data = {
            "user_id": current_profile.id,
            "brand_name": brand_name,
            "scan_type": "competitor_analysis",
            "status": "processing"
        }
        scan_id = await db_service.create_scan(scan_data)
        
        # Update scan usage
        await db_service.update_scan_usage(current_profile.id)
        
        # Analyze competitors
        analysis = await llm_service.analyze_competitors(
            brand_name,
            competitors,
            context
        )
        
        # Prepare response
        response = {
            "scan_id": scan_id,
            "brand_name": brand_name,
            "competitors": competitors,
            "analysis": analysis,
            "status": "completed",
            "scans_remaining": current_profile.scans_remaining - 1
        }
        
        # Cache the result
        await cache_service.set_cache(cache_key, response, ttl_hours=settings.CACHE_TTL_HOURS)
        
        # Update scan record
        await db_service.update_scan(scan_id, {
            "status": "completed",
            "progress": 100,
            "completed_at": "now()",
            "metadata": {
                "brand_share": analysis["brand_share"],
                "competitor_count": len(competitors)
            }
        })
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing competitors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Competitor analysis failed: {str(e)}"
        )

# Optimization endpoints
@app.post("/api/optimize/schema")
async def optimize_schema(
    request: Dict[str, Any],
    current_profile: Profile = Depends(verify_scan_quota)
):
    """
    Schema markup generation endpoint
    
    Generates JSON-LD schema markup for Organization, Product, FAQ, or Service types
    with Schema.org compliance validation and implementation recommendations.
    """
    try:
        # Import here to avoid circular imports
        from services.optimization_service import (
            optimization_service, 
            SchemaOptimizationRequest, 
            OptimizationResult
        )
        
        # Validate and parse request
        try:
            schema_request = SchemaOptimizationRequest(**request)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request data: {str(e)}"
            )
        
        # Update scan usage
        await db_service.update_scan_usage(current_profile.id)
        
        # Generate schema markup
        result = await optimization_service.generate_schema_markup(schema_request)
        
        # Create scan record for tracking
        scan_data = {
            "user_id": current_profile.id,
            "brand_name": schema_request.brand_name,
            "scan_type": "optimization",
            "status": "completed",
            "metadata": {
                "optimization_type": "schema",
                "schema_type": schema_request.schema_type,
                "compliance_score": result.compliance_score
            }
        }
        scan_id = await db_service.create_scan(scan_data)
        
        # Add scan tracking to response
        response = result.dict()
        response["scan_id"] = scan_id
        response["scans_remaining"] = current_profile.scans_remaining - 1
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schema optimization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema optimization failed: {str(e)}"
        )

@app.post("/api/optimize/content")
async def optimize_content(
    request: Dict[str, Any],
    current_profile: Profile = Depends(verify_scan_quota)
):
    """
    Content optimization endpoint
    
    Generates optimized content including meta tags, FAQ content, and landing page templates
    with industry-specific recommendations and LLM-friendly formatting.
    """
    try:
        # Import here to avoid circular imports
        from services.optimization_service import (
            optimization_service, 
            ContentOptimizationRequest, 
            OptimizationResult
        )
        
        # Validate and parse request
        try:
            content_request = ContentOptimizationRequest(**request)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request data: {str(e)}"
            )
        
        # Update scan usage
        await db_service.update_scan_usage(current_profile.id)
        
        # Generate content based on type
        content_type = content_request.content_type
        
        if content_type == "meta_tags":
            result = await optimization_service.optimize_meta_tags(content_request)
        elif content_type == "faq":
            result = await optimization_service.generate_faq_content(content_request)
        elif content_type == "landing_page":
            result = await optimization_service.generate_landing_page_content(content_request)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported content type: {content_type}"
            )
        
        # Create scan record for tracking
        scan_data = {
            "user_id": current_profile.id,
            "brand_name": content_request.brand_name,
            "scan_type": "optimization",
            "status": "completed",
            "metadata": {
                "optimization_type": "content",
                "content_type": content_type,
                "compliance_score": result.compliance_score
            }
        }
        scan_id = await db_service.create_scan(scan_data)
        
        # Add scan tracking to response
        response = result.dict()
        response["scan_id"] = scan_id
        response["scans_remaining"] = current_profile.scans_remaining - 1
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content optimization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content optimization failed: {str(e)}"
        )

@app.get("/api/optimize/history")
async def get_optimization_history(
    optimization_type: Optional[str] = None,
    limit: int = 50,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get optimization history for the current user
    
    Features:
    - Filter by optimization type (schema, meta_tags, faq, landing_page)
    - Paginated results with configurable limit
    - Includes optimization scores and timestamps for tracking progress
    """
    try:
        # Get user's optimization scans
        scans = await db_service.get_user_scans(current_user_id, limit)
        
        # Filter for optimization scans only
        optimization_scans = [scan for scan in scans if scan.scan_type == ScanType.OPTIMIZATION]
        
        # Further filter by optimization type if specified
        if optimization_type:
            optimization_scans = [
                scan for scan in optimization_scans 
                if scan.metadata and scan.metadata.get("optimization_type") == optimization_type
            ]
        
        # Format optimization history
        optimization_history = []
        for scan in optimization_scans:
            history_item = {
                "scan_id": scan.id,
                "brand_name": scan.metadata.get("brand_name") if scan.metadata else "Unknown",
                "optimization_type": scan.metadata.get("optimization_type") if scan.metadata else "unknown",
                "content_type": scan.metadata.get("content_type") if scan.metadata else None,
                "schema_type": scan.metadata.get("schema_type") if scan.metadata else None,
                "compliance_score": scan.metadata.get("compliance_score") if scan.metadata else 0,
                "status": scan.status.value,
                "created_at": scan.started_at.isoformat(),
                "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                "error_message": scan.error_message
            }
            
            optimization_history.append(history_item)
        
        # Sort by created_at (newest first)
        optimization_history.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "optimization_history": optimization_history,
            "total_count": len(optimization_history),
            "filtered_type": optimization_type if optimization_type else None,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting optimization history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve optimization history"
        )

# Custom exception for LLM API errors
class LLMAPIException(HTTPException):
    """Exception for LLM API errors"""
    def __init__(self, status_code: int, detail: str, provider: str = None, model: str = None):
        super().__init__(status_code=status_code, detail=detail)
        self.provider = provider
        self.model = model

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent error format"""
    from datetime import datetime
    
    # Check if it's an LLM API exception
    if isinstance(exc, LLMAPIException):
        return ErrorResponse(
            error=exc.detail,
            message=f"LLM API Error: {exc.detail}",
            details={
                "provider": exc.provider,
                "model": exc.model
            },
            timestamp=datetime.now().isoformat(),
            request_id=request.state.request_id if hasattr(request.state, "request_id") else None
        )
    
    return ErrorResponse(
        error=exc.detail,
        message=f"HTTP {exc.status_code}: {exc.detail}",
        timestamp=datetime.now().isoformat(),
        request_id=request.state.request_id if hasattr(request.state, "request_id") else None
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    from datetime import datetime
    
    logger.error(f"Unhandled exception: {exc}")
    return ErrorResponse(
        error="Internal Server Error",
        message="An unexpected error occurred",
        timestamp=datetime.now().isoformat(),
        request_id=request.state.request_id if hasattr(request.state, "request_id") else None
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)