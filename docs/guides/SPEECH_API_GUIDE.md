# Hướng Dẫn Sử Dụng Speech-to-Text API

Tài liệu này hướng dẫn cách sử dụng tính năng Speech-to-Text (chuyển giọng nói thành văn bản) trong Medical Chatbot API.

## Tổng Quan

Speech-to-Text API cho phép bạn:
- ✅ Chuyển đổi file audio thành văn bản (tiếng Việt)
- ✅ Gửi câu hỏi bằng giọng nói cho chatbot y tế
- ✅ Hỗ trợ nhiều định dạng audio: mp3, wav, m4a, webm, ogg, flac
- ✅ Giới hạn file: 25MB

## Yêu Cầu Hệ Thống

### 1. Cài Đặt FFmpeg

Speech-to-Text sử dụng OpenAI Whisper, cần có **ffmpeg** trên hệ thống.

**Windows:**
```bash
# Cách 1: Dùng Chocolatey
choco install ffmpeg

# Cách 2: Tải từ ffmpeg.org
# 1. Tải từ: https://ffmpeg.org/download.html
# 2. Giải nén và thêm vào PATH
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

**Kiểm tra cài đặt:**
```bash
ffmpeg -version
```

### 2. Dependencies Python

Đã được cài đặt tự động qua `requirements.txt`:
```
openai-whisper==20231117
ffmpeg-python==0.2.0
```

## API Endpoints

### 1. Health Check

Kiểm tra xem Speech service có hoạt động không.

**Endpoint:** `GET /api/speech/health`

**Request:**
```bash
curl http://localhost:5000/api/speech/health
```

**Response:**
```json
{
  "success": true,
  "service": "speech-to-text",
  "status": "healthy",
  "model": "base",
  "model_loaded": true,
  "whisper_version": "20231117"
}
```

---

### 2. Transcribe Audio (Chuyển Audio Thành Text)

Chuyển đổi file audio thành văn bản.

**Endpoint:** `POST /api/speech/transcribe`

**Authentication:** Không cần (public endpoint)

**Request:**

**Với cURL:**
```bash
curl -X POST http://localhost:5000/api/speech/transcribe \
  -F "audio=@path/to/your/audio.mp3" \
  -F "language=vi"
```

**Với Python:**
```python
import requests

url = "http://localhost:5000/api/speech/transcribe"

# Mở file audio
with open("audio.mp3", "rb") as audio_file:
    files = {"audio": audio_file}
    data = {"language": "vi"}  # Tùy chọn: vi, en, auto
    
    response = requests.post(url, files=files, data=data)
    result = response.json()
    
    print(f"Text: {result['text']}")
    print(f"Language: {result['language']}")
```

**Với JavaScript (Browser):**
```javascript
const formData = new FormData();
formData.append('audio', audioFile);  // audioFile là File object
formData.append('language', 'vi');

fetch('http://localhost:5000/api/speech/transcribe', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('Text:', data.text);
  console.log('Language:', data.language);
});
```

**Parameters:**

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|----------|-------|
| `audio` | File | ✅ Có | File audio (mp3, wav, m4a, webm, ogg, flac). Max: 25MB |
| `language` | String | ❌ Không | Mã ngôn ngữ: `vi` (Tiếng Việt), `en` (English), `auto` (tự động). Mặc định: `vi` |

**Response Success (200):**
```json
{
  "success": true,
  "text": "Tôi bị đau đầu và sốt cao",
  "language": "vi",
  "duration": 3.5,
  "message": "Transcription successful"
}
```

**Response Error (400):**
```json
{
  "success": false,
  "message": "File format not supported. Allowed: mp3, wav, m4a, webm, ogg, flac"
}
```

---

### 3. Speech-to-Chat (Hỏi Chatbot Bằng Giọng Nói)

Chuyển audio thành text và tự động hỏi chatbot y tế.

**Endpoint:** `POST /api/speech/chat`

**Authentication:** ✅ Yêu cầu JWT Token

**Request:**

**Với cURL:**
```bash
curl -X POST http://localhost:5000/api/speech/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio=@question.mp3" \
  -F "language=vi" \
  -F "conversation_id=123"
```

**Với Python:**
```python
import requests

url = "http://localhost:5000/api/speech/chat"
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}

with open("question.mp3", "rb") as audio_file:
    files = {"audio": audio_file}
    data = {
        "language": "vi",
        "conversation_id": 123  # Tùy chọn: để tiếp tục cuộc hội thoại cũ
    }
    
    response = requests.post(url, files=files, data=data, headers=headers)
    result = response.json()
    
    print(f"Câu hỏi: {result['transcribed_text']}")
    print(f"Trả lời: {result['answer']}")
```

**Với JavaScript (Browser):**
```javascript
const formData = new FormData();
formData.append('audio', audioFile);
formData.append('language', 'vi');
formData.append('conversation_id', '123');  // Optional

fetch('http://localhost:5000/api/speech/chat', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + jwtToken
  },
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('Câu hỏi:', data.transcribed_text);
  console.log('Trả lời:', data.answer);
});
```

**Parameters:**

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|----------|-------|
| `audio` | File | ✅ Có | File audio chứa câu hỏi |
| `language` | String | ❌ Không | Mã ngôn ngữ (mặc định: `vi`) |
| `conversation_id` | Integer | ❌ Không | ID cuộc hội thoại (để tiếp tục chat cũ) |

**Headers:**

| Header | Giá trị |
|--------|---------|
| `Authorization` | `Bearer <JWT_TOKEN>` |

**Response Success (200):**
```json
{
  "success": true,
  "transcribed_text": "Triệu chứng của bệnh tiểu đường là gì?",
  "question": "Triệu chứng của bệnh tiểu đường là gì?",
  "answer": "Các triệu chứng của bệnh tiểu đường bao gồm: đi tiểu nhiều, khát nước thường xuyên, mệt mỏi, sụt cân không rõ nguyên nhân...",
  "sources": [
    {
      "content": "...",
      "metadata": {...}
    }
  ],
  "conversation_id": 123,
  "message_id": 456,
  "language": "vi",
  "duration": 4.2
}
```

**Response Error (401 - Unauthorized):**
```json
{
  "success": false,
  "message": "Token is missing or invalid"
}
```

---

## Cách Lấy JWT Token

Để sử dụng endpoint `/speech/chat`, bạn cần JWT token:

### 1. Đăng Ký Tài Khoản

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password",
    "full_name": "Your Name"
  }'
```

### 2. Đăng Nhập

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password"
  }'
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {...}
}
```

Sử dụng `token` này cho header `Authorization: Bearer <token>`.

---

## Test API với Postman

### 1. Import vào Postman

Tạo collection mới với các request sau:

**Request 1: Transcribe**
- Method: `POST`
- URL: `http://localhost:5000/api/speech/transcribe`
- Body: `form-data`
  - Key: `audio`, Type: `File`, Value: chọn file audio
  - Key: `language`, Type: `Text`, Value: `vi`

**Request 2: Speech-to-Chat**
- Method: `POST`
- URL: `http://localhost:5000/api/speech/chat`
- Headers:
  - Key: `Authorization`, Value: `Bearer YOUR_JWT_TOKEN`
- Body: `form-data`
  - Key: `audio`, Type: `File`, Value: chọn file audio
  - Key: `language`, Type: `Text`, Value: `vi`

### 2. Test với Swagger UI

1. Mở trình duyệt: `http://localhost:5000/docs`
2. Tìm section **speech**
3. Click vào endpoint muốn test
4. Click **"Try it out"**
5. Upload file audio
6. (Nếu cần) Click **Authorize** và nhập JWT token
7. Click **Execute**

---

## Ví Dụ Thực Tế

### Ví Dụ 1: Ghi Âm và Hỏi Chatbot (Python)

```python
import requests
import sounddevice as sd
import soundfile as sf
import numpy as np

# 1. Ghi âm từ microphone (3 giây)
print("Đang ghi âm... Hãy nói câu hỏi của bạn!")
duration = 3  # giây
sample_rate = 16000

audio_data = sd.rec(int(duration * sample_rate), 
                    samplerate=sample_rate, 
                    channels=1)
sd.wait()
print("Ghi âm xong!")

# 2. Lưu thành file
sf.write("question.wav", audio_data, sample_rate)

# 3. Gửi lên API
url = "http://localhost:5000/api/speech/chat"
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}

with open("question.wav", "rb") as f:
    files = {"audio": f}
    response = requests.post(url, files=files, headers=headers)

result = response.json()
print(f"\nCâu hỏi: {result['transcribed_text']}")
print(f"Trả lời: {result['answer']}")
```

### Ví Dụ 2: Web Interface Đơn Giản (HTML + JavaScript)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Speech-to-Text Medical Chatbot</title>
</head>
<body>
    <h1>Hỏi Chatbot Bằng Giọng Nói</h1>
    
    <button id="recordBtn">🎤 Ghi Âm</button>
    <button id="stopBtn" disabled>⏹ Dừng</button>
    
    <div id="result"></div>
    
    <script>
        let mediaRecorder;
        let audioChunks = [];
        const JWT_TOKEN = 'YOUR_JWT_TOKEN';  // Thay bằng token thực
        
        // Bắt đầu ghi âm
        document.getElementById('recordBtn').onclick = async () => {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                audioChunks = [];
                
                // Gửi lên API
                const formData = new FormData();
                formData.append('audio', audioBlob, 'question.webm');
                formData.append('language', 'vi');
                
                const response = await fetch('http://localhost:5000/api/speech/chat', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + JWT_TOKEN },
                    body: formData
                });
                
                const result = await response.json();
                document.getElementById('result').innerHTML = `
                    <p><strong>Câu hỏi:</strong> ${result.transcribed_text}</p>
                    <p><strong>Trả lời:</strong> ${result.answer}</p>
                `;
            };
            
            mediaRecorder.start();
            document.getElementById('recordBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
        };
        
        // Dừng ghi âm
        document.getElementById('stopBtn').onclick = () => {
            mediaRecorder.stop();
            document.getElementById('recordBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
        };
    </script>
</body>
</html>
```

---

## Troubleshooting

### Lỗi: "ffmpeg not found"

**Nguyên nhân:** Chưa cài đặt ffmpeg hoặc chưa thêm vào PATH.

**Giải pháp:**
1. Cài đặt ffmpeg (xem phần Yêu Cầu Hệ Thống)
2. Kiểm tra: `ffmpeg -version`
3. Restart terminal/IDE sau khi cài

### Lỗi: "File too large"

**Nguyên nhân:** File audio > 25MB.

**Giải pháp:**
- Nén file audio (giảm bitrate)
- Cắt file thành nhiều đoạn ngắn hơn
- Hoặc tăng giới hạn trong `src/__init__.py`:
  ```python
  app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
  ```

### Lỗi: "File format not supported"

**Nguyên nhân:** Định dạng file không được hỗ trợ.

**Giải pháp:**
- Chuyển đổi sang format được hỗ trợ: mp3, wav, m4a, webm, ogg, flac
- Dùng ffmpeg để convert:
  ```bash
  ffmpeg -i input.avi -acodec libmp3lame output.mp3
  ```

### Lỗi: "Unauthorized" (401)

**Nguyên nhân:** JWT token không hợp lệ hoặc hết hạn.

**Giải pháp:**
- Đăng nhập lại để lấy token mới
- Kiểm tra header `Authorization: Bearer <token>`
- Đảm bảo token chưa hết hạn (mặc định: 24h)

### Transcription Không Chính Xác

**Giải pháp:**
1. **Cải thiện chất lượng audio:**
   - Ghi âm trong môi trường yên tĩnh
   - Nói rõ ràng, không quá nhanh
   - Sử dụng microphone tốt

2. **Thử model lớn hơn:**
   Sửa trong `src/services/speech_service.py`:
   ```python
   speech_service = SpeechService(model_name='small')  # hoặc 'medium'
   ```

3. **Chỉ định ngôn ngữ:**
   ```python
   data = {"language": "vi"}  # Thay vì "auto"
   ```

---

## Performance Tips

### 1. Model Size vs Speed

| Model | Size | Speed | Độ chính xác |
|-------|------|-------|--------------|
| tiny | 75MB | Rất nhanh | Thấp |
| base | 150MB | Nhanh | Trung bình ⭐ |
| small | 500MB | Trung bình | Cao |
| medium | 1.5GB | Chậm | Rất cao |

**Khuyến nghị:** Dùng `base` cho production.

### 2. Caching Model

Model được load lần đầu tiên khi gọi API (lazy loading). Lần gọi đầu tiên sẽ chậm hơn (~10-30s), các lần sau nhanh hơn.

### 3. Concurrent Requests

Service hỗ trợ xử lý nhiều request đồng thời, nhưng mỗi request sẽ tốn ~1-2GB RAM.

**Khuyến nghị:** Giới hạn concurrent requests nếu server có ít RAM.

---

## Liên Hệ & Hỗ Trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra logs trong terminal
2. Xem phần Troubleshooting ở trên
3. Tạo issue trên GitHub repository

---

**Chúc bạn sử dụng thành công! 🎉**
