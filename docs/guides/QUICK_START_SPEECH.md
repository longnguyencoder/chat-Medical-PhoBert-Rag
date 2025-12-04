# 🎤 Speech-to-Text API - Quick Start Guide

## Bước 1: Cài Đặt Dependencies

### Windows (PowerShell)

```powershell
# Cài Flask và dependencies cơ bản
pip install Flask==3.0.1 flask-restx flask-cors flask-mail
pip install python-dotenv PyJWT bcrypt Werkzeug==3.0.1

# Cài Speech-to-Text packages
pip install openai-whisper ffmpeg-python

# Cài ffmpeg (cần Chocolatey)
choco install ffmpeg
```

### Linux/Mac (Terminal)

```bash
# Cài Flask và dependencies cơ bản
pip3 install Flask==3.0.1 flask-restx flask-cors flask-mail
pip3 install python-dotenv PyJWT bcrypt Werkzeug==3.0.1

# Cài Speech-to-Text packages
pip3 install openai-whisper ffmpeg-python

# Cài ffmpeg
# Ubuntu/Debian:
sudo apt install ffmpeg

# Mac:
brew install ffmpeg
```

## Bước 2: Kiểm Tra Cài Đặt

```bash
# Kiểm tra Python packages
python -c "import flask; print('Flask:', flask.__version__)"
python -c "import whisper; print('Whisper:', whisper.__version__)"

# Kiểm tra ffmpeg
ffmpeg -version
```

## Bước 3: Chạy Server

```bash
python main.py
```

Kết quả mong đợi:
```
* Running on http://127.0.0.1:5000
```

## Bước 4: Test API

### Option 1: Swagger UI (Khuyến nghị)

1. Mở trình duyệt: `http://localhost:5000/docs`
2. Tìm section **speech** (màu xanh)
3. Click vào endpoint `/api/speech/transcribe`
4. Click **"Try it out"**
5. Upload file audio
6. Click **"Execute"**

### Option 2: cURL

```bash
# Test health check
curl http://localhost:5000/api/speech/health

# Test transcribe (cần file audio)
curl -X POST http://localhost:5000/api/speech/transcribe \
  -F "audio=@test_audio.mp3" \
  -F "language=vi"
```

### Option 3: Python

```python
import requests

# Test transcribe
with open("audio.mp3", "rb") as f:
    response = requests.post(
        "http://localhost:5000/api/speech/transcribe",
        files={"audio": f},
        data={"language": "vi"}
    )
    print(response.json())
```

## Troubleshooting

### ❌ "No module named 'flask'"

```bash
pip install Flask flask-restx flask-cors
```

### ❌ "No module named 'whisper'"

```bash
pip install openai-whisper
```

### ❌ "ffmpeg not found"

**Windows:**
```bash
choco install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

### ❌ Server không chạy được

Kiểm tra:
1. Python version >= 3.8: `python --version`
2. Tất cả packages đã cài: chạy các lệnh kiểm tra ở Bước 2
3. Port 5000 chưa bị chiếm: thử port khác trong `main.py`

## API Endpoints

### 1. Health Check
```
GET /api/speech/health
```
Kiểm tra service có hoạt động không.

### 2. Transcribe Audio
```
POST /api/speech/transcribe
```
Chuyển audio thành text (không cần authentication).

**Request:**
- `audio`: File audio (mp3, wav, m4a, webm, ogg, flac)
- `language`: Mã ngôn ngữ (vi/en/auto)

**Response:**
```json
{
  "success": true,
  "text": "Tôi bị đau đầu và sốt",
  "language": "vi",
  "duration": 3.5
}
```

### 3. Speech-to-Chat
```
POST /api/speech/chat
```
Chuyển audio → text → hỏi chatbot (cần JWT token).

**Request:**
- Header: `Authorization: Bearer <JWT_TOKEN>`
- `audio`: File audio
- `conversation_id`: ID cuộc hội thoại (optional)

**Response:**
```json
{
  "success": true,
  "transcribed_text": "Triệu chứng tiểu đường là gì?",
  "answer": "Các triệu chứng...",
  "conversation_id": 123,
  "message_id": 456
}
```

## Tài Liệu Chi Tiết

- 📖 **API Guide**: [`SPEECH_API_GUIDE.md`](SPEECH_API_GUIDE.md)
- 📖 **Setup Guide**: [`SETUP_SPEECH_API.md`](SETUP_SPEECH_API.md)
- 🧪 **Test Script**: [`tests/test_speech_api.py`](tests/test_speech_api.py)

## Tóm Tắt

✅ **3 bước đơn giản:**
1. Cài dependencies: `pip install Flask flask-restx openai-whisper ffmpeg-python`
2. Cài ffmpeg: `choco install ffmpeg` (Windows)
3. Chạy: `python main.py`

✅ **Test ngay:** `http://localhost:5000/docs`

🎉 **Chúc bạn thành công!**
