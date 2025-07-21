"""
Web scraping service for visibility audits
Enhanced with comprehensive Schema.org analysis, meta tag evaluation,
content structure analysis, and LLM-friendly scoring algorithm

This service analyzes websites for LLM-friendly content and structure,
providing a detailed audit with actionable recommendations for optimization.
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple, Any, Set
import json
import re
import logging
from urllib.parse import urljoin, urlparse
from datetime import datetime
import hashlib
from collections import Counter

logger = logging.getLogger(__name__)

class WebScraperService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; LLMO-Bot/1.0)'
        })
    
    async def audit_website(self, domain: str) -> Dict:
        """Perform comprehensive website audit for LLM visibility"""
        if not domain.startswith(('http://', 'https://')):
            domain = f"https://{domain}"
        
        try:
            logger.info(f"Starting website audit for domain: {domain}")
            response = self.session.get(domain, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Perform comprehensive analysis
            schema_analysis = self._analyze_schema_org(soup)
            meta_analysis = self._analyze_meta_tags(soup)
            content_analysis = self._analyze_content_structure(soup)
            technical_analysis = self._analyze_technical_factors(soup, domain, response)
            
            # Combine all analyses
            audit_results = {
                "domain": domain,
                "status_code": response.status_code,
                "schema_org": schema_analysis,
                "meta_tags": meta_analysis,
                "content_structure": content_analysis,
                "technical_factors": technical_analysis,
                "timestamp": datetime.now().isoformat()
            }
            
            # Calculate component scores
            schema_score = self._calculate_schema_score(schema_analysis)
            meta_score = self._calculate_meta_score(meta_analysis)
            content_score = self._calculate_content_score(content_analysis)
            technical_score = self._calculate_technical_score(technical_analysis)
            
            # Add component scores
            audit_results["component_scores"] = {
                "schema_score": schema_score,
                "meta_score": meta_score,
                "content_score": content_score,
                "technical_score": technical_score
            }
            
            # Calculate overall LLM-friendly score
            audit_results["llm_friendly_score"] = self._calculate_overall_score(
                schema_score, meta_score, content_score, technical_score
            )
            
            # Generate actionable recommendations
            audit_results["recommendations"] = self._generate_recommendations(audit_results)
            
            logger.info(f"Completed website audit for {domain} with score: {audit_results['llm_friendly_score']}")
            return audit_results
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {domain}: {e}")
            return {
                "domain": domain,
                "error": f"Connection error: {str(e)}",
                "error_type": "connection_error",
                "llm_friendly_score": 0,
                "recommendations": [{
                    "priority": "high",
                    "category": "technical",
                    "issue": "Website connection failed",
                    "recommendation": "Ensure your website is accessible and properly configured"
                }]
            }
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error for {domain}: {e}")
            return {
                "domain": domain,
                "error": f"Timeout error: {str(e)}",
                "error_type": "timeout",
                "llm_friendly_score": 0,
                "recommendations": [{
                    "priority": "high",
                    "category": "technical",
                    "issue": "Website response timeout",
                    "recommendation": "Improve website loading speed and server response time"
                }]
            }
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {domain}: {e}")
            return {
                "domain": domain,
                "error": f"HTTP error: {str(e)}",
                "error_type": "http_error",
                "status_code": e.response.status_code if hasattr(e, 'response') else None,
                "llm_friendly_score": 0,
                "recommendations": [{
                    "priority": "high",
                    "category": "technical",
                    "issue": f"HTTP error {e.response.status_code if hasattr(e, 'response') else 'unknown'}",
                    "recommendation": "Fix server configuration or page errors"
                }]
            }
        except Exception as e:
            logger.error(f"Unexpected error for {domain}: {e}")
            return {
                "domain": domain,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unexpected_error",
                "llm_friendly_score": 0,
                "recommendations": [{
                    "priority": "high",
                    "category": "technical",
                    "issue": "Website audit failed",
                    "recommendation": "Contact support for assistance with this website"
                }]
            }
    
    def _analyze_schema_org(self, soup: BeautifulSoup) -> Dict:
        """
        Comprehensive Schema.org structured data analysis
        
        Analyzes all JSON-LD schema markup on the page, including:
        - Schema types and their hierarchy
        - Property coverage and completeness
        - Validation of required properties
        - Detection of high-value schemas for LLMs
        - Nested entity relationships
        """
        schema_scripts = soup.find_all('script', type='application/ld+json')
        schemas = []
        schema_types = set()
        schema_properties = {}
        schema_errors = []
        schema_relationships = []
        schema_completeness = {}
        
        # High-value schema types for LLMs based on research
        llm_valuable_schemas = {
            'Organization': ['name', 'url', 'logo', 'description', 'sameAs'],
            'LocalBusiness': ['name', 'address', 'telephone', 'openingHours', 'priceRange'],
            'Product': ['name', 'description', 'image', 'offers', 'brand', 'review'],
            'FAQPage': ['mainEntity'],
            'Question': ['name', 'acceptedAnswer'],
            'Article': ['headline', 'author', 'datePublished', 'publisher', 'description'],
            'BreadcrumbList': ['itemListElement'],
            'WebSite': ['name', 'url', 'potentialAction'],
            'Person': ['name', 'jobTitle', 'affiliation', 'description'],
            'Review': ['reviewRating', 'author', 'itemReviewed'],
            'Event': ['name', 'startDate', 'location', 'description'],
            'Recipe': ['name', 'recipeIngredient', 'recipeInstructions', 'image'],
            'HowTo': ['name', 'step', 'tool', 'supply']
        }
        
        for script in schema_scripts:
            try:
                schema_data = json.loads(script.string)
                schemas.append(schema_data)
                
                # Extract schema types
                schema_type = self._extract_schema_type(schema_data)
                if schema_type:
                    for t in schema_type.split(', '):
                        schema_types.add(t)
                
                # Extract and count properties
                properties = self._extract_schema_properties(schema_data)
                for prop, value in properties.items():
                    if prop not in schema_properties:
                        schema_properties[prop] = 0
                    schema_properties[prop] += 1
                
                # Analyze schema completeness
                completeness = self._analyze_schema_completeness(schema_data, llm_valuable_schemas)
                for schema_type, score in completeness.items():
                    if schema_type not in schema_completeness:
                        schema_completeness[schema_type] = []
                    schema_completeness[schema_type].append(score)
                
                # Extract relationships between entities
                relationships = self._extract_schema_relationships(schema_data)
                schema_relationships.extend(relationships)
                    
            except json.JSONDecodeError as e:
                schema_errors.append(f"Invalid JSON: {str(e)}")
            except Exception as e:
                schema_errors.append(f"Schema processing error: {str(e)}")
        
        # Check for specific high-value schema types
        has_organization = any(t in schema_types for t in ['Organization', 'LocalBusiness', 'Corporation'])
        has_product = 'Product' in schema_types
        has_faq = any(t in schema_types for t in ['FAQPage', 'Question'])
        has_breadcrumb = 'BreadcrumbList' in schema_types
        has_article = any(t in schema_types for t in ['Article', 'BlogPosting', 'NewsArticle'])
        has_website = 'WebSite' in schema_types
        has_person = 'Person' in schema_types
        has_review = 'Review' in schema_types
        has_event = 'Event' in schema_types
        has_howto = any(t in schema_types for t in ['HowTo', 'Recipe'])
        
        # Calculate average completeness scores
        avg_completeness = {}
        for schema_type, scores in schema_completeness.items():
            avg_completeness[schema_type] = sum(scores) / len(scores)
        
        # Calculate overall schema quality score (0-100)
        schema_quality_score = self._calculate_schema_quality_score(
            schema_types, 
            schema_properties, 
            avg_completeness, 
            schema_errors
        )
        
        return {
            "found": len(schemas) > 0,
            "count": len(schemas),
            "types": list(schema_types),
            "schemas": schemas[:3],  # Limit to first 3 for brevity
            "properties": schema_properties,
            "errors": schema_errors,
            "high_value_schemas": {
                "organization": has_organization,
                "product": has_product,
                "faq": has_faq,
                "breadcrumb": has_breadcrumb,
                "article": has_article,
                "website": has_website,
                "person": has_person,
                "review": has_review,
                "event": has_event,
                "howto": has_howto
            },
            "property_count": len(schema_properties),
            "completeness": avg_completeness,
            "relationships": schema_relationships[:10],  # Limit to first 10 relationships
            "quality_score": schema_quality_score
        }
    
    def _extract_schema_type(self, schema_data: Any) -> Optional[str]:
        """Extract Schema.org type from schema data"""
        if isinstance(schema_data, dict):
            # Handle direct type
            if '@type' in schema_data:
                return schema_data['@type']
            
            # Handle graph
            if '@graph' in schema_data and isinstance(schema_data['@graph'], list):
                types = []
                for item in schema_data['@graph']:
                    if isinstance(item, dict) and '@type' in item:
                        types.append(item['@type'])
                return ', '.join(types) if types else None
        
        return None
    
    def _extract_schema_properties(self, schema_data: Any) -> Dict[str, int]:
        """
        Extract and count Schema.org properties
        
        Recursively processes schema data to extract all properties,
        handling nested objects and arrays properly.
        """
        properties = {}
        
        def process_dict(data, prefix=''):
            if not isinstance(data, dict):
                return
                
            for key, value in data.items():
                if key.startswith('@'):
                    continue
                    
                prop_name = f"{prefix}{key}" if prefix else key
                properties[prop_name] = 1
                
                if isinstance(value, dict):
                    process_dict(value, f"{prop_name}.")
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            process_dict(item, f"{prop_name}.")
        
        if isinstance(schema_data, dict):
            process_dict(schema_data)
            
            # Handle graph
            if '@graph' in schema_data and isinstance(schema_data['@graph'], list):
                for item in schema_data['@graph']:
                    if isinstance(item, dict):
                        process_dict(item)
        
        return properties
        
    def _analyze_schema_completeness(self, schema_data: Any, valuable_schemas: Dict[str, List[str]]) -> Dict[str, float]:
        """
        Analyze schema completeness based on required properties
        
        For each schema type, calculates a completeness score (0-1) based on
        the presence of important properties for LLM understanding.
        """
        completeness_scores = {}
        
        def process_entity(entity):
            if not isinstance(entity, dict) or '@type' not in entity:
                return
                
            entity_type = entity['@type']
            if entity_type in valuable_schemas:
                required_props = valuable_schemas[entity_type]
                present_props = [prop for prop in required_props if prop in entity]
                score = len(present_props) / len(required_props) if required_props else 0
                completeness_scores[entity_type] = score
                
            # Process nested entities
            for key, value in entity.items():
                if isinstance(value, dict) and '@type' in value:
                    process_entity(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and '@type' in item:
                            process_entity(item)
        
        # Process main entity
        if isinstance(schema_data, dict):
            process_entity(schema_data)
            
            # Handle graph
            if '@graph' in schema_data and isinstance(schema_data['@graph'], list):
                for item in schema_data['@graph']:
                    process_entity(item)
        
        return completeness_scores
        
    def _extract_schema_relationships(self, schema_data: Any) -> List[Dict]:
        """
        Extract relationships between schema entities
        
        Identifies connections between different entities in the schema,
        which helps understand the content structure for LLMs.
        """
        relationships = []
        entity_ids = {}  # Map of @id to entity type
        
        # First pass: collect all entity IDs
        def collect_ids(entity, path=""):
            if not isinstance(entity, dict):
                return
                
            entity_id = entity.get('@id')
            entity_type = entity.get('@type')
            
            if entity_id and entity_type:
                entity_ids[entity_id] = {
                    'type': entity_type,
                    'path': path
                }
            
            for key, value in entity.items():
                if isinstance(value, dict):
                    collect_ids(value, f"{path}.{key}" if path else key)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            collect_ids(item, f"{path}.{key}[{i}]" if path else f"{key}[{i}]")
        
        # Second pass: find relationships
        def find_relationships(entity, path=""):
            if not isinstance(entity, dict):
                return
                
            source_id = entity.get('@id')
            source_type = entity.get('@type')
            
            for key, value in entity.items():
                if key.startswith('@'):
                    continue
                    
                # Check for ID references
                if isinstance(value, str) and value in entity_ids:
                    target = entity_ids[value]
                    relationships.append({
                        'source_type': source_type,
                        'source_path': path,
                        'relation': key,
                        'target_type': target['type'],
                        'target_path': target['path']
                    })
                elif isinstance(value, dict):
                    find_relationships(value, f"{path}.{key}" if path else key)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            find_relationships(item, f"{path}.{key}[{i}]" if path else f"{key}[{i}]")
        
        # Process schema data
        if isinstance(schema_data, dict):
            collect_ids(schema_data)
            find_relationships(schema_data)
            
            # Handle graph
            if '@graph' in schema_data and isinstance(schema_data['@graph'], list):
                for item in schema_data['@graph']:
                    collect_ids(item)
                
                for item in schema_data['@graph']:
                    find_relationships(item)
        
        return relationships
        
    def _calculate_schema_quality_score(self, schema_types: Set[str], 
                                       properties: Dict[str, int],
                                       completeness: Dict[str, float],
                                       errors: List[str]) -> int:
        """
        Calculate overall schema quality score (0-100)
        
        Factors considered:
        - Presence of high-value schema types
        - Property count and diversity
        - Completeness of important properties
        - Absence of errors
        """
        score = 0
        
        # Score based on high-value schema types (max 40 points)
        high_value_types = {
            'Organization': 8,
            'LocalBusiness': 8,
            'Product': 8,
            'FAQPage': 7,
            'Article': 7,
            'BreadcrumbList': 5,
            'WebSite': 5,
            'Person': 5,
            'Review': 5,
            'Event': 4,
            'Recipe': 4,
            'HowTo': 4
        }
        
        type_score = sum(high_value_types.get(t, 1) for t in schema_types if t in high_value_types)
        type_score = min(40, type_score)  # Cap at 40 points
        score += type_score
        
        # Score based on property count (max 20 points)
        property_count = len(properties)
        if property_count >= 50:
            score += 20
        elif property_count >= 30:
            score += 15
        elif property_count >= 20:
            score += 10
        elif property_count >= 10:
            score += 5
        else:
            score += max(0, property_count)
        
        # Score based on completeness (max 30 points)
        if completeness:
            avg_completeness = sum(completeness.values()) / len(completeness)
            completeness_score = int(avg_completeness * 30)
            score += completeness_score
        
        # Penalty for errors (max -10 points)
        error_penalty = min(10, len(errors) * 2)
        score -= error_penalty
        
        # Ensure score is in range 0-100
        return max(0, min(100, score))
    
    def _analyze_meta_tags(self, soup: BeautifulSoup) -> Dict:
        """Enhanced meta tag evaluation for LLM optimization"""
        meta_analysis = {
            "title": None,
            "title_length": 0,
            "description": None,
            "description_length": 0,
            "keywords": None,
            "canonical": None,
            "robots": None,
            "viewport": None,
            "og_tags": {},
            "twitter_tags": {},
            "article_tags": {},
            "other_meta": {}
        }
        
        # Title tag
        title_tag = soup.find('title')
        if title_tag and title_tag.text:
            meta_analysis["title"] = title_tag.text.strip()
            meta_analysis["title_length"] = len(meta_analysis["title"])
        
        # Meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            meta_analysis["description"] = desc_tag.get('content').strip()
            meta_analysis["description_length"] = len(meta_analysis["description"])
        
        # Meta keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag and keywords_tag.get('content'):
            meta_analysis["keywords"] = keywords_tag.get('content').strip()
        
        # Canonical link
        canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
        if canonical_tag:
            meta_analysis["canonical"] = canonical_tag.get('href')
        
        # Robots meta
        robots_tag = soup.find('meta', attrs={'name': 'robots'})
        if robots_tag:
            meta_analysis["robots"] = robots_tag.get('content')
        
        # Viewport meta
        viewport_tag = soup.find('meta', attrs={'name': 'viewport'})
        if viewport_tag:
            meta_analysis["viewport"] = viewport_tag.get('content')
        
        # Open Graph tags
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        for tag in og_tags:
            meta_analysis["og_tags"][tag.get('property')] = tag.get('content')
        
        # Twitter Card tags
        twitter_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')})
        for tag in twitter_tags:
            meta_analysis["twitter_tags"][tag.get('name')] = tag.get('content')
        
        # Article tags
        article_tags = soup.find_all('meta', property=lambda x: x and x.startswith('article:'))
        for tag in article_tags:
            meta_analysis["article_tags"][tag.get('property')] = tag.get('content')
        
        # Other meta tags
        other_meta_tags = soup.find_all('meta')
        for tag in other_meta_tags:
            name = tag.get('name')
            if name and name not in ['description', 'keywords', 'robots', 'viewport'] and not name.startswith('twitter:'):
                meta_analysis["other_meta"][name] = tag.get('content')
        
        # Calculate completeness scores
        meta_analysis["completeness"] = {
            "basic": self._calculate_basic_meta_completeness(meta_analysis),
            "social": self._calculate_social_meta_completeness(meta_analysis),
            "overall": 0  # Will be calculated below
        }
        
        # Calculate overall completeness
        meta_analysis["completeness"]["overall"] = (
            meta_analysis["completeness"]["basic"] * 0.7 + 
            meta_analysis["completeness"]["social"] * 0.3
        )
        
        return meta_analysis
    
    def _calculate_basic_meta_completeness(self, meta_analysis: Dict) -> float:
        """
        Calculate basic meta tags completeness score (0-1)
        
        Evaluates the presence and quality of essential meta tags
        based on LLM-friendly optimization best practices.
        """
        score = 0
        total_weight = 0
        
        # Title (weight: 0.4)
        if meta_analysis["title"]:
            weight = 0.4
            total_weight += weight
            
            # Ideal title length for LLMs: 50-60 chars
            # Research shows LLMs prefer slightly longer titles than traditional SEO
            title_length = meta_analysis["title_length"]
            if 50 <= title_length <= 65:  # Optimal for LLMs
                score += weight
            elif 40 <= title_length <= 75:  # Good for LLMs
                score += weight * 0.8
            elif 30 <= title_length <= 85:  # Acceptable for LLMs
                score += weight * 0.6
            else:
                score += weight * 0.3
            
            # Check for brand name in title (bonus)
            if "brand_name" in meta_analysis and meta_analysis["brand_name"]:
                if meta_analysis["brand_name"].lower() in meta_analysis["title"].lower():
                    score += 0.05
        
        # Description (weight: 0.4)
        if meta_analysis["description"]:
            weight = 0.4
            total_weight += weight
            
            # Ideal description length for LLMs: 140-170 chars
            # LLMs can process longer descriptions than traditional SEO limits
            desc_length = meta_analysis["description_length"]
            if 140 <= desc_length <= 170:  # Optimal for LLMs
                score += weight
            elif 120 <= desc_length <= 190:  # Good for LLMs
                score += weight * 0.8
            elif 100 <= desc_length <= 220:  # Acceptable for LLMs
                score += weight * 0.6
            else:
                score += weight * 0.3
            
            # Check for keyword presence in description
            if "keywords" in meta_analysis and meta_analysis["keywords"]:
                keywords = [k.strip().lower() for k in meta_analysis["keywords"].split(",")]
                desc_lower = meta_analysis["description"].lower()
                keyword_matches = sum(1 for k in keywords if k in desc_lower)
                if keyword_matches >= 2:
                    score += 0.05
        
        # Canonical (weight: 0.1)
        if meta_analysis["canonical"]:
            weight = 0.1
            total_weight += weight
            score += weight
        
        # Robots (weight: 0.05)
        if meta_analysis["robots"]:
            weight = 0.05
            total_weight += weight
            
            # Check if indexable by search engines and LLMs
            if "noindex" not in meta_analysis["robots"].lower():
                score += weight
            else:
                # Penalize noindex as it affects LLM training data
                score += weight * 0.2
        
        # Viewport (weight: 0.05)
        if meta_analysis["viewport"]:
            weight = 0.05
            total_weight += weight
            score += weight
        
        # Language tag (weight: 0.05) - Important for LLMs
        if "language" in meta_analysis and meta_analysis["language"]:
            weight = 0.05
            total_weight += weight
            score += weight
        
        # Return normalized score
        return score / max(total_weight, 0.01)
    
    def _calculate_social_meta_completeness(self, meta_analysis: Dict) -> float:
        """
        Calculate social meta tags completeness score (0-1)
        
        Evaluates the presence and quality of social media meta tags,
        which are increasingly important for LLM training data sources.
        """
        score = 0
        total_weight = 0
        
        # Open Graph tags (weight: 0.6)
        og_tags = meta_analysis["og_tags"]
        if og_tags:
            weight = 0.6
            total_weight += weight
            
            # Check for essential OG tags
            essential_tags = ['og:title', 'og:description', 'og:image', 'og:url', 'og:type']
            present_count = sum(1 for tag in essential_tags if tag in og_tags)
            
            # Base score based on presence
            base_score = present_count / len(essential_tags)
            
            # Quality bonuses
            quality_bonus = 0
            
            # Check image dimensions if available
            if 'og:image:width' in og_tags and 'og:image:height' in og_tags:
                try:
                    width = int(og_tags['og:image:width'])
                    height = int(og_tags['og:image:height'])
                    if width >= 1200 and height >= 630:  # Optimal size
                        quality_bonus += 0.1
                except (ValueError, TypeError):
                    pass
            
            # Check for article tags if type is article
            if og_tags.get('og:type') == 'article':
                article_tags = meta_analysis.get("article_tags", {})
                if article_tags:
                    article_bonus = min(0.1, len(article_tags) * 0.02)
                    quality_bonus += article_bonus
            
            score += weight * (base_score + quality_bonus)
        
        # Twitter Card tags (weight: 0.3)
        twitter_tags = meta_analysis["twitter_tags"]
        if twitter_tags:
            weight = 0.3
            total_weight += weight
            
            # Check for essential Twitter tags
            essential_tags = ['twitter:card', 'twitter:title', 'twitter:description', 'twitter:image']
            present_count = sum(1 for tag in essential_tags if tag in twitter_tags)
            score += weight * (present_count / len(essential_tags))
        
        # JSON-LD structured data for social (weight: 0.1) - Increasingly important for LLMs
        if meta_analysis.get("has_social_schema", False):
            weight = 0.1
            total_weight += weight
            score += weight
        
        # Return normalized score
        return score / max(total_weight, 0.01) if total_weight > 0 else 0
    
    def _analyze_content_structure(self, soup: BeautifulSoup) -> Dict:
        """
        Enhanced content structure analysis for LLM-friendly elements
        
        Performs comprehensive analysis of content structure elements
        that are particularly important for LLM understanding and visibility:
        - Semantic HTML structure
        - Content organization and hierarchy
        - FAQ sections and Q&A patterns
        - Content richness and diversity
        - Readability and accessibility
        """
        # Analyze headings
        headings = {
            f"h{i}": len(soup.find_all(f'h{i}')) for i in range(1, 7)
        }
        
        # Analyze heading hierarchy
        heading_hierarchy_score = self._analyze_heading_hierarchy(soup)
        
        # Analyze paragraphs directly (without main content extraction)
        paragraphs = soup.find_all('p')
        paragraph_count = len(paragraphs)
        
        # Calculate average paragraph length
        paragraph_lengths = [len(p.get_text().split()) for p in paragraphs]
        avg_paragraph_length = sum(paragraph_lengths) / max(len(paragraph_lengths), 1)
        
        # Analyze lists
        lists = soup.find_all(['ul', 'ol'])
        list_count = len(lists)
        
        # Count list items
        list_items = soup.find_all('li')
        list_item_count = len(list_items)
        
        # Analyze tables
        tables = soup.find_all('table')
        table_count = len(tables)
        
        # Detect FAQ sections
        faq_sections = self._detect_faq_sections(soup)
        
        # Analyze images with alt text
        images = soup.find_all('img')
        images_with_alt = sum(1 for img in images if img.get('alt'))
        
        # Calculate word count
        word_count = len(soup.get_text().split())
        
        # Analyze content readability
        readability_score = self._calculate_readability(soup.get_text())
        
        # Analyze keyword density
        keyword_density = self._analyze_keyword_density(soup.get_text())
        
        # Analyze semantic HTML5 elements (important for LLMs)
        semantic_elements = self._analyze_semantic_elements(soup)
        
        # Detect structured content patterns
        structured_patterns = self._detect_structured_patterns(soup)
        
        # Calculate content diversity score
        content_diversity_score = self._calculate_content_diversity(
            headings, paragraph_count, list_count, table_count, 
            len(faq_sections), len(images), semantic_elements
        )
        
        # Analyze entity mentions (people, places, organizations)
        entity_mentions = self._analyze_entity_mentions(soup.get_text())
        
        return {
            "headings": headings,
            "heading_hierarchy_score": heading_hierarchy_score,
            "paragraphs": paragraph_count,
            "avg_paragraph_length": avg_paragraph_length,
            "lists": list_count,
            "list_items": list_item_count,
            "tables": table_count,
            "faq_sections": faq_sections,
            "faq_count": len(faq_sections),
            "images": len(images),
            "images_with_alt": images_with_alt,
            "word_count": word_count,
            "readability_score": readability_score,
            "keyword_density": keyword_density,
            "semantic_elements": semantic_elements,
            "structured_patterns": structured_patterns,
            "content_diversity_score": content_diversity_score,
            "entity_mentions": entity_mentions
        }
    
    def _analyze_heading_hierarchy(self, soup: BeautifulSoup) -> float:
        """Analyze heading hierarchy for proper structure (0-1 score)"""
        headings = []
        for i in range(1, 7):
            for h in soup.find_all(f'h{i}'):
                headings.append((i, h.get_text().strip()))
        
        if not headings:
            return 0
        
        # Check if H1 exists and is first
        if not headings or headings[0][0] != 1:
            return 0.3  # Penalize missing H1
        
        # Check for sequential hierarchy (no skipping levels)
        hierarchy_violations = 0
        for i in range(1, len(headings)):
            prev_level, _ = headings[i-1]
            curr_level, _ = headings[i]
            
            # Skipping levels (e.g., H2 to H4)
            if curr_level > prev_level and curr_level - prev_level > 1:
                hierarchy_violations += 1
        
        # Calculate score based on violations
        violation_ratio = hierarchy_violations / len(headings)
        hierarchy_score = max(0, 1 - violation_ratio)
        
        return hierarchy_score
    
    def _detect_faq_sections(self, soup: BeautifulSoup) -> List[Dict]:
        """Detect FAQ sections in content"""
        faq_sections = []
        
        # Method 1: Look for FAQ schema
        schema_scripts = soup.find_all('script', type='application/ld+json')
        for script in schema_scripts:
            try:
                schema_data = json.loads(script.string)
                if self._is_faq_schema(schema_data):
                    faq_sections.append({
                        "type": "schema",
                        "questions": self._extract_faq_questions(schema_data),
                        "quality": "high"
                    })
            except:
                continue
        
        # Method 2: Look for FAQ patterns in HTML structure
        # Common pattern: dt/dd pairs
        dl_elements = soup.find_all('dl')
        for dl in dl_elements:
            questions = []
            dt_elements = dl.find_all('dt')
            dd_elements = dl.find_all('dd')
            
            if len(dt_elements) > 1 and len(dt_elements) == len(dd_elements):
                for dt, dd in zip(dt_elements, dd_elements):
                    questions.append({
                        "question": dt.get_text().strip(),
                        "answer": dd.get_text().strip()
                    })
                
                if questions:
                    faq_sections.append({
                        "type": "dl_list",
                        "questions": questions,
                        "quality": "medium"
                    })
        
        # Method 3: Look for heading patterns (e.g., "Q:" followed by "A:")
        q_headings = soup.find_all(['h2', 'h3', 'h4', 'h5', 'h6', 'strong'], 
                                  string=lambda s: s and re.match(r'^Q[:.)]|Question|FAQ', s, re.I))
        
        for q_heading in q_headings:
            question_text = q_heading.get_text().strip()
            
            # Try to find the answer (next sibling or next element)
            answer_element = q_heading.find_next(['p', 'div'])
            if answer_element:
                answer_text = answer_element.get_text().strip()
                
                # Check if it looks like an answer
                if answer_text and len(answer_text) > 15:
                    faq_sections.append({
                        "type": "heading_pattern",
                        "questions": [{
                            "question": re.sub(r'^Q[:.)]|\s*', '', question_text).strip(),
                            "answer": answer_text
                        }],
                        "quality": "low"
                    })
        
        return faq_sections
    
    def _is_faq_schema(self, schema_data: Any) -> bool:
        """Check if schema data is FAQ schema"""
        if isinstance(schema_data, dict):
            # Direct FAQPage type
            if schema_data.get('@type') == 'FAQPage':
                return True
            
            # Check for mainEntity with FAQPage
            if schema_data.get('@type') == 'WebPage' and 'mainEntity' in schema_data:
                main_entity = schema_data['mainEntity']
                if isinstance(main_entity, dict) and main_entity.get('@type') == 'FAQPage':
                    return True
            
            # Check in graph
            if '@graph' in schema_data and isinstance(schema_data['@graph'], list):
                for item in schema_data['@graph']:
                    if isinstance(item, dict) and item.get('@type') == 'FAQPage':
                        return True
        
        return False
    
    def _extract_faq_questions(self, schema_data: Any) -> List[Dict]:
        """Extract FAQ questions from schema data"""
        questions = []
        
        def process_faq_item(item):
            if isinstance(item, dict) and item.get('@type') == 'Question':
                question = item.get('name', '')
                answer = ''
                
                # Extract answer text
                answer_obj = item.get('acceptedAnswer', {})
                if isinstance(answer_obj, dict):
                    answer = answer_obj.get('text', '')
                
                if question and answer:
                    questions.append({
                        "question": question,
                        "answer": answer
                    })
        
        if isinstance(schema_data, dict):
            # Direct FAQPage with mainEntity
            if schema_data.get('@type') == 'FAQPage' and 'mainEntity' in schema_data:
                main_entity = schema_data['mainEntity']
                if isinstance(main_entity, list):
                    for item in main_entity:
                        process_faq_item(item)
                else:
                    process_faq_item(main_entity)
            
            # Check in graph
            if '@graph' in schema_data and isinstance(schema_data['@graph'], list):
                for item in schema_data['@graph']:
                    if isinstance(item, dict) and item.get('@type') == 'FAQPage' and 'mainEntity' in item:
                        main_entity = item['mainEntity']
                        if isinstance(main_entity, list):
                            for q_item in main_entity:
                                process_faq_item(q_item)
                        else:
                            process_faq_item(main_entity)
        
        return questions
    
    def _calculate_readability(self, text: str) -> Dict:
        """Calculate readability metrics for text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Count words
        words = text.split()
        word_count = len(words)
        
        # Count syllables (approximation)
        syllable_count = 0
        for word in words:
            syllable_count += self._count_syllables(word)
        
        # Calculate metrics
        if not sentences or not words:
            return {
                "flesch_kincaid_grade": 0,
                "avg_sentence_length": 0,
                "avg_word_length": 0,
                "avg_syllables_per_word": 0
            }
        
        avg_sentence_length = word_count / len(sentences)
        avg_word_length = sum(len(word) for word in words) / word_count
        avg_syllables_per_word = syllable_count / word_count
        
        # Flesch-Kincaid Grade Level
        flesch_kincaid_grade = 0.39 * avg_sentence_length + 11.8 * avg_syllables_per_word - 15.59
        
        return {
            "flesch_kincaid_grade": round(flesch_kincaid_grade, 1),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "avg_word_length": round(avg_word_length, 1),
            "avg_syllables_per_word": round(avg_syllables_per_word, 1)
        }
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (approximation)"""
        word = word.lower()
        
        # Remove non-alphabetic characters
        word = re.sub(r'[^a-z]', '', word)
        
        if not word:
            return 0
        
        # Count vowel groups
        vowels = "aeiouy"
        count = 0
        prev_is_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_is_vowel:
                count += 1
            prev_is_vowel = is_vowel
        
        # Adjust for silent 'e' at end
        if word.endswith('e') and len(word) > 2 and word[-2] not in vowels:
            count -= 1
        
        # Ensure at least one syllable
        return max(1, count)
    
    def _analyze_keyword_density(self, text: str) -> Dict[str, Any]:
        """Analyze keyword density in content"""
        # Remove extra whitespace and convert to lowercase
        text = re.sub(r'\s+', ' ', text).strip().lower()
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 
            'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'this', 'that', 'these', 'those', 'it', 'its', 'from', 'as'
        }
        
        # Split into words and remove stop words
        words = [word for word in re.findall(r'\b\w+\b', text) if word not in stop_words]
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            if len(word) > 2:  # Ignore very short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        top_keywords = sorted_keywords[:10]
        
        # Calculate density
        total_words = len(words)
        keyword_density = {
            word: {
                'count': count,
                'density': round((count / total_words) * 100, 2) if total_words else 0
            }
            for word, count in top_keywords
        }
        
        return {
            "top_keywords": keyword_density,
            "total_words": total_words,
            "unique_words": len(word_freq)
        }
    
    def _analyze_technical_factors(self, soup: BeautifulSoup, domain: str, response: requests.Response) -> Dict:
        """Analyze technical factors affecting LLM visibility"""
        technical_factors = {
            "page_size_kb": len(response.content) / 1024,
            "load_time_ms": response.elapsed.total_seconds() * 1000,
            "ssl_enabled": domain.startswith('https://'),
            "mobile_friendly": self._check_mobile_friendly(soup),
            "structured_data_valid": True,  # Assume valid unless errors found
            "has_sitemap": False,  # Will check below
            "has_robots_txt": False,  # Will check below
            "internal_links": 0,
            "external_links": 0,
            "broken_links": []
        }
        
        # Check for sitemap
        try:
            sitemap_url = urljoin(domain, '/sitemap.xml')
            sitemap_response = self.session.head(sitemap_url, timeout=5)
            technical_factors["has_sitemap"] = sitemap_response.status_code == 200
        except:
            pass
        
        # Check for robots.txt
        try:
            robots_url = urljoin(domain, '/robots.txt')
            robots_response = self.session.head(robots_url, timeout=5)
            technical_factors["has_robots_txt"] = robots_response.status_code == 200
        except:
            pass
        
        # Count internal and external links
        base_domain = urlparse(domain).netloc
        links = soup.find_all('a', href=True)
        
        internal_links = 0
        external_links = 0
        
        for link in links:
            href = link['href']
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
                
            try:
                parsed_url = urlparse(href)
                if not parsed_url.netloc or parsed_url.netloc == base_domain:
                    internal_links += 1
                else:
                    external_links += 1
            except:
                continue
        
        technical_factors["internal_links"] = internal_links
        technical_factors["external_links"] = external_links
        
        return technical_factors
    
    def _check_mobile_friendly(self, soup: BeautifulSoup) -> bool:
        """Check if page appears mobile-friendly"""
        # Check for viewport meta tag
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        if not viewport or 'width=device-width' not in viewport.get('content', ''):
            return False
        
        # Check for responsive design indicators
        media_queries = soup.find_all('style')
        for style in media_queries:
            if style.string and '@media' in style.string:
                return True
        
        # Check for media attributes in link tags
        responsive_css = soup.find_all('link', attrs={'rel': 'stylesheet', 'media': True})
        for css in responsive_css:
            if 'screen' in css.get('media', ''):
                return True
        
        # Default to True if viewport is set
        return viewport is not None
    
    def _calculate_schema_score(self, schema_analysis: Dict) -> int:
        """Calculate Schema.org score (0-100)"""
        score = 0
        
        # Basic schema presence (30 points)
        if schema_analysis["found"]:
            score += 15
            
            # Additional points for multiple schemas
            if schema_analysis["count"] >= 3:
                score += 15
            elif schema_analysis["count"] == 2:
                score += 10
            else:
                score += 5
        
        # High-value schemas (40 points)
        high_value = schema_analysis["high_value_schemas"]
        if high_value["organization"]:
            score += 10
        if high_value["product"]:
            score += 10
        if high_value["faq"]:
            score += 10
        if high_value["breadcrumb"]:
            score += 5
        if high_value["article"]:
            score += 5
        
        # Schema property richness (30 points)
        property_count = schema_analysis["property_count"]
        if property_count >= 20:
            score += 30
        elif property_count >= 15:
            score += 25
        elif property_count >= 10:
            score += 20
        elif property_count >= 5:
            score += 10
        elif property_count > 0:
            score += 5
        
        return min(score, 100)
    
    def _calculate_meta_score(self, meta_analysis: Dict) -> int:
        """Calculate meta tags score (0-100)"""
        score = 0
        
        # Basic meta tags (50 points)
        basic_completeness = meta_analysis["completeness"]["basic"]
        score += int(basic_completeness * 50)
        
        # Social meta tags (30 points)
        social_completeness = meta_analysis["completeness"]["social"]
        score += int(social_completeness * 30)
        
        # Title quality (10 points)
        if meta_analysis["title"]:
            title_length = meta_analysis["title_length"]
            if 50 <= title_length <= 60:
                score += 10
            elif 40 <= title_length <= 70:
                score += 7
            elif 30 <= title_length <= 80:
                score += 5
            else:
                score += 2
        
        # Description quality (10 points)
        if meta_analysis["description"]:
            desc_length = meta_analysis["description_length"]
            if 140 <= desc_length <= 160:
                score += 10
            elif 120 <= desc_length <= 180:
                score += 7
            elif 100 <= desc_length <= 200:
                score += 5
            else:
                score += 2
        
        return min(score, 100)
    
    def _calculate_content_score(self, content_analysis: Dict) -> int:
        """Calculate content structure score (0-100)"""
        score = 0
        
        # Heading structure (25 points)
        if content_analysis["headings"]["h1"] > 0:
            score += 10
            
            # Heading hierarchy
            hierarchy_score = content_analysis["heading_hierarchy_score"]
            score += int(hierarchy_score * 15)
        
        # Content length (20 points)
        word_count = content_analysis["word_count"]
        if word_count >= 1500:
            score += 20
        elif word_count >= 1000:
            score += 15
        elif word_count >= 500:
            score += 10
        elif word_count >= 300:
            score += 5
        
        # Lists and structured content (20 points)
        if content_analysis["lists"] >= 3:
            score += 10
        elif content_analysis["lists"] > 0:
            score += 5
        
        if content_analysis["list_items"] >= 10:
            score += 5
        elif content_analysis["list_items"] > 0:
            score += 2
        
        if content_analysis["tables"] > 0:
            score += 5
        
        # FAQ sections (20 points)
        faq_count = content_analysis["faq_count"]
        if faq_count >= 3:
            score += 20
        elif faq_count == 2:
            score += 15
        elif faq_count == 1:
            score += 10
        
        # Image optimization (10 points)
        images = content_analysis["images"]
        images_with_alt = content_analysis["images_with_alt"]
        
        if images > 0:
            alt_ratio = images_with_alt / images
            score += int(alt_ratio * 10)
        
        # Readability (5 points)
        readability = content_analysis["readability_score"]
        if 6 <= readability["flesch_kincaid_grade"] <= 10:
            score += 5
        elif 5 <= readability["flesch_kincaid_grade"] <= 12:
            score += 3
        
        return min(score, 100)
    
    def _calculate_technical_score(self, technical_analysis: Dict) -> int:
        """Calculate technical factors score (0-100)"""
        score = 0
        
        # SSL enabled (20 points)
        if technical_analysis["ssl_enabled"]:
            score += 20
        
        # Mobile friendly (20 points)
        if technical_analysis["mobile_friendly"]:
            score += 20
        
        # Page size and load time (20 points)
        page_size_kb = technical_analysis["page_size_kb"]
        load_time_ms = technical_analysis["load_time_ms"]
        
        # Size score (10 points)
        if page_size_kb <= 500:
            score += 10
        elif page_size_kb <= 1000:
            score += 7
        elif page_size_kb <= 2000:
            score += 5
        elif page_size_kb <= 3000:
            score += 2
        
        # Load time score (10 points)
        if load_time_ms <= 500:
            score += 10
        elif load_time_ms <= 1000:
            score += 7
        elif load_time_ms <= 2000:
            score += 5
        elif load_time_ms <= 3000:
            score += 2
        
        # Sitemap and robots.txt (20 points)
        if technical_analysis["has_sitemap"]:
            score += 10
        if technical_analysis["has_robots_txt"]:
            score += 10
        
        # Link structure (20 points)
        internal_links = technical_analysis["internal_links"]
        external_links = technical_analysis["external_links"]
        
        # Internal links score (10 points)
        if internal_links >= 20:
            score += 10
        elif internal_links >= 10:
            score += 7
        elif internal_links >= 5:
            score += 5
        elif internal_links > 0:
            score += 2
        
        # External links score (10 points)
        if external_links >= 5:
            score += 10
        elif external_links >= 3:
            score += 7
        elif external_links >= 1:
            score += 5
        
        return min(score, 100)
    
    def _calculate_overall_score(self, schema_score: int, meta_score: int, 
                               content_score: int, technical_score: int) -> int:
        """
        Calculate overall LLM-friendly score (0-100)
        
        Uses a weighted average of component scores with weights determined
        through research on LLM training data sources and visibility factors.
        
        The methodology prioritizes:
        1. Structured data (Schema.org) - Highest weight as it provides explicit semantics
        2. Content structure - Second highest as it affects understanding and context
        3. Meta tags - Important for classification and summarization
        4. Technical factors - Baseline requirements for accessibility
        """
        # Weighted average of component scores
        # Schema and content have higher weights as they're more important for LLMs
        weights = {
            "schema": 0.35,  # Schema.org is critical for LLM understanding
            "content": 0.30,  # Content structure affects context comprehension
            "meta": 0.25,    # Meta tags help with classification
            "technical": 0.10  # Technical factors affect accessibility
        }
        
        # Calculate weighted score
        weighted_score = (
            schema_score * weights["schema"] +
            meta_score * weights["meta"] +
            content_score * weights["content"] +
            technical_score * weights["technical"]
        )
        
        # Apply bonus for exceptional combinations
        bonus = 0
        
        # Bonus for high schema + high content (synergistic effect)
        if schema_score >= 80 and content_score >= 80:
            bonus += 5
        
        # Bonus for balanced optimization across all areas
        if all(score >= 70 for score in [schema_score, meta_score, content_score, technical_score]):
            bonus += 3
        
        # Bonus for perfect meta tags with good schema
        if meta_score >= 90 and schema_score >= 70:
            bonus += 2
        
        # Apply bonus (capped at 100)
        final_score = min(100, weighted_score + bonus)
        
        return round(final_score)
    
    def _generate_recommendations(self, audit_results: Dict) -> List[Dict]:
        """
        Generate actionable recommendations with implementation priority
        
        Creates a prioritized list of recommendations based on audit results,
        focusing on the most impactful improvements for LLM visibility.
        Each recommendation includes:
        - Priority level (high/medium/low)
        - Category (schema/meta/content/technical)
        - Issue description
        - Recommendation summary
        - Implementation guidance
        """
        recommendations = []
        
        # Schema recommendations
        schema_org = audit_results["schema_org"]
        if not schema_org["found"]:
            recommendations.append({
                "priority": "high",
                "category": "schema",
                "issue": "No Schema.org markup found",
                "recommendation": "Implement JSON-LD Schema.org markup for your organization and main content types",
                "implementation": "Add a JSON-LD script with Organization schema to your homepage with essential properties like name, url, logo, and description"
            })
        else:
            high_value = schema_org["high_value_schemas"]
            
            # Check for schema quality score if available
            schema_quality = schema_org.get("quality_score", 0)
            if schema_quality < 50 and schema_org["found"]:
                recommendations.append({
                    "priority": "high",
                    "category": "schema",
                    "issue": "Low quality Schema.org implementation",
                    "recommendation": "Enhance existing Schema.org markup with more properties and better structure",
                    "implementation": "Add missing properties to your schemas and ensure proper nesting of entities"
                })
            
            if not high_value["organization"]:
                recommendations.append({
                    "priority": "high",
                    "category": "schema",
                    "issue": "Missing Organization schema",
                    "recommendation": "Add Organization or LocalBusiness schema to improve entity recognition in LLMs",
                    "implementation": "Implement JSON-LD with your organization details including name, logo, url, description, and sameAs links to social profiles"
                })
            
            if not high_value["product"] and not high_value["article"] and not high_value.get("howto", False):
                recommendations.append({
                    "priority": "medium",
                    "category": "schema",
                    "issue": "Missing content type schemas",
                    "recommendation": "Add appropriate schemas for your main content (Product, Article, HowTo, etc.)",
                    "implementation": "Identify your primary content type and implement the corresponding Schema.org type with all required properties"
                })
            
            if not high_value["faq"] and audit_results["content_structure"].get("faq_count", 0) == 0:
                recommendations.append({
                    "priority": "medium",
                    "category": "schema",
                    "issue": "No FAQ content or schema",
                    "recommendation": "Add an FAQ section with FAQPage schema to improve LLM visibility and question answering",
                    "implementation": "Create a list of common questions and answers about your products/services with FAQPage schema markup"
                })
                
            # Check for schema completeness if available
            completeness = schema_org.get("completeness", {})
            for schema_type, score in completeness.items():
                if score < 0.7:  # Less than 70% complete
                    recommendations.append({
                        "priority": "medium",
                        "category": "schema",
                        "issue": f"Incomplete {schema_type} schema properties",
                        "recommendation": f"Add missing properties to your {schema_type} schema",
                        "implementation": f"Enhance your {schema_type} schema with additional properties like description, image, and relevant dates"
                    })
                    break  # Only add one recommendation for incomplete schemas
        
        # Meta tag recommendations
        meta_tags = audit_results["meta_tags"]
        
        if not meta_tags["title"]:
            recommendations.append({
                "priority": "high",
                "category": "meta",
                "issue": "Missing title tag",
                "recommendation": "Add a descriptive title tag (50-65 characters) for better LLM understanding",
                "implementation": "Create a title that includes your brand name, primary keyword, and value proposition"
            })
        elif meta_tags["title_length"] < 30 or meta_tags["title_length"] > 70:
            recommendations.append({
                "priority": "medium",
                "category": "meta",
                "issue": f"Suboptimal title length ({meta_tags['title_length']} characters)",
                "recommendation": "Adjust title length to 50-65 characters for optimal LLM visibility",
                "implementation": "Revise your title to be more descriptive and keyword-rich while staying within the recommended length"
            })
            
        # Check title format and structure
        if meta_tags["title"] and not re.search(r'\s[\|\-\–\—]\s', meta_tags["title"]):
            recommendations.append({
                "priority": "low",
                "category": "meta",
                "issue": "Title lacks proper structure",
                "recommendation": "Format title with brand name separator (e.g., 'Primary Keyword | Brand Name')",
                "implementation": "Restructure your title to follow the pattern 'Primary Content | Brand Name' for better LLM recognition"
            })
        
        if not meta_tags["description"]:
            recommendations.append({
                "priority": "high",
                "category": "meta",
                "issue": "Missing meta description",
                "recommendation": "Add a descriptive meta description (140-170 characters) for LLM context understanding",
                "implementation": "Write a compelling description that summarizes your page content with relevant keywords and a call to action"
            })
        elif meta_tags["description_length"] < 100 or meta_tags["description_length"] > 180:
            recommendations.append({
                "priority": "medium",
                "category": "meta",
                "issue": f"Suboptimal description length ({meta_tags['description_length']} characters)",
                "recommendation": "Adjust description length to 140-170 characters for optimal LLM visibility",
                "implementation": "Revise your description to be more informative and keyword-rich while staying within the recommended length"
            })
        
        # Check description quality
        if meta_tags["description"] and len(meta_tags["description"].split()) < 15:
            recommendations.append({
                "priority": "medium",
                "category": "meta",
                "issue": "Low-quality meta description",
                "recommendation": "Improve meta description with more context and keywords",
                "implementation": "Enhance your description with specific details about your content, benefits, and relevant keywords"
            })
        
        # Open Graph recommendations
        if not meta_tags["og_tags"]:
            recommendations.append({
                "priority": "medium",
                "category": "meta",
                "issue": "Missing Open Graph tags",
                "recommendation": "Add Open Graph meta tags for better social sharing and LLM context",
                "implementation": "Implement og:title, og:description, og:image, og:url, and og:type tags"
            })
        elif "og:image" not in meta_tags["og_tags"]:
            recommendations.append({
                "priority": "medium",
                "category": "meta",
                "issue": "Missing og:image tag",
                "recommendation": "Add og:image tag for visual representation in LLM training data",
                "implementation": "Add an og:image tag with a high-quality, relevant image (minimum 1200x630 pixels)"
            })
        
        # Content structure recommendations
        content = audit_results["content_structure"]
        
        if content["headings"]["h1"] == 0:
            recommendations.append({
                "priority": "high",
                "category": "content",
                "issue": "Missing H1 heading",
                "recommendation": "Add a single H1 heading that clearly describes your page content for LLM understanding",
                "implementation": "Create an H1 tag that includes your primary keyword and matches your title tag intent"
            })
        
        if content["heading_hierarchy_score"] < 0.7:
            recommendations.append({
                "priority": "medium",
                "category": "content",
                "issue": "Poor heading hierarchy",
                "recommendation": "Improve heading structure with proper H1-H6 hierarchy for better LLM content parsing",
                "implementation": "Ensure headings follow a logical structure without skipping levels (e.g., H1 → H2 → H3)"
            })
        
        if content["word_count"] < 300:
            recommendations.append({
                "priority": "high",
                "category": "content",
                "issue": "Insufficient content length",
                "recommendation": "Expand content to at least 500-800 words for better LLM visibility and context",
                "implementation": "Add more comprehensive information about your topic, addressing common questions and including relevant keywords"
            })
        
        if content["lists"] == 0:
            recommendations.append({
                "priority": "medium",
                "category": "content",
                "issue": "No list elements found",
                "recommendation": "Add bulleted or numbered lists to improve content structure for LLM parsing",
                "implementation": "Convert appropriate content sections into lists for better readability and structured data extraction by LLMs"
            })
            
        # Check for content diversity
        if "content_diversity_score" in content and content["content_diversity_score"] < 0.5:
            recommendations.append({
                "priority": "medium",
                "category": "content",
                "issue": "Low content diversity",
                "recommendation": "Add more diverse content elements for better LLM understanding",
                "implementation": "Include a mix of paragraphs, lists, tables, images with alt text, and quotes to create richer content"
            })
            
        # Check for semantic HTML elements
        if "semantic_elements" in content and len(content.get("semantic_elements", {})) < 3:
            recommendations.append({
                "priority": "medium",
                "category": "content",
                "issue": "Limited use of semantic HTML elements",
                "recommendation": "Add semantic HTML5 elements to improve content structure for LLMs",
                "implementation": "Use elements like <article>, <section>, <figure>, <figcaption>, and <aside> to better organize content"
            })
        
        if content["faq_count"] == 0:
            recommendations.append({
                "priority": "medium",
                "category": "content",
                "issue": "No FAQ sections found",
                "recommendation": "Add an FAQ section to improve LLM visibility and question answering capabilities",
                "implementation": "Create a list of 5-10 common questions and detailed answers about your products/services, using proper HTML structure (dl/dt/dd or h3+p patterns)"
            })
        
        # Check for entity mentions
        if "entity_mentions" in content:
            entities = content.get("entity_mentions", {})
            if not entities.get("organizations") and not entities.get("products"):
                recommendations.append({
                    "priority": "low",
                    "category": "content",
                    "issue": "Limited entity mentions",
                    "recommendation": "Include more named entities in your content for better LLM context",
                    "implementation": "Mention specific organizations, products, people, or locations relevant to your content"
                })
        
        if content["images"] > 0 and content["images_with_alt"] / content["images"] < 0.5:
            recommendations.append({
                "priority": "medium",
                "category": "content",
                "issue": "Images missing alt text",
                "recommendation": "Add descriptive alt text to all images for LLM context understanding",
                "implementation": "Write concise, descriptive alt text that explains the image content, context, and relevance to the topic"
            })
            
        # Check for structured patterns
        if "structured_patterns" in content:
            patterns = content.get("structured_patterns", {})
            if not patterns:
                recommendations.append({
                    "priority": "medium",
                    "category": "content",
                    "issue": "Limited structured content patterns",
                    "recommendation": "Add more structured content patterns for better LLM parsing",
                    "implementation": "Include definition lists, tables with headers, blockquotes, or code samples where appropriate"
                })
        
        # Technical recommendations
        technical = audit_results["technical_factors"]
        
        if not technical["ssl_enabled"]:
            recommendations.append({
                "priority": "high",
                "category": "technical",
                "issue": "SSL not enabled",
                "recommendation": "Enable HTTPS for your website to improve LLM trust signals",
                "implementation": "Install an SSL certificate and configure your server to use HTTPS, which is a key trust signal for LLMs"
            })
        
        if not technical["mobile_friendly"]:
            recommendations.append({
                "priority": "high",
                "category": "technical",
                "issue": "Not mobile-friendly",
                "recommendation": "Implement responsive design for mobile devices to improve LLM visibility",
                "implementation": "Add viewport meta tag and ensure your CSS supports responsive layouts, as mobile-friendliness is a key quality signal for LLMs"
            })
        
        if technical["page_size_kb"] > 2000:
            recommendations.append({
                "priority": "medium",
                "category": "technical",
                "issue": f"Large page size ({technical['page_size_kb']:.1f} KB)",
                "recommendation": "Optimize page size for faster loading and better LLM processing",
                "implementation": "Compress images, minify CSS/JS, and remove unnecessary resources to improve page performance"
            })
        
        if not technical.get("has_sitemap", False):
            recommendations.append({
                "priority": "medium",
                "category": "technical",
                "issue": "No sitemap.xml found",
                "recommendation": "Add a sitemap.xml file for better indexing and LLM discovery",
                "implementation": "Generate a sitemap.xml file listing all important pages on your site with priority and change frequency"
            })
            
        if not technical.get("structured_data_valid", True):
            recommendations.append({
                "priority": "high",
                "category": "technical",
                "issue": "Invalid structured data",
                "recommendation": "Fix structured data validation errors for better LLM understanding",
                "implementation": "Use Schema.org's validator or Google's Structured Data Testing Tool to identify and fix errors"
            })
            
        if technical.get("load_time_ms", 0) > 3000:
            recommendations.append({
                "priority": "medium",
                "category": "technical",
                "issue": "Slow page load time",
                "recommendation": "Improve page speed for better user experience and LLM crawling",
                "implementation": "Optimize server response time, enable caching, and reduce render-blocking resources"
            })
        
        # Sort recommendations by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order[x["priority"]])
        
        return recommendations
        """
        Extract the main content area of the page
        
        Attempts to identify the main content section by looking for
        semantic HTML5 elements and content density patterns.
        """
        # Try to find main content using semantic HTML5 elements
        main_candidates = []
        
        # Check for <main> element
        main_element = soup.find('main')
        if main_element:
            main_candidates.append((main_element, 10))  # High priority
        
        # Check for <article> elements
        article_elements = soup.find_all('article')
        for article in article_elements:
            main_candidates.append((article, 8))
        
        # Check for content divs with common IDs/classes
        content_selectors = [
            'div#content', 'div#main', 'div#main-content', 
            'div.content', 'div.main', 'div.main-content',
            'div#post', 'div.post', 'div#entry', 'div.entry'
        ]
        
        for selector in content_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    main_candidates.append((element, 6))
            except:
                continue
        
        # If no candidates found, look for the div with most content
        if not main_candidates:
            divs = soup.find_all('div')
            for div in divs:
                # Skip very small divs
                if len(div.get_text(strip=True)) < 200:
                    continue
                
                # Calculate content density (text / total HTML)
                text_length = len(div.get_text(strip=True))
                html_length = len(str(div))
                if html_length > 0:
                    density = text_length / html_length
                    # Only consider divs with reasonable density
                    if density > 0.2:
                        main_candidates.append((div, density * 5))
        
        # Return the best candidate or the original soup if none found
        if main_candidates:
            main_candidates.sort(key=lambda x: x[1], reverse=True)
            return main_candidates[0][0]
        
        return soup
    
    def _analyze_semantic_elements(self, soup: BeautifulSoup) -> Dict[str, int]:
        """
        Analyze semantic HTML5 elements
        
        Counts semantic HTML5 elements that improve content structure
        and help LLMs understand the page organization.
        """
        semantic_elements = [
            'header', 'footer', 'main', 'article', 'section', 
            'nav', 'aside', 'figure', 'figcaption', 'time',
            'mark', 'details', 'summary'
        ]
        
        counts = {}
        for element in semantic_elements:
            count = len(soup.find_all(element))
            if count > 0:
                counts[element] = count
        
        return counts
    
    def _detect_structured_patterns(self, soup: BeautifulSoup) -> Dict[str, int]:
        """
        Detect structured content patterns
        
        Identifies common content patterns that are valuable for LLMs:
        - Definition lists
        - Blockquotes
        - Code blocks
        - Tables with headers
        - Figures with captions
        - Accordions/expandable sections
        """
        patterns = {}
        
        # Definition lists
        dl_elements = soup.find_all('dl')
        if dl_elements:
            patterns['definition_lists'] = len(dl_elements)
            dt_elements = soup.find_all('dt')
            dd_elements = soup.find_all('dd')
            patterns['definition_terms'] = len(dt_elements)
            patterns['definition_descriptions'] = len(dd_elements)
        
        # Blockquotes
        blockquotes = soup.find_all('blockquote')
        if blockquotes:
            patterns['blockquotes'] = len(blockquotes)
        
        # Code blocks
        code_blocks = soup.find_all(['pre', 'code'])
        if code_blocks:
            patterns['code_blocks'] = len(code_blocks)
        
        # Tables with headers
        tables_with_headers = 0
        for table in soup.find_all('table'):
            if table.find('th'):
                tables_with_headers += 1
        if tables_with_headers:
            patterns['tables_with_headers'] = tables_with_headers
        
        # Figures with captions
        figures = soup.find_all('figure')
        figures_with_captions = sum(1 for fig in figures if fig.find('figcaption'))
        if figures_with_captions:
            patterns['figures_with_captions'] = figures_with_captions
        
        # Accordions/expandable sections
        details_elements = soup.find_all('details')
        if details_elements:
            patterns['expandable_sections'] = len(details_elements)
        
        # Other common accordion patterns
        accordion_selectors = ['.accordion', '.collapse', '.expandable', '[data-toggle="collapse"]']
        for selector in accordion_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    patterns['accordion_elements'] = len(elements)
                    break
            except:
                continue
        
        return patterns
    
    def _calculate_content_diversity(self, headings: Dict[str, int], paragraph_count: int,
                                    list_count: int, table_count: int, faq_count: int,
                                    image_count: int, semantic_elements: Dict[str, int]) -> float:
        """
        Calculate content diversity score (0-1)
        
        Measures how diverse and rich the content structure is,
        which correlates with higher LLM visibility.
        """
        # Base score components
        components = []
        
        # Heading diversity (0-0.2)
        heading_types = sum(1 for h, count in headings.items() if count > 0)
        heading_score = min(0.2, heading_types * 0.04)
        components.append(heading_score)
        
        # Paragraph density (0-0.15)
        paragraph_score = min(0.15, paragraph_count / 50 * 0.15)
        components.append(paragraph_score)
        
        # List presence (0-0.15)
        list_score = min(0.15, list_count / 5 * 0.15)
        components.append(list_score)
        
        # Table presence (0-0.1)
        table_score = min(0.1, table_count / 2 * 0.1)
        components.append(table_score)
        
        # FAQ presence (0-0.15)
        faq_score = min(0.15, faq_count / 3 * 0.15)
        components.append(faq_score)
        
        # Image presence (0-0.1)
        image_score = min(0.1, image_count / 10 * 0.1)
        components.append(image_score)
        
        # Semantic HTML usage (0-0.15)
        semantic_count = sum(semantic_elements.values())
        semantic_score = min(0.15, semantic_count / 10 * 0.15)
        components.append(semantic_score)
        
        # Calculate total score
        return sum(components)
    
    def _analyze_entity_mentions(self, text: str) -> Dict[str, List[str]]:
        """
        Analyze entity mentions in content
        
        Uses simple pattern matching to detect potential named entities:
        - People (capitalized names)
        - Organizations (capitalized multi-word names)
        - Locations (known location patterns)
        - Products (capitalized names with potential model numbers)
        
        Note: This is a simplified approach without NLP libraries
        """
        entities = {
            "people": [],
            "organizations": [],
            "locations": [],
            "products": []
        }
        
        # Simple cleanup
        text = re.sub(r'\s+', ' ', text)
        
        # People detection (simplified)
        # Look for Title Case Names
        name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        potential_names = re.findall(name_pattern, text)
        # Filter common false positives
        common_phrases = {'New York', 'United States', 'Home Page', 'Privacy Policy'}
        entities["people"] = [name for name in potential_names[:10] if name not in common_phrases]
        
        # Organization detection (simplified)
        # Look for Inc, LLC, Ltd, Corp patterns
        org_pattern = r'\b[A-Z][A-Za-z0-9\s]+\s+(?:Inc|LLC|Ltd|Corp|Corporation|Company)\b'
        entities["organizations"] = re.findall(org_pattern, text)[:10]
        
        # Location detection (simplified)
        # Common location patterns
        location_patterns = [
            r'\b[A-Z][a-z]+,\s+[A-Z]{2}\b',  # City, State
            r'\b[A-Z][a-z]+,\s+[A-Z][a-z]+\b'  # City, Country
        ]
        locations = []
        for pattern in location_patterns:
            locations.extend(re.findall(pattern, text))
        entities["locations"] = locations[:10]
        
        # Product detection (simplified)
        # Look for product model patterns
        product_pattern = r'\b[A-Z][a-z]+\s+(?:[A-Z0-9]{1,4}-[A-Z0-9]{1,4}|[A-Z0-9]{3,10})\b'
        entities["products"] = re.findall(product_pattern, text)[:10]
        
        return entities