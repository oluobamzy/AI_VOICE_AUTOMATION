import pytest
from app.utils.helpers import (
    generate_unique_filename,
    validate_url,
    sanitize_filename,
    get_file_size_mb
)


def test_generate_unique_filename():
    """Test unique filename generation"""
    filename1 = generate_unique_filename("test.mp4")
    filename2 = generate_unique_filename("test.mp4")
    
    assert filename1 != filename2
    assert filename1.endswith(".mp4")
    assert filename2.endswith(".mp4")


def test_validate_url():
    """Test URL validation"""
    assert validate_url("https://example.com/video.mp4") == True
    assert validate_url("http://localhost:8000/api") == True
    assert validate_url("not-a-url") == False
    assert validate_url("") == False


def test_sanitize_filename():
    """Test filename sanitization"""
    assert sanitize_filename("test<>file.mp4") == "test__file.mp4"
    assert sanitize_filename("valid_filename.mp4") == "valid_filename.mp4"
    assert sanitize_filename("") == "unnamed_file"
    assert sanitize_filename("   ") == "unnamed_file"