# Hướng Dẫn Cài ffmpeg - Bước Cuối Cùng
# ========================================

## Cách 1: Tải và Cài Thủ Công (5 phút)

### Bước 1: Tải ffmpeg
1. Mở: https://www.gyan.dev/ffmpeg/builds/
2. Tải file: **ffmpeg-release-essentials.zip** (~100MB)

### Bước 2: Giải nén
1. Giải nén file ZIP
2. Copy thư mục `ffmpeg-xxx-essentials_build` vào `C:\`
3. Đổi tên thành `C:\ffmpeg`

### Bước 3: Thêm vào PATH
1. Nhấn `Windows + R`, gõ: `sysdm.cpl`
2. Tab **Advanced** → **Environment Variables**
3. Trong **System variables**, chọn **Path** → **Edit**
4. Click **New** → Thêm: `C:\ffmpeg\bin`
5. Click **OK** tất cả

### Bước 4: Kiểm tra
Mở PowerShell MỚI và chạy:
```powershell
ffmpeg -version
```

Nếu thấy version → Thành công!

### Bước 5: Restart Server
```powershell
# Stop server hiện tại (Ctrl+C)
python main.py
```

## Cách 2: Dùng Chocolatey (Nếu đã cài)

```powershell
# Mở PowerShell as Administrator
choco install ffmpeg

# Restart terminal và kiểm tra
ffmpeg -version
```

## Cách 3: Dùng Scoop (Nếu đã cài)

```powershell
scoop install ffmpeg
ffmpeg -version
```

## Sau Khi Cài Xong

1. ✅ Restart terminal
2. ✅ Kiểm tra: `ffmpeg -version`
3. ✅ Restart server: `python main.py`
4. ✅ Test Speech API tại: http://localhost:5000/docs

## Tóm Tắt

**Vấn đề hiện tại:**
- ✅ Whisper đã cài
- ✅ Server đang chạy
- ❌ Thiếu ffmpeg

**Giải pháp:**
Cài ffmpeg theo Cách 1 (đơn giản nhất, không cần admin)

**Sau khi cài ffmpeg:**
Speech-to-Text sẽ hoạt động 100%! 🎉
