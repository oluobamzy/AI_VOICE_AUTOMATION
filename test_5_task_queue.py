#!/usr/bin/env python3
"""
Test 5: Celery Task Queue Test
Tests Redis connection and Celery task creation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import redis
from celery import Celery
from app.core.config import settings

def test_task_queue():
    print("⚡ TESTING CELERY TASK QUEUE SYSTEM")
    print("=" * 50)
    
    try:
        print("1. TESTING REDIS CONNECTION:")
        print("-" * 30)
        
        # Test Redis connection
        r = redis.Redis.from_url(settings.REDIS_URL)
        ping_result = r.ping()
        print(f"✅ Redis ping: {ping_result}")
        
        # Test Redis operations
        r.set("test_key", "celery_working")
        value = r.get("test_key")
        print(f"✅ Redis set/get: {value.decode()}")
        
        # Test Redis info
        info = r.info()
        print(f"✅ Redis version: {info.get('redis_version')}")
        print(f"✅ Connected clients: {info.get('connected_clients')}")
        
        r.delete("test_key")
        
        print()
        print("2. TESTING CELERY CONFIGURATION:")
        print("-" * 30)
        
        # Create test Celery app
        test_app = Celery(
            'test_pipeline',
            broker=settings.CELERY_BROKER_URL,
            backend=settings.CELERY_RESULT_BACKEND
        )
        
        print(f"✅ Celery app: {test_app.main}")
        print(f"✅ Broker: {test_app.conf.broker_url}")
        print(f"✅ Backend: {test_app.conf.result_backend}")
        
        print()
        print("3. TESTING TASK DEFINITION:")
        print("-" * 30)
        
        # Define test tasks
        @test_app.task
        def process_video(video_url, options=None):
            """Mock video processing task."""
            return {
                "status": "completed",
                "url": video_url,
                "processed_at": "2025-10-09T00:00:00Z",
                "options": options or {}
            }
        
        @test_app.task
        def transcribe_audio(audio_file, language="en"):
            """Mock audio transcription task."""
            return {
                "status": "transcribed",
                "file": audio_file,
                "language": language,
                "text": "This is a mock transcription result.",
                "confidence": 0.95
            }
        
        print("✅ Tasks defined:")
        print("   - process_video(url, options)")
        print("   - transcribe_audio(file, language)")
        
        print()
        print("4. TESTING TASK QUEUING:")
        print("-" * 30)
        
        # Test task delay (queuing)
        video_task = process_video.delay(
            "https://www.youtube.com/watch?v=test",
            {"quality": "high", "format": "mp4"}
        )
        print(f"✅ Video task queued: {video_task.id}")
        
        audio_task = transcribe_audio.delay(
            "/tmp/audio.mp3",
            "en"
        )
        print(f"✅ Audio task queued: {audio_task.id}")
        
        print()
        print("5. TESTING TASK STATUS:")
        print("-" * 30)
        
        print(f"✅ Video task state: {video_task.state}")
        print(f"✅ Audio task state: {audio_task.state}")
        
        # Tasks won't execute without worker, but they're queued
        print("✅ Tasks successfully queued in Redis")
        print("   (Would execute when worker is running)")
        
        print()
        print("6. CONFIGURATION VALUES:")
        print("-" * 30)
        
        print(f"✅ Redis URL: {settings.REDIS_URL}")
        print(f"✅ Broker URL: {settings.CELERY_BROKER_URL}")
        print(f"✅ Result backend: {settings.CELERY_RESULT_BACKEND}")
        
        print()
        print("🎉 TASK QUEUE TEST: PASSED!")
        print("Redis and Celery are configured and operational")
        
        print()
        print("TO START A WORKER:")
        print("-" * 30)
        print("celery -A app.tasks.celery_app worker --loglevel=info")
        
    except Exception as e:
        print(f"❌ Task queue test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_task_queue()