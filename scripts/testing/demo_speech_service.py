"""
Demo Script - Test Speech Service Trực Tiếp
============================================
Script này test Speech service mà không cần chạy Flask server.
Dùng để kiểm tra xem Whisper có hoạt động không.

Cách chạy:
    python demo_speech_service.py
"""

import sys
import os

# Thêm src vào path để import được
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.speech_service import speech_service

def test_whisper_installation():
    """
    Test 1: Kiểm tra Whisper đã cài đặt chưa
    """
    print("\n" + "="*60)
    print("TEST 1: Kiểm tra Whisper Installation")
    print("="*60)
    
    try:
        import whisper
        print(f"✓ Whisper version: {whisper.__version__}")
        print(f"✓ Model name: {speech_service.model_name}")
        return True
    except ImportError as e:
        print(f"✗ Whisper chưa được cài đặt: {e}")
        print("  Chạy: pip install openai-whisper")
        return False


def test_load_model():
    """
    Test 2: Thử load Whisper model
    """
    print("\n" + "="*60)
    print("TEST 2: Load Whisper Model")
    print("="*60)
    print("⚠ Lần đầu load model sẽ tải về ~150MB, mất 10-30s...")
    
    try:
        speech_service._load_model()
        print("✓ Model loaded successfully!")
        print(f"✓ Model type: {type(speech_service.model)}")
        return True
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        return False


def test_transcribe_sample():
    """
    Test 3: Thử transcribe một file audio mẫu (nếu có)
    """
    print("\n" + "="*60)
    print("TEST 3: Transcribe Audio Sample")
    print("="*60)
    
    # Tìm file audio mẫu
    sample_files = [
        "test_audio.mp3",
        "test_audio.wav",
        "tests/test_audio.mp3",
        "tests/test_audio.wav"
    ]
    
    audio_file = None
    for f in sample_files:
        if os.path.exists(f):
            audio_file = f
            break
    
    if not audio_file:
        print("⚠ Không tìm thấy file audio mẫu")
        print("  Để test transcription, tạo file:")
        print("  - test_audio.mp3")
        print("  - test_audio.wav")
        return False
    
    print(f"ℹ Testing with: {audio_file}")
    
    try:
        result = speech_service.transcribe_audio(audio_file, language='vi')
        print("✓ Transcription successful!")
        print(f"  Text: {result['text']}")
        print(f"  Language: {result['language']}")
        print(f"  Duration: {result.get('duration', 0):.2f}s")
        return True
    except Exception as e:
        print(f"✗ Transcription failed: {e}")
        return False


def test_file_validation():
    """
    Test 4: Test validation logic
    """
    print("\n" + "="*60)
    print("TEST 4: File Validation")
    print("="*60)
    
    # Tạo mock file object để test
    class MockFile:
        def __init__(self, filename, size):
            self.filename = filename
            self._size = size
            self._position = 0
        
        def seek(self, offset, whence=0):
            if whence == 2:  # SEEK_END
                self._position = self._size
            else:
                self._position = offset
        
        def tell(self):
            return self._position
    
    # Test 1: Valid file
    valid_file = MockFile("test.mp3", 1024 * 1024)  # 1MB
    is_valid, error = speech_service.validate_audio_file(valid_file)
    if is_valid:
        print("✓ Valid file accepted: test.mp3 (1MB)")
    else:
        print(f"✗ Valid file rejected: {error}")
    
    # Test 2: File quá lớn
    large_file = MockFile("large.mp3", 30 * 1024 * 1024)  # 30MB
    is_valid, error = speech_service.validate_audio_file(large_file)
    if not is_valid and "too large" in error.lower():
        print("✓ Large file rejected correctly")
    else:
        print(f"✗ Large file validation failed")
    
    # Test 3: File format không hỗ trợ
    invalid_file = MockFile("test.txt", 1024)
    is_valid, error = speech_service.validate_audio_file(invalid_file)
    if not is_valid and "not supported" in error.lower():
        print("✓ Invalid format rejected correctly")
    else:
        print(f"✗ Invalid format validation failed")
    
    return True


def main():
    """
    Chạy tất cả các test
    """
    print("\n" + "="*60)
    print("SPEECH SERVICE DEMO & TEST")
    print("="*60)
    print("\nScript này test Speech-to-Text service mà không cần Flask server")
    
    results = []
    
    # Test 1: Installation
    results.append(("Whisper Installation", test_whisper_installation()))
    
    # Test 2: Load model (chỉ chạy nếu test 1 pass)
    if results[0][1]:
        results.append(("Load Model", test_load_model()))
    
    # Test 3: Transcribe (chỉ chạy nếu test 2 pass)
    if len(results) > 1 and results[1][1]:
        results.append(("Transcribe Sample", test_transcribe_sample()))
    
    # Test 4: Validation (luôn chạy)
    results.append(("File Validation", test_file_validation()))
    
    # Tổng kết
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "PASSED ✓" if passed else "FAILED ✗"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Speech service is ready!")
        print("\nNext steps:")
        print("1. Start Flask server: python main.py")
        print("2. Test API: python tests/test_speech_api.py")
        print("3. Read docs: SPEECH_API_GUIDE.md")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        print("\nCommon issues:")
        print("- Whisper not installed: pip install openai-whisper")
        print("- ffmpeg not installed: choco install ffmpeg (Windows)")
        print("- No audio sample: create test_audio.mp3 for testing")


if __name__ == "__main__":
    main()
