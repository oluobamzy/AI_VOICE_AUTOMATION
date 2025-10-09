# -*- coding: utf-8 -*-
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
    
    # Check environment configuration
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        api_key_configured = hasattr(settings, 'OPENAI_API_KEY') and bool(getattr(settings, 'OPENAI_API_KEY', None))
        print("OpenAI API key configured:", "YES" if api_key_configured else "NO")
        
        if not api_key_configured:
            print("Note: Set OPENAI_API_KEY environment variable for full functionality")
        
    except Exception as e:
        print("X Configuration error:", e)
        return False
    
    return True


def test_transcription_service_init():
    """Test transcription service initialization."""
    print("\nTesting transcription service initialization...")
    
    try:
        from app.services.ai.transcription import TranscriptionService
        
        # This will fail without API key, but we can test basic initialization
        service = TranscriptionService()
        print("* TranscriptionService initialized")
        
        # Test supported languages
        assert hasattr(service, 'supported_languages')
        assert 'en' in service.supported_languages
        assert 'es' in service.supported_languages
        print("* Supported languages loaded ({} languages)".format(len(service.supported_languages)))
        
        # Test configuration
        assert hasattr(service, 'max_file_size')
        assert service.max_file_size > 0
        print("* File size limit configured: {}MB".format(service.max_file_size // (1024*1024)))
        
        return True
        
    except Exception as e:
        print("X TranscriptionService initialization failed:", e)
        return False


def test_audio_processor_init():
    """Test audio processor initialization."""
    print("\nTesting audio processor initialization...")
    
    try:
        from app.utils.audio_utils import AudioProcessor
        
        processor = AudioProcessor()
        print("* AudioProcessor initialized")
        
        # Test supported formats
        assert hasattr(processor, 'supported_video_formats')
        assert hasattr(processor, 'supported_audio_formats')
        assert '.mp4' in processor.supported_video_formats
        assert '.wav' in processor.supported_audio_formats
        print("* Supported formats configured")
        
        # Test temp directory
        assert hasattr(processor, 'temp_dir')
        print("* Temp directory configured: {}".format(processor.temp_dir))
        
        return True
        
    except Exception as e:
        print("X AudioProcessor initialization failed:", e)
        return False


async def test_basic_functionality():
    """Test basic functionality without requiring external APIs."""
    print("\nTesting basic functionality...")
    
    try:
        from app.services.ai.transcription import TranscriptionService
        
        service = TranscriptionService()
        
        # Test parameter validation
        try:
            await service._validate_transcription_params("invalid_lang", "whisper-1", 0.5, "json")
            print("X Should have failed for invalid language")
            return False
        except Exception:
            print("* Parameter validation working")
        
        # Test confidence calculation
        test_segments = [
            {"confidence": 0.9, "text": "Hello world"},
            {"confidence": 0.8, "text": "This is a test"}
        ]
        confidence = service._calculate_overall_confidence(test_segments)
        assert 0.8 <= confidence <= 0.9
        print("* Confidence calculation working: {}".format(confidence))
        
        return True
        
    except Exception as e:
        print("X Basic functionality test failed:", e)
        return False


def main():
    """Run all tests."""
    print("Running Transcription Service Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_transcription_service_init,
        test_audio_processor_init,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print("X Test {} crashed: {}".format(test.__name__, e))
    
    # Run async test
    try:
        result = asyncio.run(test_basic_functionality())
        if result:
            passed += 1
        total += 1
    except Exception as e:
        print("X Async test crashed: {}".format(e))
        total += 1
    
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

import sys
import os

# Add the project root to Python path
sys.path.append('/home/labber/AI_VOICE_AUTOMATION')

def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")
    
    try:
        from app.core.config import get_settings
        print("Config import successful")
        
        settings = get_settings()
        api_key_configured = bool(settings.OPENAI_API_KEY)
        print("OpenAI API key configured: {}".format(api_key_configured))
        
        if not api_key_configured:
            print("Warning: Set OPENAI_API_KEY environment variable to test transcription")
        
        return True
        
    except ImportError as e:
        print("Import failed: {}".format(e))
        return False
    except Exception as e:
        print("Configuration error: {}".format(e))
        return False

def test_service_creation():
    """Test creating the transcription service."""
    print("Testing service creation...")
    
    try:
        from app.services.ai.transcription import TranscriptionService
        from app.utils.audio_utils import AudioProcessor
        
        service = TranscriptionService()
        processor = AudioProcessor()
        
        print("TranscriptionService created successfully")
        print("AudioProcessor created successfully")
        
        # Test configuration
        supported_langs = len(service.supported_languages)
        max_size_mb = service.max_file_size / (1024 * 1024)
        
        print("Supported languages: {}".format(supported_langs))
        print("Max file size: {:.1f} MB".format(max_size_mb))
        
        return True
        
    except Exception as e:
        print("Service creation failed: {}".format(e))
        return False

def main():
    """Run basic tests."""
    print("AI Transcription Service - Basic Tests")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test service creation
        services_ok = test_service_creation()
        
        if services_ok:
            print("\nAll basic tests passed!")
            print("\nTo test actual transcription:")
            print("   1. Set OPENAI_API_KEY environment variable")
            print("   2. Place test audio file as /tmp/test_audio.wav")
            print("   3. Run advanced transcription tests")
        else:
            print("\nService creation failed")
    else:
        print("\nImport tests failed")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()

import sys
import os

# Add the project root to Python path
sys.path.append('/home/labber/AI_VOICE_AUTOMATION')

def test_imports():
    """Test that all required imports work."""
    print("🔍 Testing imports...")
    
    try:
        from app.core.config import get_settings
        print("✅ Config import successful")
        
        settings = get_settings()
        api_key_configured = bool(settings.OPENAI_API_KEY)
        print(f"� OpenAI API key configured: {'✅' if api_key_configured else '❌'}")
        
        if not api_key_configured:
            print("⚠️  Set OPENAI_API_KEY environment variable to test transcription")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_service_creation():
    """Test creating the transcription service."""
    print("\n🏗️ Testing service creation...")
    
    try:
        from app.services.ai.transcription import TranscriptionService
        from app.utils.audio_utils import AudioProcessor
        
        service = TranscriptionService()
        processor = AudioProcessor()
        
        print("✅ TranscriptionService created successfully")
        print("✅ AudioProcessor created successfully")
        
        # Test configuration
        supported_langs = len(service.supported_languages)
        max_size_mb = service.max_file_size / (1024 * 1024)
        
        print(f"🌍 Supported languages: {supported_langs}")
        print(f"📏 Max file size: {max_size_mb:.1f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Service creation failed: {e}")
        return False

def main():
    """Run basic tests."""
    print("🚀 AI Transcription Service - Basic Tests")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test service creation
        services_ok = test_service_creation()
        
        if services_ok:
            print("\n✅ All basic tests passed!")
            print("\n📝 To test actual transcription:")
            print("   1. Set OPENAI_API_KEY environment variable")
            print("   2. Place test audio file as /tmp/test_audio.wav")
            print("   3. Run advanced transcription tests")
        else:
            print("\n❌ Service creation failed")
    else:
        print("\n❌ Import tests failed")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    main()