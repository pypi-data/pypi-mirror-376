"""
JSBucket: S3 Bucket Discovery Tool From JavaScript Files

A Python package for discovering Amazon S3 buckets by analyzing JavaScript files
on subdomains. Designed for security researchers, bug bounty hunters, and pentesters.
"""

from .core import (
    # Core API functions
    analyze_subdomain_for_s3_buckets,
    analyze_multiple_subdomains,
    
    # Utility functions
    extract_s3_buckets,
    get_html_content,
    extract_js_urls,
    
    # Domain detection functions
    extract_base_domain,
    auto_detect_base_domain,
    
    # CLI function
    main,
)

__version__ = "2.7.5"
__author__ = "Mortaza Behesti Al Saeed"
__email__ = "saeed.ctf@gmail.com"
__description__ = "A tool to discover S3 buckets from subdomains by analyzing JavaScript files."

__all__ = [
    # Version info
    '__version__',
    
    # Core API functions
    'analyze_subdomain_for_s3_buckets',
    'analyze_multiple_subdomains',
    
    # Utility functions
    'extract_s3_buckets',
    'get_html_content', 
    'extract_js_urls',
    
    # Domain detection functions
    'extract_base_domain',
    'auto_detect_base_domain',
    
    # CLI function
    'main',
]