#!/usr/bin/env python3
"""
Health check script for the Meli Challenge Docker container.
This script verifies that all required components are available.
"""

import sys
import os
import importlib.util

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        return False
    print("✅ Python version compatible")
    return True

def check_required_packages():
    """Check if required packages are installed."""
    required_packages = [
        'scrapy',
        'boto3',
        'decouple',
        'yaml',
        'scrapy_zyte_api'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'scrapy_zyte_api':
                importlib.import_module('scrapy_zyte_api')
            else:
                importlib.import_module(package)
            print(f"✅ {package} available")
        except ImportError:
            print(f"❌ {package} not available")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_environment_variables():
    """Check if required environment variables are set."""
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'DYNAMODB_TABLE_NAME',
        'SQS_QUEUE_URL',
        'ZYTE_API_KEY'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is not set")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def check_project_structure():
    """Check if project structure is correct."""
    required_files = [
        'meli_crawler/__init__.py',
        'meli_crawler/spiders/__init__.py',
        'meli_crawler/spiders/meli_uy_collect.py',
        'meli_crawler/spiders/meli_uy-identify.py',
        'meli_crawler/pipelines.py',
        'meli_crawler/settings.py',
        'scrapy.cfg'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def main():
    """Run all health checks."""
    print("🏥 Running health checks for Meli Challenge container...")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_required_packages),
        ("Environment Variables", check_environment_variables),
        ("Project Structure", check_project_structure)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}:")
        print("-" * 30)
        try:
            if check_func():
                print(f"✅ {check_name} check passed")
            else:
                print(f"❌ {check_name} check failed")
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} check error: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All health checks passed! Container is healthy.")
        sys.exit(0)
    else:
        print("⚠️  Some health checks failed. Container may not function properly.")
        sys.exit(1)

if __name__ == "__main__":
    main()
