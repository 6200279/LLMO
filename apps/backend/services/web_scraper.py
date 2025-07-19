"""
Web scraping service for visibility audits
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import json
from urllib.parse import urljoin, urlparse

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
            response = self.session.get(domain, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            audit_results = {
                "domain": domain,
                "status_code": response.status_code,
                "schema_org": self._check_schema_org(soup),
                "meta_tags": self._analyze_meta_tags(soup),
                "structured_data": self._extract_structured_data(soup),
                "content_analysis": self._analyze_content(soup),
                "llm_friendly_score": 0
            }
            
            # Calculate LLM-friendly score
            audit_results["llm_friendly_score"] = self._calculate_score(audit_results)
            
            return audit_results
            
        except Exception as e:
            return {
                "domain": domain,
                "error": str(e),
                "llm_friendly_score": 0
            }
    
    def _check_schema_org(self, soup: BeautifulSoup) -> Dict:
        """Check for Schema.org structured data"""
        schema_scripts = soup.find_all('script', type='application/ld+json')
        schemas = []
        
        for script in schema_scripts:
            try:
                schema_data = json.loads(script.string)
                schemas.append(schema_data)
            except:
                continue
        
        return {
            "found": len(schemas) > 0,
            "count": len(schemas),
            "schemas": schemas[:3]  # Limit to first 3 for brevity
        }
    
    def _analyze_meta_tags(self, soup: BeautifulSoup) -> Dict:
        """Analyze meta tags for LLM optimization"""
        meta_analysis = {
            "title": soup.find('title').text if soup.find('title') else None,
            "description": None,
            "keywords": None,
            "og_tags": {}
        }
        
        # Meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag:
            meta_analysis["description"] = desc_tag.get('content')
        
        # Meta keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag:
            meta_analysis["keywords"] = keywords_tag.get('content')
        
        # Open Graph tags
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        for tag in og_tags:
            meta_analysis["og_tags"][tag.get('property')] = tag.get('content')
        
        return meta_analysis
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict:
        """Extract various structured data formats"""
        return {
            "microdata": len(soup.find_all(attrs={"itemtype": True})),
            "rdfa": len(soup.find_all(attrs={"typeof": True})),
            "json_ld": len(soup.find_all('script', type='application/ld+json'))
        }
    
    def _analyze_content(self, soup: BeautifulSoup) -> Dict:
        """Analyze content for LLM-friendly elements"""
        headings = {
            f"h{i}": len(soup.find_all(f'h{i}')) for i in range(1, 7)
        }
        
        return {
            "headings": headings,
            "paragraphs": len(soup.find_all('p')),
            "lists": len(soup.find_all(['ul', 'ol'])),
            "word_count": len(soup.get_text().split())
        }
    
    def _calculate_score(self, audit_results: Dict) -> int:
        """Calculate LLM-friendly score (0-100)"""
        score = 0
        
        # Schema.org presence (+30 points)
        if audit_results["schema_org"]["found"]:
            score += 30
        
        # Meta tags (+20 points)
        meta = audit_results["meta_tags"]
        if meta["title"]:
            score += 5
        if meta["description"]:
            score += 10
        if meta["og_tags"]:
            score += 5
        
        # Content structure (+30 points)
        content = audit_results["content_analysis"]
        if content["headings"]["h1"] > 0:
            score += 10
        if content["word_count"] > 300:
            score += 10
        if content["lists"] > 0:
            score += 10
        
        # Structured data variety (+20 points)
        structured = audit_results["structured_data"]
        if structured["json_ld"] > 0:
            score += 15
        if structured["microdata"] > 0:
            score += 5
        
        return min(score, 100)