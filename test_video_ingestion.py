#!/usr/bin/env python3
"""
Test script for video ingestion services.

This script tests the comprehensive video ingestion system including
video downloading, URL validation, batch processing, and error handling.
"""

import asyncio
import os
from typing import List, Dict, Any

from app.services.ingest import (
    VideoDownloader,
    VideoIngestionService, 
    URLValidator,
    BatchVideoIngestionService
)
from app.core.logging import get_logger

logger = get_logger(__name__)


# Test URLs for different platforms
TEST_URLS = {
    'tiktok': [
        'https://www.tiktok.com/@username/video/1234567890',
        'https://vm.tiktok.com/test123',
    ],
    'youtube': [
        'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'https://youtu.be/dQw4w9WgXcQ',
        'https://www.youtube.com/shorts/test123',
    ],
    'instagram': [
        'https://www.instagram.com/p/test123/',
        'https://www.instagram.com/reel/test123/',
    ],
    'twitter': [
        'https://twitter.com/username/status/1234567890',
        'https://x.com/username/status/1234567890',
    ]
}

# Invalid URLs for testing validation
INVALID_URLS = [
    'not-a-url',
    'http://',
    'https://unsupported-site.com/video',
    'ftp://invalid-protocol.com',
    'https://malware-site.com/video',
]


async def test_url_validator():
    """Test URL validation functionality."""
    logger.info("🧪 Testing URL validator...")
    
    validator = URLValidator()
    
    # Test valid URLs
    logger.info("Testing valid URLs...")
    for platform, urls in TEST_URLS.items():
        for url in urls:
            try:
                result = await validator.validate_url(url, check_accessibility=False)
                status = "✅ VALID" if result['is_valid'] else "❌ INVALID"
                detected_platform = result.get('platform', 'unknown')
                
                logger.info(f"{status} - {url}")
                logger.info(f"   Platform: {detected_platform} (expected: {platform})")
                
                if result.get('errors'):
                    logger.info(f"   Errors: {result['errors']}")
                if result.get('warnings'):
                    logger.info(f"   Warnings: {result['warnings']}")
                
            except Exception as e:
                logger.error(f"❌ Validation failed for {url}: {e}")
    
    # Test invalid URLs
    logger.info("\\nTesting invalid URLs...")
    for url in INVALID_URLS:
        try:
            result = await validator.validate_url(url, check_accessibility=False)
            status = "✅ INVALID (as expected)" if not result['is_valid'] else "❌ SHOULD BE INVALID"
            
            logger.info(f"{status} - {url}")
            if result.get('errors'):
                logger.info(f"   Errors: {result['errors']}")
                
        except Exception as e:
            logger.error(f"❌ Validation test failed for {url}: {e}")
    
    # Test cache functionality
    logger.info("\\nTesting cache functionality...")
    cache_stats = validator.get_cache_stats()
    logger.info(f"Cache stats: {cache_stats}")


async def test_video_downloader():
    """Test video downloader functionality."""
    logger.info("\\n🧪 Testing video downloader...")
    
    downloader = VideoDownloader()
    
    # Test supported sites
    logger.info("Getting supported sites...")
    try:
        sites = await downloader.get_supported_sites()
        logger.info(f"✅ Supported sites count: {len(sites)}")
        
        # Show some popular sites
        popular_sites = [site for site in sites[:20] if any(platform in site.lower() for platform in ['youtube', 'tiktok', 'instagram', 'twitter'])]
        logger.info(f"Popular supported sites: {popular_sites}")
        
    except Exception as e:
        logger.error(f"❌ Failed to get supported sites: {e}")
    
    # Test URL validation
    logger.info("\\nTesting downloader URL validation...")
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    try:
        is_valid, error = await downloader.validate_url(test_url)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        logger.info(f"{status} - {test_url}")
        if error:
            logger.info(f"   Error: {error}")
            
    except Exception as e:
        logger.error(f"❌ URL validation failed: {e}")
    
    # Test metadata extraction (without downloading)
    logger.info("\\nTesting metadata extraction...")
    try:
        # Use a test URL that should work
        metadata = await downloader.extract_metadata(test_url)
        
        if metadata:
            logger.info("✅ Metadata extraction successful")
            logger.info(f"   Title: {metadata.title}")
            logger.info(f"   Duration: {metadata.duration}s")
            logger.info(f"   Platform: {metadata.platform}")
            logger.info(f"   Resolution: {metadata.resolution}")
        else:
            logger.warning("⚠️  No metadata extracted")
            
    except Exception as e:
        logger.error(f"❌ Metadata extraction failed: {e}")
    
    # Test platform detection
    logger.info("\\nTesting platform detection...")
    for platform, urls in TEST_URLS.items():
        for url in urls:
            detected = downloader.get_platform_from_url(url)
            status = "✅ CORRECT" if detected == platform else f"❌ WRONG (got {detected})"
            logger.info(f"{status} - {url} -> {detected}")


async def test_video_ingestion():
    """Test complete video ingestion pipeline."""
    logger.info("\\n🧪 Testing video ingestion service...")
    
    ingestion_service = VideoIngestionService()
    test_user_id = "test_user_123"
    
    # Test ingestion stats
    logger.info("Getting ingestion stats...")
    try:
        stats = await ingestion_service.get_ingestion_stats()
        logger.info(f"✅ Global stats: {stats}")
        
        user_stats = await ingestion_service.get_ingestion_stats(test_user_id)
        logger.info(f"✅ User stats: {user_stats}")
        
    except Exception as e:
        logger.error(f"❌ Failed to get stats: {e}")
    
    # Test URL validation
    logger.info("\\nTesting ingestion URL validation...")
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    try:
        validation = await ingestion_service.validate_url(test_url)
        status = "✅ VALID" if validation['is_valid'] else "❌ INVALID"
        logger.info(f"{status} - {test_url}")
        logger.info(f"   Platform: {validation.get('platform', 'unknown')}")
        
        if validation.get('error'):
            logger.info(f"   Error: {validation['error']}")
            
    except Exception as e:
        logger.error(f"❌ URL validation failed: {e}")
    
    # Test metadata extraction
    logger.info("\\nTesting metadata extraction...")
    try:
        metadata = await ingestion_service.extract_metadata(test_url)
        
        if metadata:
            logger.info("✅ Metadata extraction successful")
            logger.info(f"   Title: {metadata.title}")
            logger.info(f"   Platform: {metadata.platform}")
        else:
            logger.warning("⚠️  No metadata extracted")
            
    except Exception as e:
        logger.error(f"❌ Metadata extraction failed: {e}")
    
    # Test content validation
    if metadata:
        logger.info("\\nTesting content validation...")
        try:
            validation_options = {
                'min_duration': 1,
                'required_keywords': [],
                'blocked_keywords': []
            }
            
            content_validation = await ingestion_service.validate_content(
                metadata, validation_options
            )
            
            status = "✅ VALID" if content_validation['is_valid'] else "❌ INVALID"
            logger.info(f"{status} - Content validation")
            
            if content_validation.get('error'):
                logger.info(f"   Error: {content_validation['error']}")
                
        except Exception as e:
            logger.error(f"❌ Content validation failed: {e}")
    
    # Test cleanup functionality
    logger.info("\\nTesting cleanup functionality...")
    try:
        cleanup_result = await ingestion_service.cleanup_temp_files(older_than_hours=0)
        logger.info(f"✅ Cleanup result: {cleanup_result}")
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")


async def test_batch_ingestion():
    """Test batch video ingestion functionality."""
    logger.info("\\n🧪 Testing batch ingestion service...")
    
    batch_service = BatchVideoIngestionService(max_concurrent=2)
    test_user_id = "test_user_batch"
    
    # Create a test batch with mix of valid and invalid URLs
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://invalid-url-format",
        "https://www.youtube.com/watch?v=test123",
        "not-a-url-at-all"
    ]
    
    # Test batch job creation
    logger.info("Starting batch ingestion job...")
    try:
        job_id = await batch_service.start_batch_ingestion(
            urls=test_urls,
            user_id=test_user_id,
            options={'quality': 'medium'}
        )
        
        logger.info(f"✅ Batch job started: {job_id}")
        
        # Monitor batch progress
        logger.info("Monitoring batch progress...")
        for i in range(10):  # Monitor for up to 30 seconds
            await asyncio.sleep(3)
            
            status = batch_service.get_batch_status(job_id)
            if status:
                logger.info(
                    f"Progress: {status['progress']}% - "
                    f"Status: {status['status']} - "
                    f"Success: {status['successful_videos']}, "
                    f"Failed: {status['failed_videos']}"
                )
                
                if status['status'] in ['completed', 'failed', 'cancelled']:
                    break
            else:
                logger.warning("Could not get batch status")
                break
        
        # Get final results
        logger.info("\\nGetting batch results...")
        results = batch_service.get_batch_results(job_id, include_details=False)
        if results:
            logger.info(f"✅ Batch results: {results}")
        else:
            logger.warning("Could not get batch results")
        
    except Exception as e:
        logger.error(f"❌ Batch ingestion test failed: {e}")
    
    # Test service stats
    logger.info("\\nGetting service stats...")
    try:
        stats = batch_service.get_service_stats()
        logger.info(f"✅ Service stats: {stats}")
        
    except Exception as e:
        logger.error(f"❌ Failed to get service stats: {e}")
    
    # Test cleanup
    logger.info("\\nTesting batch cleanup...")
    try:
        cleanup_result = batch_service.cleanup_completed_jobs(older_than_hours=0)
        logger.info(f"✅ Cleanup result: {cleanup_result}")
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")


async def test_error_handling():
    """Test error handling scenarios."""
    logger.info("\\n🧪 Testing error handling...")
    
    # Test with completely invalid URLs
    validator = URLValidator()
    downloader = VideoDownloader()
    ingestion_service = VideoIngestionService()
    
    error_test_urls = [
        "",  # Empty string
        "javascript:alert('xss')",  # Malicious URL
        "https://this-domain-should-not-exist-12345.com/video",  # Non-existent domain
        "https://httpbin.org/status/404",  # 404 error
        "https://httpbin.org/status/500",  # 500 error
    ]
    
    for url in error_test_urls:
        logger.info(f"\\nTesting error handling for: {url}")
        
        # Test URL validation
        try:
            result = await validator.validate_url(url)
            logger.info(f"   Validation: {'VALID' if result['is_valid'] else 'INVALID'}")
            if result.get('errors'):
                logger.info(f"   Errors: {result['errors'][:2]}")  # Show first 2 errors
        except Exception as e:
            logger.info(f"   Validation exception: {str(e)[:100]}...")
        
        # Test downloader validation
        try:
            is_valid, error = await downloader.validate_url(url)
            logger.info(f"   Downloader validation: {'VALID' if is_valid else 'INVALID'}")
            if error:
                logger.info(f"   Downloader error: {str(error)[:100]}...")
        except Exception as e:
            logger.info(f"   Downloader exception: {str(e)[:100]}...")


async def run_all_tests():
    """Run all ingestion service tests."""
    logger.info("🚀 Starting comprehensive video ingestion tests...")
    
    tests = [
        ("URL Validator", test_url_validator),
        ("Video Downloader", test_video_downloader),  
        ("Video Ingestion", test_video_ingestion),
        ("Batch Ingestion", test_batch_ingestion),
        ("Error Handling", test_error_handling),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\\n{'='*60}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*60}")
        
        try:
            await test_func()
            results[test_name] = "✅ PASSED"
            logger.info(f"✅ {test_name} completed successfully")
        except Exception as e:
            results[test_name] = f"❌ FAILED: {str(e)}"
            logger.error(f"❌ {test_name} failed: {str(e)}")
    
    # Print summary
    logger.info(f"\\n{'='*60}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    for test_name, result in results.items():
        logger.info(f"{test_name}: {result}")
    
    passed = sum(1 for result in results.values() if result.startswith("✅"))
    total = len(results)
    
    logger.info(f"\\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All video ingestion tests passed!")
        return True
    else:
        logger.error("⚠️  Some tests failed. Check the logs above for details.")
        return False


if __name__ == "__main__":
    # Ensure we're using the right environment
    os.environ.setdefault('ENVIRONMENT', 'development')
    
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)