import pytest
import asyncio
from httpx import AsyncClient
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_create_video(client: AsyncClient):
    """Test video creation endpoint"""
    video_data = {
        "title": "Test Video",
        "description": "A test video",
        "source_url": "https://example.com/video.mp4",
        "platform": "tiktok",
        "tags": ["test", "video"]
    }
    
    response = await client.post("/api/v1/videos/", json=video_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Video"
    assert data["platform"] == "tiktok"


@pytest.mark.asyncio
async def test_list_videos(client: AsyncClient):
    """Test video listing endpoint"""
    response = await client.get("/api/v1/videos/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)