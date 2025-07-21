# LLMO MVP Design Document

## Overview

This document outlines the technical design for LLMO MVP, a SaaS platform for optimizing brand visibility in Large Language Models. The design follows a microservices-inspired architecture with clear separation of concerns, scalable background processing, and comprehensive caching strategies.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Next.js Frontend]
        AUTH[Authentication]
        DASH[Dashboard]
    end
    
    subgraph "API Gateway Layer"
        API[FastAPI Gateway]
        RATE[Rate Limiting]
        VALID[Request Validation]
    end
    
    subgraph "Service Layer"
        LLM[LLM Service]
        SCRAPER[Web Scraper Service]
        OPT[Optimization Service]
        TASK[Task Service]
    end
    
    subgraph "Background Processing"
        CELERY[Celery Workers]
        QUEUE[Redis Queue]
        JOBS[Background Jobs]
    end
    
    subgraph "Supabase Backend"
        SUPABASE_DB[(Supabase PostgreSQL)]
        SUPABASE_AUTH[Supabase Auth]
        SUPABASE_STORAGE[Supabase Storage]
        SUPABASE_REALTIME[Supabase Realtime]
    end
    
    subgraph "External APIs"
        OPENAI[OpenAI API]
        ANTHROPIC[Anthropic API]
        WEBSITES[Target Websites]
    end
    
    UI --> API
    API --> LLM
    API --> SCRAPER
    API --> OPT
    API --> TASK
    
    LLM --> OPENAI
    LLM --> ANTHROPIC
    SCRAPER --> WEBSITES
    
    CELERY --> SUPABASE_DB
    
    API --> SUPABASE_DB
    API --> SUPABASE_AUTH
    UI --> SUPABASE_AUTH
    UI --> SUPABASE_REALTIME
```

### Technology Stack

**Frontend:**
- Next.js 14 with App Router for server-side rendering and optimal performance
- TypeScript for type safety and developer experience
- Tailwind CSS for consistent, responsive design
- Supabase JavaScript client for database and auth
- React Query for API state management and caching

**Backend:**
- FastAPI for high-performance API with automatic OpenAPI documentation
- Supabase Python client for database operations
- Supabase Auth for user authentication and authorization
- Supabase Realtime for live updates and progress tracking
- Pydantic for data validation and serialization

**Infrastructure:**
- Supabase hosted PostgreSQL with built-in optimizations
- Supabase Auth for user management
- Supabase Storage for file uploads
- Supabase Edge Functions for serverless compute (future)
- Docker containers for FastAPI deployment

## Components and Interfaces

### 1. Supabase Authentication Service

**Purpose:** Handle user registration, authentication, and session management using Supabase Auth

**Key Components:**
```python
class SupabaseAuthService:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    async def register_user(self, email: str, password: str, metadata: Dict) -> AuthResponse
    async def authenticate_user(self, email: str, password: str) -> AuthResponse
    async def verify_email(self, token: str) -> bool
    async def reset_password(self, email: str) -> bool
    async def refresh_token(self, refresh_token: str) -> AuthResponse
    async def get_current_user(self, access_token: str) -> User
    async def update_user_metadata(self, user_id: str, metadata: Dict) -> User
```

**Supabase Auth Features:**
- Built-in JWT tokens with automatic refresh
- Secure password hashing and validation
- Email verification with customizable templates
- Built-in rate limiting and security measures
- Social authentication support (Google, GitHub, etc.)
- Row Level Security (RLS) for data access control

### 2. LLM Service

**Purpose:** Interface with multiple LLM providers for brand visibility analysis

**Key Components:**
```python
class LLMService:
    async def query_brand_visibility(
        self, 
        brand_name: str, 
        domain: str, 
        keywords: List[str], 
        model: str
    ) -> VisibilityResult
    
    async def simulate_prompts(
        self, 
        brand_name: str, 
        prompts: List[str]
    ) -> List[PromptResult]
    
    async def analyze_competitors(
        self, 
        brand_name: str, 
        competitors: List[str], 
        context: Dict
    ) -> CompetitorAnalysis
    
    async def detect_brand_mentions(
        self, 
        text: str, 
        brand_name: str
    ) -> MentionAnalysis
```

**Provider Abstraction:**
```python
class LLMProvider(ABC):
    @abstractmethod
    async def query(self, prompt: str, **kwargs) -> str
    
    @abstractmethod
    async def get_usage_stats(self) -> Dict
    
    @abstractmethod
    async def validate_api_key(self) -> bool

class OpenAIProvider(LLMProvider):
    # OpenAI-specific implementation
    
class AnthropicProvider(LLMProvider):
    # Anthropic-specific implementation
```

**Caching Strategy with Supabase:**
- Store LLM responses in Supabase with TTL using database triggers
- Use Supabase functions for cache key generation and management
- Implement cache warming through scheduled Supabase Edge Functions
- Cache invalidation using Supabase database triggers and webhooks

### 3. Web Scraper Service

**Purpose:** Analyze websites for LLM-friendly content and structure

**Key Components:**
```python
class WebScraperService:
    async def audit_website(self, domain: str) -> AuditResult
    async def analyze_schema_org(self, soup: BeautifulSoup) -> SchemaAnalysis
    async def analyze_meta_tags(self, soup: BeautifulSoup) -> MetaAnalysis
    async def analyze_content_structure(self, soup: BeautifulSoup) -> ContentAnalysis
    async def calculate_llm_score(self, analyses: List[Analysis]) -> int
    async def generate_recommendations(self, analyses: List[Analysis]) -> List[Recommendation]
```

**Scoring Algorithm:**
```python
def calculate_llm_friendly_score(audit_data: Dict) -> int:
    score = 0
    
    # Schema.org structured data (30 points)
    if audit_data["schema_org"]["found"]:
        score += min(30, audit_data["schema_org"]["count"] * 10)
    
    # Meta tags optimization (25 points)
    meta_score = 0
    if audit_data["meta"]["title"]: meta_score += 8
    if audit_data["meta"]["description"]: meta_score += 12
    if audit_data["meta"]["og_tags"]: meta_score += 5
    score += meta_score
    
    # Content structure (25 points)
    content = audit_data["content"]
    if content["h1_count"] > 0: score += 8
    if content["word_count"] > 300: score += 7
    if content["list_count"] > 0: score += 5
    if content["faq_sections"] > 0: score += 5
    
    # Technical factors (20 points)
    if audit_data["technical"]["mobile_friendly"]: score += 5
    if audit_data["technical"]["page_speed"] > 70: score += 5
    if audit_data["technical"]["ssl_enabled"]: score += 5
    if audit_data["technical"]["structured_data_valid"]: score += 5
    
    return min(100, score)
```

### 4. Optimization Service

**Purpose:** Generate optimized content and schema for improved LLM visibility

**Key Components:**
```python
class OptimizationService:
    async def generate_schema_markup(
        self, 
        brand_data: BrandData, 
        schema_type: str
    ) -> str
    
    async def optimize_meta_tags(
        self, 
        brand_data: BrandData, 
        current_meta: Dict
    ) -> MetaOptimization
    
    async def generate_faq_content(
        self, 
        brand_data: BrandData, 
        industry: str
    ) -> List[FAQItem]
    
    async def create_content_templates(
        self, 
        brand_data: BrandData, 
        template_type: str
    ) -> ContentTemplate
```

**Schema Generation Templates:**
```python
SCHEMA_TEMPLATES = {
    "organization": {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "{brand_name}",
        "url": "{domain}",
        "description": "{description}",
        "foundingDate": "{founding_date}",
        "industry": "{industry}",
        "sameAs": ["{social_profiles}"]
    },
    "product": {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "{product_name}",
        "description": "{product_description}",
        "brand": {"@type": "Brand", "name": "{brand_name}"},
        "offers": {
            "@type": "Offer",
            "price": "{price}",
            "priceCurrency": "{currency}"
        }
    }
}
```

### 5. Task Management Service

**Purpose:** Manage background job processing and progress tracking

**Key Components:**
```python
class TaskService:
    async def create_scan_task(
        self, 
        user_id: str, 
        scan_data: ScanCreate
    ) -> TaskResponse
    
    async def get_task_status(self, task_id: str) -> TaskStatus
    async def cancel_task(self, task_id: str) -> bool
    async def retry_failed_task(self, task_id: str) -> TaskResponse
    async def get_user_tasks(self, user_id: str) -> List[TaskStatus]
```

**Background Job Architecture:**
```python
@celery_app.task(bind=True, name="process_visibility_scan")
def process_visibility_scan(self, scan_id: str, brand_data: Dict):
    try:
        # Step 1: Initialize and validate (10%)
        self.update_state(state="PROGRESS", meta={"progress": 10})
        
        # Step 2: Query LLMs (60%)
        llm_results = {}
        for i, model in enumerate(["gpt-3.5-turbo", "gpt-4", "claude-3"]):
            result = query_llm(model, brand_data)
            llm_results[model] = result
            progress = 10 + (i + 1) * 20
            self.update_state(state="PROGRESS", meta={"progress": progress})
        
        # Step 3: Analyze and score (20%)
        self.update_state(state="PROGRESS", meta={"progress": 80})
        analysis = analyze_results(llm_results)
        
        # Step 4: Save results (10%)
        self.update_state(state="PROGRESS", meta={"progress": 90})
        save_results(scan_id, analysis)
        
        return {"status": "completed", "results": analysis}
        
    except Exception as e:
        self.retry(exc=e, countdown=60, max_retries=3)
```

## Data Models

### Supabase Database Schema

**User Profiles Table (extends Supabase auth.users):**
```sql
-- Supabase automatically creates auth.users table
-- We create a profiles table for additional user data
CREATE TABLE profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    scans_remaining INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Create policy for users to only access their own profile
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);
```

**Brands Table:**
```sql
CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    keywords TEXT[],
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS and create policies
ALTER TABLE brands ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own brands" ON brands
    FOR ALL USING (auth.uid() = user_id);
```

**Scans Table:**
```sql
CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    scan_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB
);

-- Enable RLS and create policies
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own scans" ON scans
    FOR ALL USING (auth.uid() = user_id);

-- Create function to update scan progress (for real-time updates)
CREATE OR REPLACE FUNCTION update_scan_progress()
RETURNS TRIGGER AS $$
BEGIN
    -- Notify Supabase Realtime subscribers
    PERFORM pg_notify('scan_progress', json_build_object(
        'scan_id', NEW.id,
        'progress', NEW.progress,
        'status', NEW.status
    )::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER scan_progress_trigger
    AFTER UPDATE ON scans
    FOR EACH ROW
    EXECUTE FUNCTION update_scan_progress();
```

**Results Tables with RLS:**
```sql
CREATE TABLE visibility_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    overall_score INTEGER NOT NULL,
    gpt35_score INTEGER,
    gpt4_score INTEGER,
    claude_score INTEGER,
    mention_count INTEGER DEFAULT 0,
    competitor_comparison JSONB,
    raw_responses JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE audit_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    overall_score INTEGER NOT NULL,
    schema_score INTEGER,
    meta_score INTEGER,
    content_score INTEGER,
    recommendations JSONB,
    technical_details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS for results tables
ALTER TABLE visibility_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_results ENABLE ROW LEVEL SECURITY;

-- Create policies using joins to ensure users only see their own results
CREATE POLICY "Users can view own visibility results" ON visibility_results
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM scans 
            WHERE scans.id = visibility_results.scan_id 
            AND scans.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can view own audit results" ON audit_results
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM scans 
            WHERE scans.id = audit_results.scan_id 
            AND scans.user_id = auth.uid()
        )
    );

-- Create cache table for LLM responses
CREATE TABLE llm_response_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    response_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

-- Create index for efficient cache lookups
CREATE INDEX idx_llm_cache_key ON llm_response_cache(cache_key);
CREATE INDEX idx_llm_cache_expires ON llm_response_cache(expires_at);

-- Create function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM llm_response_cache WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;
```

### API Data Models

**Request Models:**
```python
class ScanRequest(BaseModel):
    brand_name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., regex=r'^https?://.+')
    keywords: List[str] = Field(default=[], max_items=20)
    competitors: List[str] = Field(default=[], max_items=5)
    scan_type: str = Field(..., regex=r'^(visibility|audit|simulation)$')

class PromptSimulationRequest(BaseModel):
    brand_name: str = Field(..., min_length=1, max_length=255)
    prompts: List[str] = Field(..., min_items=1, max_items=50)
    custom_prompts: List[str] = Field(default=[], max_items=10)
```

**Response Models:**
```python
class VisibilityResult(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    llm_scores: Dict[str, int]
    mention_analysis: MentionAnalysis
    competitor_comparison: CompetitorAnalysis
    recommendations: List[Recommendation]
    scan_metadata: ScanMetadata

class AuditResult(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    schema_analysis: SchemaAnalysis
    meta_analysis: MetaAnalysis
    content_analysis: ContentAnalysis
    recommendations: List[Recommendation]
    technical_details: TechnicalDetails
```

## Error Handling

### Error Classification

**Client Errors (4xx):**
- 400 Bad Request: Invalid input data
- 401 Unauthorized: Authentication required
- 403 Forbidden: Insufficient permissions
- 404 Not Found: Resource not found
- 429 Too Many Requests: Rate limit exceeded

**Server Errors (5xx):**
- 500 Internal Server Error: Unexpected server error
- 502 Bad Gateway: External API failure
- 503 Service Unavailable: System overloaded
- 504 Gateway Timeout: External API timeout

**Error Response Format:**
```python
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict] = None
    timestamp: datetime
    request_id: str
```

### Retry Logic

**LLM API Failures:**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((APIError, TimeoutError))
)
async def query_llm_with_retry(prompt: str, model: str) -> str:
    # LLM query implementation
    pass
```

**Background Job Failures:**
```python
@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def process_scan_task(self, scan_data: Dict):
    # Task implementation with automatic retry
    pass
```

## Testing Strategy

### Unit Testing

**Service Layer Tests:**
```python
class TestLLMService:
    async def test_brand_visibility_detection(self):
        # Test brand mention detection accuracy
        pass
    
    async def test_score_calculation(self):
        # Test visibility score calculation
        pass
    
    async def test_competitor_analysis(self):
        # Test competitor comparison logic
        pass

class TestWebScraperService:
    async def test_schema_detection(self):
        # Test Schema.org detection
        pass
    
    async def test_score_calculation(self):
        # Test LLM-friendly score calculation
        pass
```

**API Endpoint Tests:**
```python
class TestScanEndpoints:
    async def test_create_visibility_scan(self):
        # Test scan creation and validation
        pass
    
    async def test_get_scan_results(self):
        # Test results retrieval
        pass
    
    async def test_scan_progress_tracking(self):
        # Test progress updates
        pass
```

### Integration Testing

**End-to-End Workflows:**
```python
class TestScanWorkflow:
    async def test_complete_visibility_scan(self):
        # Test complete scan from creation to results
        pass
    
    async def test_audit_workflow(self):
        # Test website audit workflow
        pass
    
    async def test_optimization_workflow(self):
        # Test optimization generation workflow
        pass
```

### Performance Testing

**Load Testing Scenarios:**
- 100 concurrent users performing scans
- 1000 API requests per minute
- Background job processing under load
- Database performance with large datasets

**Performance Targets:**
- API response time: <2 seconds (95th percentile)
- Scan processing time: <2 minutes average
- System uptime: 99.5%
- Database query time: <100ms average

### Security Testing

**Security Test Cases:**
- SQL injection prevention
- XSS attack prevention
- Authentication bypass attempts
- Rate limiting effectiveness
- Data access control validation

## Deployment Architecture

### Development Environment

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  frontend:
    build: ./apps/frontend
    ports: ["3000:3000"]
    environment:
      - NODE_ENV=development
    volumes:
      - ./apps/frontend:/app
  
  backend:
    build: ./apps/backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/llmo
      - REDIS_URL=redis://redis:6379/0
    depends_on: [postgres, redis]
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=llmo
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
  
  celery:
    build: ./apps/backend
    command: celery -A celery_app worker --loglevel=info
    depends_on: [postgres, redis]
```

### Production Environment

**Infrastructure Components:**
- Load balancer (AWS ALB/GCP Load Balancer)
- Container orchestration (ECS/Kubernetes)
- Managed database (RDS/Cloud SQL)
- Managed cache (ElastiCache/Memorystore)
- Object storage (S3/Cloud Storage)
- Monitoring (CloudWatch/Stackdriver)

**Scaling Strategy:**
- Horizontal scaling for API servers
- Dedicated worker nodes for background jobs
- Database read replicas for query optimization
- CDN for static asset delivery
- Auto-scaling based on CPU/memory metrics

This design provides a robust, scalable foundation for the LLMO MVP while maintaining flexibility for future enhancements and optimizations.