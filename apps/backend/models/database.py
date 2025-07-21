"""
Pydantic models for database entities and API requests/responses
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum
import re

# Enums for database constraints
class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    AGENCY = "agency"
    ENTERPRISE = "enterprise"

class ScanType(str, Enum):
    VISIBILITY = "visibility"
    AUDIT = "audit"
    SIMULATION = "simulation"
    OPTIMIZATION = "optimization"

class ScanStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Base models
class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None

# User Profile Models
class ProfileBase(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=255)
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=255)

class Profile(ProfileBase, TimestampMixin):
    id: str
    scans_remaining: int = 1
    scans_used: int = 0
    
    class Config:
        from_attributes = True

# Brand Models
class BrandBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    keywords: List[str] = Field(default=[], max_items=20)
    description: Optional[str] = None
    competitors: List[str] = Field(default=[], max_items=10)
    
    @validator('domain')
    def validate_domain(cls, v):
        if not re.match(r'^https?://.+', v):
            raise ValueError('Domain must start with http:// or https://')
        return v
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if len(v) > 20:
            raise ValueError('Maximum 20 keywords allowed')
        return [keyword.strip() for keyword in v if keyword.strip()]
    
    @validator('competitors')
    def validate_competitors(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 competitors allowed')
        return [comp.strip() for comp in v if comp.strip()]

class BrandCreate(BrandBase):
    pass

class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    keywords: Optional[List[str]] = Field(None, max_items=20)
    description: Optional[str] = None
    competitors: Optional[List[str]] = Field(None, max_items=10)
    
    @validator('domain')
    def validate_domain(cls, v):
        if v and not re.match(r'^https?://.+', v):
            raise ValueError('Domain must start with http:// or https://')
        return v

class Brand(BrandBase, TimestampMixin):
    id: str
    user_id: str
    
    class Config:
        from_attributes = True

# Scan Models
class ScanBase(BaseModel):
    brand_id: str
    scan_type: ScanType
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ScanCreate(ScanBase):
    pass

class ScanUpdate(BaseModel):
    status: Optional[ScanStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Scan(ScanBase, TimestampMixin):
    id: str
    user_id: str
    status: ScanStatus = ScanStatus.PENDING
    progress: int = Field(0, ge=0, le=100)
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

# Results Models
class VisibilityResultBase(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    gpt35_score: Optional[int] = Field(None, ge=0, le=100)
    gpt4_score: Optional[int] = Field(None, ge=0, le=100)
    claude_score: Optional[int] = Field(None, ge=0, le=100)
    mention_count: int = Field(0, ge=0)
    competitor_comparison: Dict[str, Any] = Field(default_factory=dict)
    raw_responses: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)

class VisibilityResultCreate(VisibilityResultBase):
    scan_id: str

class VisibilityResult(VisibilityResultBase):
    id: str
    scan_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuditResultBase(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    schema_score: Optional[int] = Field(None, ge=0, le=100)
    meta_score: Optional[int] = Field(None, ge=0, le=100)
    content_score: Optional[int] = Field(None, ge=0, le=100)
    technical_score: Optional[int] = Field(None, ge=0, le=100)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    technical_details: Dict[str, Any] = Field(default_factory=dict)
    audit_data: Dict[str, Any] = Field(default_factory=dict)

class AuditResultCreate(AuditResultBase):
    scan_id: str

class AuditResult(AuditResultBase):
    id: str
    scan_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SimulationResultBase(BaseModel):
    prompt_text: str
    response_text: str
    brand_mentioned: bool = False
    mention_context: Optional[str] = None
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    competitor_mentions: List[Dict[str, Any]] = Field(default_factory=list)

class SimulationResultCreate(SimulationResultBase):
    scan_id: str

class SimulationResult(SimulationResultBase):
    id: str
    scan_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Cache Models
class CacheEntry(BaseModel):
    cache_key: str
    response_data: Dict[str, Any]
    model_name: str
    prompt_hash: str
    expires_at: datetime
    access_count: int = 1

# API Request Models
class ScanRequest(BaseModel):
    brand_name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., max_length=255)
    keywords: List[str] = Field(default=[], max_items=20)
    competitors: List[str] = Field(default=[], max_items=5)
    scan_type: ScanType
    
    @validator('domain')
    def validate_domain(cls, v):
        if not re.match(r'^https?://.+', v):
            raise ValueError('Domain must start with http:// or https://')
        return v

class PromptSimulationRequest(BaseModel):
    brand_name: str = Field(..., min_length=1, max_length=255)
    prompts: List[str] = Field(..., min_items=1, max_items=50)
    custom_prompts: List[str] = Field(default=[], max_items=10)
    
    @validator('prompts')
    def validate_prompts(cls, v):
        if not v:
            raise ValueError('At least one prompt is required')
        return [prompt.strip() for prompt in v if prompt.strip()]

class VisibilityAuditRequest(BaseModel):
    domain: str = Field(..., max_length=255)
    
    @validator('domain')
    def validate_domain(cls, v):
        if not re.match(r'^https?://.+', v):
            raise ValueError('Domain must start with http:// or https://')
        return v

# API Response Models
class ScanResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    progress: int = Field(0, ge=0, le=100)
    message: str
    estimated_completion: Optional[datetime] = None

class ScanSummary(BaseModel):
    id: str
    brand_name: str
    domain: str
    scan_type: ScanType
    status: ScanStatus
    progress: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    overall_score: Optional[int] = None

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    request_id: Optional[str] = None

# Authentication Models
class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=255)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: Dict[str, Any]
    expires_in: int

class TokenRefresh(BaseModel):
    refresh_token: str