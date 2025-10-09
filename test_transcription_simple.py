#!/usr/bin/env python3
"""
Simple test for transcription service functionality.
"""

import os
import sys
import asyncio

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def test_imports():
    """Test that we can import the transcription service modules."""
    print("Testing imports...")
    
    try:
        from app.services.ai.transcription import TranscriptionService
        print("* TranscriptionService imported successfully")
    except ImportError as e:
        print("X Failed to import TranscriptionService:", e)
        return False
    
    try:
        from app.utils.audio_utils import AudioProcessor
        print("* AudioProcessor imported successfully")
    except ImportError as e:
        print("X Failed to import AudioProcessor:", e)
        return False
    
    try:
        from app.core.exceptions import TranscriptionError, AudioProcessingError
        print("* Custom exceptions imported successfully")
    except ImportError as e:
        print("X Failed to import custom exceptions:", e)
        return False
    
    return True


def test_configuration():
    """Test configuration and dependencies."""
    print("\nTesting configuration...")
    
    # Check OpenAI dependency
    try:
        import openai
        print("* OpenAI library available")
    except ImportError:
        print("X OpenAI library not installed")
        return False
    
    # Check ffmpeg dependency
    try:
        import ffmpeg
        print("* ffmpeg-python library available")
    except ImportError:
        print("X ffmpeg-python library not installed")
        return False
    
    return True


def test_transcription_service_init():
    """Test transcription service initialization."""
    print("\nTesting transcription service initialization...")
    
    try:
        from app.services.ai.transcription import TranscriptionService
        
        service = TranscriptionService()
        print("* TranscriptionService initialized")
        
        # Test supported languages
        assert hasattr(service, 'supported_languages')
        assert 'en' in service.supported_languages
        print("* Supported languages loaded")
        
        return True
        
    except Exception as e:
        print("X TranscriptionService initialization failed:", e)
        return False


def main():
    """Run all tests."""
    print("Running Transcription Service Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_transcription_service_init,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print("X Test crashed:", e)
    
    print("\n" + "=" * 50)
    print("Tests completed: {}/{} passed".format(passed, total))
    
    if passed == total:
        print("All tests passed! Transcription service is ready.")
        return 0
    else:
        print("Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit(main())