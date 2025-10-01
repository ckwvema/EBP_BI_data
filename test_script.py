#!/usr/bin/env python3
"""
Test script to verify the EBP data ingestion script works correctly.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    try:
        import ingest_ebp_data
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_environment():
    """Test that environment variables are properly configured."""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['EBP_USERNAME', 'EBP_PASSWORD', 'EBP_API_PREFIX', 'EXPORT_BASE_PATH']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_export_directory():
    """Test that export directory exists and is writable."""
    from dotenv import load_dotenv
    load_dotenv()
    
    export_path = os.getenv('EXPORT_BASE_PATH')
    if not export_path:
        print("❌ EXPORT_BASE_PATH not set")
        return False
    
    export_dir = Path(export_path)
    if not export_dir.exists():
        print(f"❌ Export directory does not exist: {export_dir}")
        return False
    
    if not os.access(export_dir, os.W_OK):
        print(f"❌ Export directory is not writable: {export_dir}")
        return False
    
    print("✅ Export directory is accessible and writable")
    return True

def main():
    """Run all tests."""
    print("Running EBP Data Ingestion Script Tests...")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Environment Test", test_environment),
        ("Export Directory Test", test_export_directory)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The script is ready to run.")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues before running the script.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

