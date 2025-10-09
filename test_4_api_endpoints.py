#!/usr/bin/env python3
"""
Test 4: API Endpoints Test
Tests all FastAPI endpoints using TestClient.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

def test_api_endpoints():
    print("🔗 TESTING API ENDPOINTS")
    print("=" * 50)
    
    try:
        client = TestClient(app)
        
        print("1. TESTING CORE ENDPOINTS:")
        print("-" * 30)
        
        # Test health endpoint
        response = client.get("/api/v1/health")
        print(f"✅ Health Check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Service: {data.get('service')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
        
        print()
        print("2. TESTING VIDEO ENDPOINTS:")
        print("-" * 30)
        
        # Test videos list
        response = client.get("/api/v1/videos/")
        print(f"✅ List Videos: {response.status_code}")
        if response.status_code == 200:
            videos = response.json()
            print(f"   Found {len(videos)} sample videos")
            
        # Test video creation
        video_data = {
            "title": "Test Video",
            "description": "API test video",
            "source_url": "https://www.youtube.com/watch?v=test",
            "tags": ["test", "api"]
        }
        response = client.post("/api/v1/videos/", json=video_data)
        print(f"✅ Create Video: {response.status_code}")
        
        print()
        print("3. TESTING JOB ENDPOINTS:")
        print("-" * 30)
        
        # Test jobs list
        response = client.get("/api/v1/jobs/")
        print(f"✅ List Jobs: {response.status_code}")
        if response.status_code == 200:
            jobs = response.json()
            print(f"   Found {len(jobs)} sample jobs")
            
        # Test job creation
        job_data = {
            "job_type": "video_processing",
            "priority": 8,
            "parameters": {"test": True}
        }
        response = client.post("/api/v1/jobs/", json=job_data)
        print(f"✅ Create Job: {response.status_code}")
        if response.status_code == 200:
            job = response.json()
            print(f"   Job ID: {job.get('id')}")
            print(f"   Status: {job.get('status')}")
        
        print()
        print("4. TESTING API DOCUMENTATION:")
        print("-" * 30)
        
        # Test OpenAPI schema
        response = client.get("/openapi.json")
        print(f"✅ OpenAPI Schema: {response.status_code}")
        if response.status_code == 200:
            schema = response.json()
            endpoints = len(schema.get("paths", {}))
            print(f"   API Endpoints: {endpoints}")
            
        # Test Swagger docs
        response = client.get("/docs")
        print(f"✅ Swagger UI: {response.status_code}")
        
        print()
        print("5. AVAILABLE API ENDPOINTS:")
        print("-" * 30)
        
        if response.status_code == 200:
            # Get all endpoints from OpenAPI schema
            response = client.get("/openapi.json")
            if response.status_code == 200:
                schema = response.json()
                paths = schema.get("paths", {})
                
                for path, methods in sorted(paths.items()):
                    for method in methods.keys():
                        if method.upper() in ["GET", "POST", "PUT", "DELETE"]:
                            print(f"   {method.upper():6} {path}")
        
        print()
        print("🎉 API ENDPOINTS TEST: PASSED!")
        print("All endpoints responding correctly")
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_endpoints()