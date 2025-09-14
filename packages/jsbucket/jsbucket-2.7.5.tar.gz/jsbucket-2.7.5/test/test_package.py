#!/usr/bin/env python3
"""
Test script to verify JSBucket package functionality after refactoring.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jsbucket import (
    analyze_subdomain_for_s3_buckets,
    analyze_multiple_subdomains,
    extract_s3_buckets,
    get_html_content,
    extract_js_urls
)

def test_extract_s3_buckets():
    """Test S3 bucket extraction from content."""
    print("Testing S3 bucket extraction...")
    
    test_cases = [
        # Standard S3 URL
        (b"bucket-name.s3.amazonaws.com", ["bucket-name"]),
        # S3 with region
        (b"my-bucket.s3.us-west-2.amazonaws.com", ["my-bucket"]),
        # S3 path style
        (b"s3.amazonaws.com/path-bucket", ["path-bucket"]),
        # Multiple buckets
        (b"bucket1.s3.amazonaws.com and bucket2.s3.eu-west-1.amazonaws.com", ["bucket1", "bucket2"]),
        # No buckets
        (b"just regular text", []),
    ]
    
    for content, expected in test_cases:
        result = extract_s3_buckets(content)
        result_set = set(result)
        expected_set = set(expected)
        
        if result_set == expected_set:
            print(f"✅ PASS: {content.decode()[:30]}... -> {result}")
        else:
            print(f"❌ FAIL: {content.decode()[:30]}... -> Expected {expected}, got {result}")
    
    print()

def test_get_html_content():
    """Test HTML content fetching."""
    print("Testing HTML content fetching...")
    
    # Test with a reliable service
    content = get_html_content("https://httpbin.org/html", timeout=10)
    if content and len(content) > 0:
        print(f"✅ PASS: Retrieved {len(content)} bytes from httpbin.org")
    else:
        print("❌ FAIL: Could not retrieve content from httpbin.org")
    
    # Test with invalid URL
    content = get_html_content("https://this-domain-should-not-exist-123456.com", timeout=2)
    if content is None:
        print("✅ PASS: Correctly returned None for invalid URL")
    else:
        print("❌ FAIL: Should have returned None for invalid URL")
    
    print()

def test_extract_js_urls():
    """Test JavaScript URL extraction."""
    print("Testing JavaScript URL extraction...")
    
    html_content = b'''
    <html>
        <head>
            <script src="/js/app.js"></script>
            <script src="https://cdn.example.com/lib.js"></script>
            <script src="relative/path.js"></script>
        </head>
    </html>
    '''
    
    js_urls = extract_js_urls(html_content, "https://example.com")
    expected_count = 3
    
    if len(js_urls) == expected_count:
        print(f"✅ PASS: Found {len(js_urls)} JavaScript URLs")
        for url in js_urls:
            print(f"  - {url}")
    else:
        print(f"❌ FAIL: Expected {expected_count} URLs, got {len(js_urls)}")
        print(f"  URLs: {js_urls}")
    
    print()

def test_analyze_subdomain_api():
    """Test the main API function."""
    print("Testing subdomain analysis API...")
    
    # Test with a real domain (should not find S3 buckets but should succeed)
    result = analyze_subdomain_for_s3_buckets("httpbin.org", timeout=10)
    
    required_keys = ["subdomain", "s3_buckets", "success"]
    if all(key in result for key in required_keys):
        print(f"✅ PASS: API returned correct structure")
        print(f"  Subdomain: {result['subdomain']}")
        print(f"  Success: {result['success']}")
        print(f"  Buckets found: {len(result['s3_buckets'])}")
    else:
        print(f"❌ FAIL: API result missing required keys")
        print(f"  Result: {result}")
    
    # Test with invalid domain
    result = analyze_subdomain_for_s3_buckets("invalid-domain-123456.com", timeout=2)
    if not result['success']:
        print("✅ PASS: Correctly handled invalid domain")
    else:
        print("❌ FAIL: Should have failed for invalid domain")
    
    print()

def test_analyze_multiple_subdomains():
    """Test multiple subdomain analysis."""
    print("Testing multiple subdomain analysis...")
    
    subdomains = ["httpbin.org", "invalid-domain-123456.com"]
    results = analyze_multiple_subdomains(subdomains, timeout=5, max_threads=2)
    
    if len(results) == len(subdomains):
        print(f"✅ PASS: Analyzed {len(results)} subdomains")
        for result in results:
            print(f"  {result['subdomain']}: Success = {result['success']}")
    else:
        print(f"❌ FAIL: Expected {len(subdomains)} results, got {len(results)}")
    
    print()

def main():
    """Run all tests."""
    print("JSBucket Package Functionality Tests")
    print("=" * 50)
    print()
    
    test_extract_s3_buckets()
    test_get_html_content()
    test_extract_js_urls()
    test_analyze_subdomain_api()
    test_analyze_multiple_subdomains()
    
    print("=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    main()
