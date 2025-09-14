#!/usr/bin/env python3
"""
Final integration test to ensure the refactored JSBucket works correctly
both as CLI and as a package.
"""

import subprocess
import sys
import os

def test_cli():
    """Test CLI functionality."""
    print("Testing CLI functionality...")
    
    # Test basic CLI help
    result = subprocess.run([
        sys.executable, "-m", "jsbucket", "--help"
    ], capture_output=True, text=True, cwd="/media/saeed/Coding/Coding/Projects/jsbucket")
    
    if result.returncode == 0 and "Analyze Javascript files" in result.stdout:
        print("✅ CLI help works correctly")
    else:
        print("❌ CLI help failed")
        return False
    
    # Test basic CLI functionality
    result = subprocess.run([
        sys.executable, "-m", "jsbucket", 
        "-u", "httpbin.org", 
        "-d", "httpbin.org", 
        "-silent"
    ], capture_output=True, text=True, cwd="/media/saeed/Coding/Coding/Projects/jsbucket")
    
    if result.returncode == 0 and result.stderr == "":
        print("✅ CLI execution works without warnings")
        return True
    else:
        print(f"❌ CLI execution failed or has warnings: {result.stderr}")
        return False

def test_package():
    """Test package functionality."""
    print("Testing package functionality...")
    
    # Set PYTHONPATH to use local version
    env = os.environ.copy()
    env['PYTHONPATH'] = '/media/saeed/Coding/Coding/Projects/jsbucket'
    
    test_code = '''
import sys
sys.path.insert(0, "/media/saeed/Coding/Coding/Projects/jsbucket")

from jsbucket import analyze_subdomain_for_s3_buckets, extract_s3_buckets

# Test API function
result = analyze_subdomain_for_s3_buckets('httpbin.org', timeout=5)
assert result['success'] == True
assert 'subdomain' in result
assert 's3_buckets' in result
print("✅ API function works correctly")

# Test utility function
test_content = b"var bucket = 'test-bucket.s3.amazonaws.com';"
buckets = extract_s3_buckets(test_content)
assert buckets == ['test-bucket']
print("✅ Utility function works correctly")

print("✅ All package tests passed!")
'''
    
    result = subprocess.run([
        sys.executable, "-c", test_code
    ], capture_output=True, text=True, env=env)
    
    if result.returncode == 0 and "All package tests passed!" in result.stdout:
        print("✅ Package functionality works correctly")
        return True
    else:
        print(f"❌ Package test failed: {result.stderr}")
        print(f"Stdout: {result.stdout}")
        return False

def main():
    """Run all integration tests."""
    print("JSBucket Integration Tests")
    print("=" * 50)
    
    cli_ok = test_cli()
    package_ok = test_package()
    
    print("\n" + "=" * 50)
    if cli_ok and package_ok:
        print("🎉 All integration tests PASSED!")
        print("JSBucket is ready for use as both CLI tool and Python package!")
    else:
        print("❌ Some tests FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()
