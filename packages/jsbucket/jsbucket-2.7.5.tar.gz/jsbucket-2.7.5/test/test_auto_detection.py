#!/usr/bin/env python3
"""
Test the auto-detection functionality of JSBucket.
"""

import sys
sys.path.insert(0, '/media/saeed/Coding/Coding/Projects/jsbucket')

from jsbucket import extract_base_domain, auto_detect_base_domain

def test_domain_extraction():
    """Test base domain extraction with various inputs."""
    print("🧪 Testing Base Domain Extraction")
    print("=" * 50)
    
    test_cases = [
        # (input, expected_output)
        ('api.example.com', 'example.com'),
        ('www.example.co.uk', 'example.co.uk'), 
        ('https://cdn.test.example.org', 'example.org'),
        ('sub.api.example.com:8080/path', 'example.com'),
        ('simple-domain.com', 'simple-domain.com'),
        ('192.168.1.1', '192.168.1.1'),  # IP address
        ('localhost', 'localhost'),
        ('admin.staging.company.co.uk', 'company.co.uk'),
        ('app.example.com.au', 'example.com.au'),
        ('test', 'test'),  # Single word
    ]
    
    passed = 0
    total = len(test_cases)
    
    for input_domain, expected in test_cases:
        result = extract_base_domain(input_domain)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status}: '{input_domain}' -> '{result}' (expected: '{expected}')")
        if result == expected:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed\n")
    return passed == total

def test_auto_detection():
    """Test automatic base domain detection."""
    print("🔍 Testing Auto-Detection")
    print("=" * 50)
    
    test_cases = [
        # (input_list, expected_output)
        (['api.example.com', 'www.example.com', 'cdn.example.com'], 'example.com'),
        (['app.test.co.uk', 'api.test.co.uk', 'www.test.co.uk'], 'test.co.uk'),
        (['api.example.com', 'www.different.com', 'cdn.example.com'], 'example.com'),  # Most common
        (['192.168.1.1', '192.168.1.2'], '192.168.1.1'),  # IP addresses (first one)
        (['single.domain.com'], 'domain.com'),
        ([], None),  # Empty list
    ]
    
    passed = 0
    total = len(test_cases)
    
    for input_list, expected in test_cases:
        result = auto_detect_base_domain(input_list)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        input_str = str(input_list)[:50] + "..." if len(str(input_list)) > 50 else str(input_list)
        print(f"{status}: {input_str}")
        print(f"      -> '{result}' (expected: '{expected}')")
        if result == expected:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed\n")
    return passed == total

def main():
    """Run all tests."""
    print("JSBucket Auto-Detection Tests")
    print("=" * 60)
    
    test1_passed = test_domain_extraction()
    test2_passed = test_auto_detection()
    
    print("=" * 60)
    if test1_passed and test2_passed:
        print("🎉 All tests PASSED!")
        print("✅ Auto-detection feature is working correctly!")
    else:
        print("❌ Some tests FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()
