"""
Test Script cho Speech-to-Text API
===================================
Script này test các API endpoints của Speech-to-Text service.

Yêu cầu:
1. Server đang chạy (python main.py)
2. Có file audio mẫu để test
3. Có JWT token (nếu test endpoint /chat)

Cách chạy:
    python tests/test_speech_api.py
"""

import requests
import os
import sys
from pathlib import Path

# URL của API server
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

# Màu sắc cho terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_success(message):
    """In thông báo thành công màu xanh"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message):
    """In thông báo lỗi màu đỏ"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message):
    """In thông tin màu xanh dương"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")


def print_warning(message):
    """In cảnh báo màu vàng"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def test_health_check():
    """
    Test 1: Kiểm tra health của Speech service
    Endpoint: GET /api/speech/health
    """
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{API_BASE}/speech/health")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Service status: {data.get('status')}")
            print_info(f"Model: {data.get('model')}")
            print_info(f"Model loaded: {data.get('model_loaded')}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_transcribe_endpoint(audio_file_path):
    """
    Test 2: Test endpoint transcribe (chuyển audio thành text)
    Endpoint: POST /api/speech/transcribe
    
    Args:
        audio_file_path: Đường dẫn đến file audio test
    """
    print("\n" + "="*60)
    print("TEST 2: Transcribe Audio")
    print("="*60)
    
    if not os.path.exists(audio_file_path):
        print_error(f"Audio file not found: {audio_file_path}")
        return False
    
    print_info(f"Testing with file: {audio_file_path}")
    
    try:
        # Mở file audio
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            data = {'language': 'vi'}  # Tiếng Việt
            
            print_info("Sending request to /api/speech/transcribe...")
            response = requests.post(
                f"{API_BASE}/speech/transcribe",
                files=files,
                data=data
            )
        
        if response.status_code == 200:
            result = response.json()
            print_success("Transcription successful!")
            print_info(f"Text: {result.get('text')}")
            print_info(f"Language: {result.get('language')}")
            print_info(f"Duration: {result.get('duration')} seconds")
            return True
        else:
            print_error(f"Transcription failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_chat_endpoint(audio_file_path, jwt_token):
    """
    Test 3: Test endpoint chat (audio -> text -> chatbot)
    Endpoint: POST /api/speech/chat
    Yêu cầu JWT authentication
    
    Args:
        audio_file_path: Đường dẫn đến file audio test
        jwt_token: JWT token để authentication
    """
    print("\n" + "="*60)
    print("TEST 3: Speech-to-Chat (with JWT)")
    print("="*60)
    
    if not jwt_token:
        print_warning("No JWT token provided. Skipping this test.")
        print_info("To get JWT token:")
        print_info("1. Register: POST /api/auth/register")
        print_info("2. Login: POST /api/auth/login")
        return False
    
    if not os.path.exists(audio_file_path):
        print_error(f"Audio file not found: {audio_file_path}")
        return False
    
    print_info(f"Testing with file: {audio_file_path}")
    
    try:
        # Mở file audio
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            data = {'language': 'vi'}
            headers = {'Authorization': f'Bearer {jwt_token}'}
            
            print_info("Sending request to /api/speech/chat...")
            response = requests.post(
                f"{API_BASE}/speech/chat",
                files=files,
                data=data,
                headers=headers
            )
        
        if response.status_code == 200:
            result = response.json()
            print_success("Speech-to-chat successful!")
            print_info(f"Transcribed text: {result.get('transcribed_text')}")
            print_info(f"Chatbot answer: {result.get('answer')[:200]}...")
            print_info(f"Conversation ID: {result.get('conversation_id')}")
            return True
        elif response.status_code == 401:
            print_error("Unauthorized - Invalid JWT token")
            return False
        else:
            print_error(f"Request failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_invalid_file():
    """
    Test 4: Test với file không hợp lệ (error handling)
    """
    print("\n" + "="*60)
    print("TEST 4: Error Handling - Invalid File")
    print("="*60)
    
    try:
        # Test với file text (không phải audio)
        print_info("Testing with invalid file type (text file)...")
        
        # Tạo file text tạm
        temp_file = "temp_test.txt"
        with open(temp_file, 'w') as f:
            f.write("This is not an audio file")
        
        with open(temp_file, 'rb') as f:
            files = {'audio': (temp_file, f, 'text/plain')}
            response = requests.post(
                f"{API_BASE}/speech/transcribe",
                files=files
            )
        
        # Xóa file tạm
        os.remove(temp_file)
        
        if response.status_code == 400:
            print_success("Error handling works correctly!")
            print_info(f"Error message: {response.json().get('message')}")
            return True
        else:
            print_warning(f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def main():
    """
    Main function - chạy tất cả các test
    """
    print("\n" + "="*60)
    print("SPEECH-TO-TEXT API TEST SUITE")
    print("="*60)
    
    # Kiểm tra server có chạy không
    print_info("Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print_success("Server is running!")
        else:
            print_error("Server is not responding correctly")
            sys.exit(1)
    except:
        print_error("Cannot connect to server. Please start the server first:")
        print_info("Run: python main.py")
        sys.exit(1)
    
    # Tìm file audio mẫu
    audio_file = None
    possible_paths = [
        "test_audio.mp3",
        "test_audio.wav",
        "tests/test_audio.mp3",
        "tests/test_audio.wav",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            audio_file = path
            break
    
    if not audio_file:
        print_warning("No test audio file found!")
        print_info("Please create a test audio file (mp3 or wav) and place it in:")
        print_info("  - test_audio.mp3 (root directory)")
        print_info("  - tests/test_audio.mp3")
        print_warning("Some tests will be skipped.")
    
    # Lấy JWT token (nếu có)
    jwt_token = os.environ.get('JWT_TOKEN')
    if not jwt_token:
        print_warning("No JWT_TOKEN environment variable found")
        print_info("To test /chat endpoint, set JWT_TOKEN:")
        print_info("  export JWT_TOKEN=your_token_here  (Linux/Mac)")
        print_info("  set JWT_TOKEN=your_token_here     (Windows)")
    
    # Chạy các test
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health_check()))
    
    # Test 2: Transcribe (nếu có audio file)
    if audio_file:
        results.append(("Transcribe", test_transcribe_endpoint(audio_file)))
    
    # Test 3: Chat (nếu có audio file và JWT token)
    if audio_file and jwt_token:
        results.append(("Speech-to-Chat", test_chat_endpoint(audio_file, jwt_token)))
    
    # Test 4: Error handling
    results.append(("Error Handling", test_invalid_file()))
    
    # Tổng kết
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{test_name}: {status}{Colors.END}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("All tests passed! 🎉")
    else:
        print_warning(f"{total - passed} test(s) failed")


if __name__ == "__main__":
    main()
