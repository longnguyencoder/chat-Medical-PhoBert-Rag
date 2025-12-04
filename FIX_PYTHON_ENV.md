# FIX: Python Environment Issue
# ==============================

## Vấn Đề

Bạn đang dùng virtual environment `venv_old` nhưng nó không có pip.
Flask đã được cài vào global Python nhưng không thể dùng được.

## Giải Pháp

### Option 1: Deactivate venv và dùng Global Python (Đơn giản nhất)

```powershell
# 1. Deactivate virtual environment
deactivate

# 2. Kiểm tra Python path
python -c "import sys; print(sys.executable)"
# Kết quả mong đợi: C:\Users\PT COMPUTER\AppData\Local\Programs\Python\Python312\python.exe

# 3. Kiểm tra Flask đã cài chưa
python -c "import flask; print('Flask OK')"

# 4. Chạy server
python main.py
```

### Option 2: Tạo Virtual Environment Mới

```powershell
# 1. Deactivate venv cũ
deactivate

# 2. Tạo venv mới
python -m venv venv

# 3. Activate venv mới
.\venv\Scripts\Activate.ps1

# 4. Cài dependencies
python -m pip install Flask flask-restx flask-cors flask-mail
python -m pip install openai-whisper ffmpeg-python
python -m pip install python-dotenv PyJWT bcrypt

# 5. Chạy server
python main.py
```

### Option 3: Fix venv_old (Phức tạp hơn)

```powershell
# 1. Cài pip vào venv_old
python -m ensurepip --upgrade

# 2. Cài dependencies
python -m pip install Flask flask-restx flask-cors flask-mail
python -m pip install openai-whisper ffmpeg-python

# 3. Chạy server
python main.py
```

## Khuyến Nghị

**Dùng Option 1** - Đơn giản nhất vì Flask đã được cài vào global Python rồi!

```powershell
deactivate
python main.py
```

Nếu lệnh `deactivate` không work, đóng terminal và mở lại.

## Kiểm Tra Sau Khi Fix

```powershell
# Kiểm tra Python đang dùng
python -c "import sys; print(sys.executable)"

# Kiểm tra Flask
python -c "import flask; print(flask.__version__)"

# Kiểm tra Whisper
python -c "import whisper; print(whisper.__version__)"

# Chạy server
python main.py
```

## Về ffmpeg

ffmpeg không bắt buộc để chạy server, chỉ cần khi test Speech-to-Text.

Tải ffmpeg từ: https://ffmpeg.org/download.html
Giải nén và thêm vào PATH.
