"""
Standardized industry prompts for the prompt simulation engine
"""
from typing import List, Dict

# General product recommendation prompts
PRODUCT_RECOMMENDATION_PROMPTS = [
    "What are the best {product_category} available today?",
    "Can you recommend some top {product_category} for someone looking to buy?",
    "I'm researching {product_category}. What options should I consider?",
    "What companies are known for excellent {product_category}?",
    "If I need {product_category}, what are my best options?",
    "What are the most popular {product_category} brands?",
    "I'm looking for high-quality {product_category}. What do you recommend?",
    "What {product_category} would you recommend for a professional?",
    "What are the top-rated {product_category} according to experts?",
    "I need a reliable {product_category}. What should I buy?"
]

# Industry-specific prompts
INDUSTRY_PROMPTS = {
    "software": [
        "What project management software should I use for my team?",
        "What's the best CRM software for a small business?",
        "What software tools do professional developers use?",
        "What's the best software for {specific_task}?",
        "What software would you recommend for a startup?",
        "What are the most user-friendly software options for {specific_task}?",
        "What enterprise-grade software is best for {specific_task}?",
        "What software has the best integration capabilities?",
        "What software offers the best value for money?",
        "What software is considered the industry standard for {specific_task}?"
    ],
    "ecommerce": [
        "What are the best platforms for setting up an online store?",
        "What tools do I need for my ecommerce business?",
        "What's the best shopping cart software for a small business?",
        "What payment processors should I use for my online store?",
        "What are the most reliable shipping solutions for ecommerce?",
        "What ecommerce platforms have the best SEO features?",
        "What's the best way to handle inventory management for an online store?",
        "What ecommerce tools offer the best analytics?",
        "What platforms are best for dropshipping?",
        "What ecommerce solution is best for scaling a business?"
    ],
    "finance": [
        "What are the best accounting software options for small businesses?",
        "What tools should I use for personal financial planning?",
        "What are the most reliable payment processing services?",
        "What's the best software for tax preparation?",
        "What financial tools do professional accountants recommend?",
        "What are the best budgeting apps available?",
        "What investment platforms offer the lowest fees?",
        "What financial software integrates best with banking systems?",
        "What tools should I use for financial forecasting?",
        "What are the most secure financial management solutions?"
    ],
    "marketing": [
        "What are the best email marketing platforms?",
        "What tools should I use for social media management?",
        "What's the best software for content marketing?",
        "What analytics tools do professional marketers use?",
        "What are the most effective SEO tools available?",
        "What marketing automation platforms offer the best features?",
        "What tools should I use for creating marketing videos?",
        "What are the best CRM systems for marketing teams?",
        "What tools are best for influencer marketing campaigns?",
        "What platforms offer the best ROI tracking for marketing?"
    ],
    "healthcare": [
        "What are the best electronic health record (EHR) systems?",
        "What telehealth platforms do doctors recommend?",
        "What software should medical practices use for billing?",
        "What are the most reliable healthcare scheduling systems?",
        "What tools help with HIPAA compliance?",
        "What healthcare analytics platforms offer the best insights?",
        "What patient engagement tools are most effective?",
        "What software is best for managing a medical practice?",
        "What healthcare tools have the best mobile capabilities?",
        "What platforms offer the best integration with medical devices?"
    ]
}

# Comparison prompts
COMPARISON_PROMPTS = [
    "How does {brand_name} compare to {competitor}?",
    "What's better, {brand_name} or {competitor}?",
    "What are the differences between {brand_name} and {competitor}?",
    "Should I choose {brand_name} or {competitor} for {specific_task}?",
    "What are the pros and cons of {brand_name} vs {competitor}?"
]

# Purchase intent prompts
PURCHASE_INTENT_PROMPTS = [
    "I'm thinking about buying {product_category}. What should I know?",
    "What should I look for when purchasing {product_category}?",
    "I'm ready to invest in {product_category}. What's the best choice?",
    "What features are most important when buying {product_category}?",
    "Is now a good time to buy {product_category} or should I wait?"
]

def get_standard_prompts(industry: str = None, product_category: str = None) -> List[str]:
    """
    Get standardized prompts for a specific industry and product category
    
    Args:
        industry: Industry category (software, ecommerce, finance, marketing, healthcare)
        product_category: Product category to substitute in prompts
        
    Returns:
        List of standardized prompts
    """
    prompts = []
    
    # Add general product recommendation prompts
    if product_category:
        for prompt in PRODUCT_RECOMMENDATION_PROMPTS:
            prompts.append(prompt.format(product_category=product_category))
    
    # Add industry-specific prompts
    if industry and industry.lower() in INDUSTRY_PROMPTS:
        industry_prompts = INDUSTRY_PROMPTS[industry.lower()]
        for prompt in industry_prompts:
            if "{specific_task}" in prompt and product_category:
                prompts.append(prompt.format(specific_task=product_category))
            elif "{specific_task}" not in prompt:
                prompts.append(prompt)
    
    # Add purchase intent prompts
    if product_category:
        for prompt in PURCHASE_INTENT_PROMPTS:
            prompts.append(prompt.format(product_category=product_category))
    
    return prompts

def get_comparison_prompts(brand_name: str, competitors: List[str]) -> List[str]:
    """
    Get comparison prompts for a brand and its competitors
    
    Args:
        brand_name: Name of the brand
        competitors: List of competitor brand names
        
    Returns:
        List of comparison prompts
    """
    prompts = []
    
    for competitor in competitors:
        for prompt in COMPARISON_PROMPTS:
            prompts.append(prompt.format(brand_name=brand_name, competitor=competitor))
    
    return prompts