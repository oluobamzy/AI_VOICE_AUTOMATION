#!/usr/bin/env python3
"""
Test script to verify all dependencies are installed correctly.
"""

import sys
import importlib

def test_import(module_name):
    """Test if a module can be imported successfully."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - ERROR: {e}")
        return False

def main():
    """Test all critical dependencies."""
    print("Testing AI Video Automation Dependencies...")
    print("=" * 50)
    
    critical_modules = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'asyncpg',
        'alembic',
        'pydantic', 
        'celery',
        'redis',
        'httpx',
        'aiohttp',
        'openai',
        'elevenlabs',
        'boto3',
        'google.cloud.storage',
        'yt_dlp',
        'ffmpeg',
    ]
    
    dev_modules = [
        'pytest',
        'black',
        'isort',
        'mypy',
        'ipython',
        'jupyter',
    ]
    
    # Test critical modules
    print("\nCritical Dependencies:")
    critical_success = 0
    for module in critical_modules:
        if test_import(module):
            critical_success += 1
    
    # Test dev modules
    print("\nDevelopment Dependencies:")
    dev_success = 0
    for module in dev_modules:
        if test_import(module):
            dev_success += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Critical Dependencies: {critical_success}/{len(critical_modules)} ✅")
    print(f"Development Dependencies: {dev_success}/{len(dev_modules)} ✅")
    
    if critical_success == len(critical_modules):
        print("\n🎉 All critical dependencies installed successfully!")
        print("You can now proceed with running the AI Video Automation pipeline.")
        return 0
    else:
        print(f"\n⚠️  Missing {len(critical_modules) - critical_success} critical dependencies.")
        return 1

if __name__ == "__main__":
    sys.exit(main())