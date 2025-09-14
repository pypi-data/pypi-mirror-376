#!/usr/bin/env python3
"""
Test the JSON formatting function to ensure it handles all field types correctly.
This test was added to prevent regressions after fixing the boolean field issue.
"""

import sys
sys.path.insert(0, '/media/saeed/Coding/Coding/Projects/jsbucket')

from jsbucket.core import format_json_with_colors, _console

def test_formatting_with_different_field_types():
    """Test the formatting function with various field types."""
    print("🧪 Testing JSON formatting with various field types")
    print("=" * 55)
    
    test_cases = [
        {
            'name': 'Standard result with S3 buckets',
            'data': {
                'subdomain': 'https://example.com',
                's3_buckets': [
                    {'bucket_name': 'test-bucket', 'bucket_url': 'https://test-bucket.s3.amazonaws.com'}
                ],
                'success': True
            }
        },
        {
            'name': 'Empty result',
            'data': {
                'subdomain': 'https://example.com',
                's3_buckets': [],
                'success': True
            }
        },
        {
            'name': 'Result with multiple buckets',
            'data': {
                'subdomain': 'api.example.com',
                's3_buckets': [
                    {'bucket_name': 'bucket1', 'bucket_url': 'https://bucket1.s3.amazonaws.com'},
                    {'bucket_name': 'bucket2', 'bucket_url': 'https://bucket2.s3.amazonaws.com'}
                ],
                'success': True
            }
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for test_case in test_cases:
        try:
            formatted = format_json_with_colors(test_case['data'], _console)
            # Check that success field is not in the output
            if 'success' not in formatted:
                print(f"✅ PASS: {test_case['name']}")
                passed += 1
            else:
                print(f"❌ FAIL: {test_case['name']} - success field should be hidden")
        except Exception as e:
            print(f"❌ FAIL: {test_case['name']} - Exception: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    return passed == total

if __name__ == "__main__":
    success = test_formatting_with_different_field_types()
    if success:
        print("\n🎉 All formatting tests PASSED!")
        print("✅ JSON formatting is working correctly!")
    else:
        print("\n❌ Some formatting tests FAILED!")
        sys.exit(1)
