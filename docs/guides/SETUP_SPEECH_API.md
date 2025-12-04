# Hướng Dẫn Khắc Phục Lỗi và Chạy Server

## Vấn Đề Hiện Tại

Bạn đang gặp lỗi: `ModuleNotFoundError: No module named 'flask'`

**Nguyên nhân:** Dependencies chưa được cài đặt hoặc bạn đang dùng Python environment khác.

## Giải Pháp

### Option 1: Sử Dụng Virtual Environment (Khuyến Nghị)

```bash
# 1. Tạo virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows CMD:
.\venv\Scripts\activate.bat

# 3. Cài đặt dependencies
pip install Flask flask-restx flask-cors flask-mail
pip install openai-whisper ffmpeg-python
pip install chromadb sentence-transformers
pip install psycopg2-binary SQLAlchemy
pip install python-dotenv PyJWT bcrypt

# 4. Chạy server
python main.py
```

### Option 2: Cài Đặt Trực Tiếp (Nếu không dùng venv)

```bash
# Cài các package cần thiết cho Speech API
pip install Flask flask-restx flask-cors
pip install openai-whisper ffmpeg-python
pip install python-dotenv

# Chạy server
python main.py
```

### Option 3: Cài Đặt Từ requirements.txt (Nếu có sẵn)

```bash
# Lưu ý: requirements.txt có thể có version cũ của torch
# Bạn có thể skip torch nếu gặp lỗi

pip install Flask flask-restx flask-cors flask-mail
pip install openai-whisper ffmpeg-python
pip install chromadb sentence-transformers psycopg2-binary SQLAlchemy
pip install python-dotenv PyJWT bcrypt
```

## Kiểm Tra Sau Khi Cài Đặt

### 1. Kiểm tra Flask

```bash
python -c "import flask; print(flask.__version__)"
```

Kết quả mong đợi: `3.0.1` hoặc tương tự

### 2. Kiểm tra Whisper

```bash
python test_whisper_quick.py
```

Kết quả mong đợi:
```
✓ Whisper installed successfully!
✓ Model loaded successfully!
✓ ffmpeg installed
```

### 3. Chạy Server

```bash
python main.py
```

Kết quả mong đợi:
```
* Running on http://127.0.0.1:5000
```

## Nếu Vẫn Gặp Lỗi

### Lỗi: "No module named 'whisper'"

```bash
pip install openai-whisper
```

### Lỗi: "ffmpeg not found"

**Windows:**
```bash
# Cài ffmpeg bằng Chocolatey
choco install ffmpeg

# Hoặc tải từ: https://ffmpeg.org/download.html
# Sau đó thêm vào PATH
```

**Kiểm tra:**
```bash
ffmpeg -version
```

### Lỗi: "torch version conflict"

```bash
# Cài torch version mới hơn
pip install torch --upgrade
```

### Lỗi: "Cannot import name 'generate_medical_answer'"

✅ **Đã fix!** File `speech_controller.py` đã được cập nhật để dùng đúng functions.

## Test API Sau Khi Server Chạy

### 1. Test Health Check

```bash
curl http://localhost:5000/api/speech/health
```

### 2. Test Swagger UI

Mở trình duyệt: `http://localhost:5000/docs`

Tìm section **speech** và test các endpoint.

### 3. Test với file audio

```bash
# Tạo file audio test (hoặc dùng file có sẵn)
curl -X POST http://localhost:5000/api/speech/transcribe \
  -F "audio=@test_audio.mp3" \
  -F "language=vi"
```

## Tóm Tắt Các Bước

1. ✅ **Activate venv** (nếu dùng)
2. ✅ **Cài Flask và dependencies**
3. ✅ **Cài openai-whisper**
4. ✅ **Cài ffmpeg** (hệ thống)
5. ✅ **Chạy `python main.py`**
6. ✅ **Test tại `http://localhost:5000/docs`**

## Liên Hệ

Nếu vẫn gặp vấn đề, vui lòng:
1. Kiểm tra Python version: `python --version` (cần >= 3.8)
2. Kiểm tra pip version: `pip --version`
3. Thử chạy trong virtual environment mới

**Chúc bạn thành công! 🎉**
