#!/usr/bin/env python3
"""
Test script for Celery task queue system.

This script tests various Celery tasks to ensure the queue system
is working correctly.
"""

import asyncio
import time
from typing import Dict, Any

from app.tasks.celery_app import celery_app, debug_task
from app.tasks.video_tasks import health_check_task
from app.tasks.task_monitor import task_monitor, task_manager
from app.core.logging import get_logger

logger = get_logger(__name__)


def test_celery_connection():
    """Test basic Celery connection."""
    try:
        logger.info("Testing Celery connection...")
        
        # Check if Redis is available
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            logger.info("✅ Celery connection successful")
            logger.info(f"Active workers: {list(stats.keys())}")
            return True
        else:
            logger.error("❌ No active workers found")
            return False
            
    except Exception as exc:
        logger.error(f"❌ Celery connection failed: {exc}")
        return False


def test_basic_task():
    """Test basic task execution."""
    try:
        logger.info("Testing basic task execution...")
        
        # Submit debug task
        result = debug_task.delay()
        logger.info(f"Task submitted: {result.id}")
        
        # Wait for completion
        task_result = result.get(timeout=30)
        logger.info(f"✅ Task completed: {task_result}")
        
        return True
        
    except Exception as exc:
        logger.error(f"❌ Basic task test failed: {exc}")
        return False


def test_health_check():
    """Test health check task."""
    try:
        logger.info("Testing health check task...")
        
        result = health_check_task.delay()
        task_result = result.get(timeout=30)
        
        if task_result.get("status") == "healthy":
            logger.info("✅ Health check passed")
            return True
        else:
            logger.error(f"❌ Health check failed: {task_result}")
            return False
            
    except Exception as exc:
        logger.error(f"❌ Health check test failed: {exc}")
        return False


def test_task_monitoring():
    """Test task monitoring functionality."""
    try:
        logger.info("Testing task monitoring...")
        
        # Submit a task to monitor
        result = debug_task.delay()
        task_id = result.id
        
        # Test task status monitoring
        status = task_monitor.get_task_status(task_id)
        logger.info(f"Task status: {status['status']}")
        
        # Wait for completion and check again
        result.get(timeout=30)
        final_status = task_monitor.get_task_status(task_id)
        
        if final_status['status'] == 'SUCCESS':
            logger.info("✅ Task monitoring working correctly")
            return True
        else:
            logger.error(f"❌ Task monitoring failed: {final_status}")
            return False
            
    except Exception as exc:
        logger.error(f"❌ Task monitoring test failed: {exc}")
        return False


def test_queue_status():
    """Test queue status monitoring."""
    try:
        logger.info("Testing queue status monitoring...")
        
        queue_status = task_monitor.get_queue_status()
        
        if 'queues' in queue_status:
            logger.info("✅ Queue status monitoring working")
            logger.info(f"Available queues: {list(queue_status['queues'].keys())}")
            logger.info(f"Total active tasks: {queue_status['total_tasks']['active']}")
            return True
        else:
            logger.error(f"❌ Queue status monitoring failed: {queue_status}")
            return False
            
    except Exception as exc:
        logger.error(f"❌ Queue status test failed: {exc}")
        return False


def test_worker_stats():
    """Test worker statistics."""
    try:
        logger.info("Testing worker statistics...")
        
        worker_stats = task_monitor.get_worker_stats()
        
        if 'workers' in worker_stats:
            logger.info("✅ Worker statistics working")
            logger.info(f"Active workers: {len(worker_stats['workers'])}")
            for worker_name in worker_stats['workers'].keys():
                logger.info(f"  - {worker_name}")
            return True
        else:
            logger.error(f"❌ Worker statistics failed: {worker_stats}")
            return False
            
    except Exception as exc:
        logger.error(f"❌ Worker statistics test failed: {exc}")
        return False


def run_all_tests():
    """Run all Celery tests."""
    logger.info("🚀 Starting Celery task queue tests...")
    
    tests = [
        ("Connection Test", test_celery_connection),
        ("Basic Task Test", test_basic_task),
        ("Health Check Test", test_health_check),
        ("Task Monitoring Test", test_task_monitoring),
        ("Queue Status Test", test_queue_status),
        ("Worker Stats Test", test_worker_stats)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            results[test_name] = test_func()
        except Exception as exc:
            logger.error(f"Test {test_name} crashed: {exc}")
            results[test_name] = False
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("TEST SUMMARY")
    logger.info("="*50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Celery task queue is working correctly.")
        return True
    else:
        logger.error("⚠️  Some tests failed. Check the logs above for details.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)