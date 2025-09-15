#!/usr/bin/env python3
"""
Test script specifically for the version_check module.

This script tests the version_check module functions directly
without importing the main django_cfg package.
"""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_version_check_utilities():
    """Test version_check utility functions."""
    print("🧪 Testing version_check module utilities...")
    
    try:
        from django_cfg.version_check import (
            is_python_compatible,
            get_python_version_string
        )
        
        # Test utility functions
        version_str = get_python_version_string()
        is_compatible = is_python_compatible()
        
        print(f"   📋 Version string: {version_str}")
        print(f"   📋 Is compatible: {is_compatible}")
        
        # Verify version string format
        parts = version_str.split('.')
        if len(parts) == 3 and all(part.isdigit() for part in parts):
            print("✅ PASS: get_python_version_string() returns valid format")
        else:
            print(f"❌ FAIL: Invalid version string format: {version_str}")
            return False
        
        # Verify compatibility check
        expected_compatible = sys.version_info >= (3, 12)
        if is_compatible == expected_compatible:
            print("✅ PASS: is_python_compatible() returns correct result")
        else:
            print(f"❌ FAIL: is_python_compatible() returned {is_compatible}, expected {expected_compatible}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Error testing version_check module: {e}")
        return False


def test_version_check_function():
    """Test version_check function behavior."""
    print("\n🧪 Testing check_python_version function...")
    
    try:
        from django_cfg.version_check import check_python_version
        
        if sys.version_info >= (3, 12):
            # Should not raise exception
            try:
                check_python_version("test-context")
                print("✅ PASS: check_python_version() passed for Python 3.12+")
                return True
            except SystemExit:
                print("❌ FAIL: check_python_version() should not exit for Python 3.12+")
                return False
        else:
            # Should raise SystemExit
            try:
                check_python_version("test-context")
                print("❌ FAIL: check_python_version() should exit for Python < 3.12")
                return False
            except SystemExit:
                print("✅ PASS: check_python_version() correctly exits for Python < 3.12")
                return True
        
    except Exception as e:
        print(f"❌ FAIL: Error testing check_python_version: {e}")
        return False


def main():
    """Run version_check module tests."""
    print(f"🐍 Current Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print("📋 Testing version_check module directly")
    print("=" * 70)
    
    tests = [
        test_version_check_utilities,
        test_version_check_function,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except SystemExit:
            # Expected for Python < 3.12 in test_version_check_function
            if sys.version_info < (3, 12) and test == test_version_check_function:
                print("✅ PASS: check_python_version() correctly exits for Python < 3.12")
                passed += 1
            else:
                print("❌ FAIL: Unexpected SystemExit")
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Version checking module works correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
