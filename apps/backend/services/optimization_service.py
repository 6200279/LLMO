"""
Optimization Service for LLMO MVP
"""

import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)

class OptimizationRequest(BaseModel):
    """Base request model for optimization services"""
    brand_name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    
    @validator('domain')
    def validate_domain(cls, v):
        if not re.match(r'^https?://.+', v):
            raise ValueError('Domain must start with http:// or https://')
        return v

class SchemaOptimizationRequest(OptimizationRequest):
    """Request model for schema markup generation"""
    schema_type: str = Field(..., regex=r'^(organization|product|faq|service)$')
    additional_data: Dict[str, Any] = Field(default_factory=dict)

class ContentOptimizationRequest(OptimizationRequest):
    """Request model for content optimization"""
    content_type: str = Field(..., regex=r'^(meta_tags|faq|landing_page)$')
    target_keywords: List[str] = Field(default=[], max_items=10)
    target_audience: Optional[str] = Field(None, max_length=255)

class OptimizationResult(BaseModel):
    """Response model for optimization results"""
    optimization_type: str
    brand_name: str
    domain: str
    generated_content: Dict[str, Any]
    recommendations: List[Dict[str, str]]
    compliance_score: int = Field(..., ge=0, le=100)
    timestamp: datetime# Schema Templates
SCHEMA_TEMPLATES = {
    "organization": {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "{brand_name}",
        "url": "{domain}",
        "description": "{description}",
        "industry": "{industry}"
    },
    "product": {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "{product_name}",
        "description": "{product_description}",
        "brand": {
            "@type": "Brand",
            "name": "{brand_name}"
        }
    },
    "service": {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": "{service_name}",
        "description": "{service_description}",
        "provider": {
            "@type": "Organization",
            "name": "{brand_name}",
            "url": "{domain}"
        }
    }
}

# Industry-specific FAQ patterns
INDUSTRY_FAQ_PATTERNS = {
    "technology": [
        "What is {brand_name} and how does it work?",
        "How secure is {brand_name}?",
        "What are the pricing plans for {brand_name}?",
        "How do I get started with {brand_name}?",
        "What customer support does {brand_name} offer?"
    ],
    "healthcare": [
        "What services does {brand_name} provide?",
        "How do I schedule an appointment with {brand_name}?",
        "What insurance does {brand_name} accept?",
        "Where is {brand_name} located?",
        "What are {brand_name}'s hours of operation?"
    ],
    "default": [
        "What is {brand_name}?",
        "How does {brand_name} work?",
        "What makes {brand_name} different?",
        "How much does {brand_name} cost?",
        "How can I contact {brand_name}?"
    ]
}

# Meta tag templates by industry
META_TAG_TEMPLATES = {
    "technology": {
        "title_patterns": [
            "{brand_name} - {service_type} Software Solution",
            "{brand_name}: Advanced {service_type} Platform"
        ],
        "description_patterns": [
            "Discover {brand_name}, the leading {service_type} solution. {key_benefit}.",
            "{brand_name} provides advanced {service_type} technology for {target_audience}."
        ]
    },
    "default": {
        "title_patterns": [
            "{brand_name} - {service_type}",
            "{brand_name}: Quality {service_type}"
        ],
        "description_patterns": [
            "Choose {brand_name} for quality {service_type}. {key_benefit}.",
            "{brand_name} provides professional {service_type} services."
        ]
    }
}class OptimizationService:
    """Service for generating optimized content and schema markup"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def generate_schema_markup(self, request: SchemaOptimizationRequest) -> OptimizationResult:
        """Generate JSON-LD schema markup for improved LLM visibility"""
        try:
            schema_type = request.schema_type.lower()
            
            if schema_type not in SCHEMA_TEMPLATES:
                raise ValueError(f"Unsupported schema type: {schema_type}")
            
            # Get base template
            template = SCHEMA_TEMPLATES[schema_type].copy()
            
            # Prepare substitution data
            substitution_data = {
                "brand_name": request.brand_name,
                "domain": request.domain,
                "description": request.description or f"{request.brand_name} - Quality services and products",
                "industry": request.industry or "Business",
                **request.additional_data
            }
            
            # Generate schema
            schema = self._substitute_template_values(template, substitution_data)
            
            # Validate schema compliance
            compliance_score = await self._validate_schema_compliance(schema)
            
            # Generate implementation recommendations
            recommendations = await self._generate_schema_recommendations(schema_type, compliance_score)
            
            return OptimizationResult(
                optimization_type=f"schema_{schema_type}",
                brand_name=request.brand_name,
                domain=request.domain,
                generated_content={
                    "schema_markup": schema,
                    "html_implementation": f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>',
                    "schema_type": schema_type
                },
                recommendations=recommendations,
                compliance_score=compliance_score,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Schema generation error: {e}")
            raise    async def optimize_meta_tags(self, request: ContentOptimizationRequest) -> OptimizationResult:
        """Generate optimized meta tags for improved LLM visibility"""
        try:
            industry = request.industry or "default"
            templates = META_TAG_TEMPLATES.get(industry, META_TAG_TEMPLATES["default"])
            
            # Prepare substitution data
            substitution_data = {
                "brand_name": request.brand_name,
                "service_type": request.industry or "services",
                "key_benefit": self._extract_key_benefit(request.description, request.target_keywords),
                "target_audience": request.target_audience or "businesses"
            }
            
            # Generate title options
            title_options = []
            for pattern in templates["title_patterns"]:
                title = pattern.format(**substitution_data)
                if len(title) <= 60:  # SEO best practice
                    title_options.append(title)
            
            # Generate description options
            description_options = []
            for pattern in templates["description_patterns"]:
                description = pattern.format(**substitution_data)
                if len(description) <= 160:  # SEO best practice
                    description_options.append(description)
            
            # Generate Open Graph tags
            og_tags = {
                "og:title": title_options[0] if title_options else f"{request.brand_name}",
                "og:description": description_options[0] if description_options else request.description or f"Quality services from {request.brand_name}",
                "og:url": request.domain,
                "og:type": "website",
                "og:site_name": request.brand_name
            }
            
            # Generate Twitter Card tags
            twitter_tags = {
                "twitter:card": "summary_large_image",
                "twitter:title": title_options[0] if title_options else f"{request.brand_name}",
                "twitter:description": description_options[0] if description_options else request.description or f"Quality services from {request.brand_name}"
            }
            
            # Calculate compliance score
            compliance_score = await self._calculate_meta_compliance_score(title_options, description_options, og_tags, twitter_tags)
            
            # Generate recommendations
            recommendations = await self._generate_meta_recommendations(title_options, description_options, compliance_score)
            
            return OptimizationResult(
                optimization_type="meta_tags",
                brand_name=request.brand_name,
                domain=request.domain,
                generated_content={
                    "title_options": title_options,
                    "description_options": description_options,
                    "open_graph_tags": og_tags,
                    "twitter_tags": twitter_tags,
                    "html_implementation": self._generate_meta_html(title_options[0] if title_options else "", description_options[0] if description_options else "", og_tags, twitter_tags)
                },
                recommendations=recommendations,
                compliance_score=compliance_score,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Meta tag optimization error: {e}")
            raise    async def generate_faq_content(self, request: ContentOptimizationRequest) -> OptimizationResult:
        """Generate FAQ content based on common LLM query patterns"""
        try:
            industry = request.industry or "default"
            faq_patterns = INDUSTRY_FAQ_PATTERNS.get(industry, INDUSTRY_FAQ_PATTERNS["default"])
            
            # Generate FAQ items
            faq_items = []
            for pattern in faq_patterns:
                question = pattern.format(brand_name=request.brand_name)
                answer = await self._generate_faq_answer(question, request)
                
                faq_items.append({
                    "question": question,
                    "answer": answer
                })
            
            # Generate FAQ schema
            faq_schema = {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["question"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": item["answer"]
                        }
                    }
                    for item in faq_items
                ]
            }
            
            # Generate HTML implementation
            html_implementation = self._generate_faq_html(faq_items, faq_schema)
            
            # Calculate compliance score
            compliance_score = await self._validate_schema_compliance(faq_schema)
            
            # Generate recommendations
            recommendations = await self._generate_faq_recommendations(faq_items, compliance_score)
            
            return OptimizationResult(
                optimization_type="faq_content",
                brand_name=request.brand_name,
                domain=request.domain,
                generated_content={
                    "faq_items": faq_items,
                    "schema_markup": faq_schema,
                    "html_implementation": html_implementation
                },
                recommendations=recommendations,
                compliance_score=compliance_score,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"FAQ generation error: {e}")
            raise