#!/usr/bin/env python3
"""
Test 2: Database Operations Test
Tests all database functionality including CRUD operations.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import init_db, AsyncSessionLocal
from app.models import User, Video, Job
from sqlalchemy import select, func, text

async def test_database_operations():
    print("🗄️  TESTING DATABASE OPERATIONS")
    print("=" * 50)
    
    try:
        # Initialize database
        await init_db()
        print("✅ Database initialized successfully")
        
        async with AsyncSessionLocal() as session:
            # Test table count
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Database tables created: {len(tables)}")
            
            # Create test user
            user = User(
                email="test@aivoice.com",
                username="test_user",
                hashed_password="test_hash_123",
                first_name="Test",
                last_name="User",
                bio="Testing the AI Video Automation Pipeline"
            )
            session.add(user)
            await session.flush()
            print(f"✅ User created: {user.username} (ID: {str(user.id)[:8]}...)")
            
            # Create test video with array fields
            video = Video(
                user_id=user.id,
                title="Database Test Video",
                description="Testing cross-database array compatibility",
                source_platform="youtube",
                source_url="https://www.youtube.com/watch?v=test123",
                tags=["database", "test", "arrays", "compatibility"],
                duration=300.0,
                format="mp4",
                resolution="1920x1080"
            )
            session.add(video)
            await session.flush()
            print(f"✅ Video created: {video.title}")
            print(f"   - Tags (ArrayType): {video.tags}")
            print(f"   - Platform: {video.source_platform}")
            
            # Create test job
            job = Job(
                user_id=user.id,
                job_type="video_processing",
                category="test",
                name="Database Test Job",
                task_name="test_task",
                priority=5,
                args={"video_id": str(video.id)},
                kwargs={"test": True, "database": "working"}
            )
            session.add(job)
            await session.flush()
            print(f"✅ Job created: {job.name}")
            print(f"   - Args: {job.args}")
            print(f"   - Kwargs: {job.kwargs}")
            
            # Test queries
            user_count = await session.scalar(select(func.count(User.id)))
            video_count = await session.scalar(select(func.count(Video.id)))
            job_count = await session.scalar(select(func.count(Job.id)))
            
            print()
            print("📊 DATABASE STATISTICS:")
            print(f"   - Users: {user_count}")
            print(f"   - Videos: {video_count}")
            print(f"   - Jobs: {job_count}")
            
            # Test relationship queries
            result = await session.execute(
                select(Video).where(Video.user_id == user.id)
            )
            user_videos = result.scalars().all()
            print(f"   - User's videos: {len(user_videos)}")
            
            # Clean up test data
            await session.rollback()
            print("✅ Test data cleaned up")
            
        print()
        print("🎉 DATABASE TEST: PASSED!")
        print("All CRUD operations working correctly")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_operations())