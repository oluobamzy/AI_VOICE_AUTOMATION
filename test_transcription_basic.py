# -*- coding: utf-8 -*-
"""
Basic test script for AI Transcription Service.
"""

import sys
import os

# Add project root to Python path
sys.path.append('/home/labber/AI_VOICE_AUTOMATION')

def test_imports():
    """Test basic imports."""
    print("Testing imports...")
    
    try:
        from app.core.config import get_settings
        print("SUCCESS: Config import")
        
        settings = get_settings()
        api_key_configured = bool(settings.OPENAI_API_KEY)
        print("OpenAI API key configured: " + str(api_key_configured))
        
        return True
        
    except Exception as e:
        print("FAILED: " + str(e))
        return False

def test_transcription_service():
    """Test transcription service creation."""
    print("Testing transcription service...")
    
    try:
        from app.services.ai.transcription import TranscriptionService
        
        service = TranscriptionService()
        print("SUCCESS: TranscriptionService created")
        
        langs = len(service.supported_languages)
        print("Supported languages: " + str(langs))
        
        return True
        
    except Exception as e:
        print("FAILED: " + str(e))
        return False

def test_audio_processor():
    """Test audio processor creation."""
    print("Testing audio processor...")
    
    try:
        from app.utils.audio_utils import AudioProcessor
        
        processor = AudioProcessor()
        print("SUCCESS: AudioProcessor created")
        
        return True
        
    except Exception as e:
        print("FAILED: " + str(e))
        return False

def main():
    """Main test runner."""
    print("AI Transcription Service - Basic Tests")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Transcription Service", test_transcription_service),
        ("Audio Processor", test_audio_processor)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print("\n" + name + ":")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print("Results: " + str(passed) + "/" + str(total) + " tests passed")
    
    if passed == total:
        print("All tests PASSED!")
    else:
        print("Some tests FAILED!")

if __name__ == "__main__":
    main()