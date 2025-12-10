# Setup Instructions - Medication Reminder Feature

## Bước 1: Cài đặt Dependencies

```bash
pip install APScheduler==3.10.4 pytz==2024.1
```

## Bước 2: Cấu hình Gmail App Password

1. Vào https://myaccount.google.com/security
2. Bật **2-Step Verification**
3. Vào **App passwords** → Tạo password mới
4. Copy password và thêm vào `.env`:

```env
MAIL_PASSWORD=<your_16_character_app_password>
```

## Bước 3: Chạy Server (Tables sẽ tự động tạo)

```bash
python main.py
```

Khi server khởi động, bạn sẽ thấy:
```
✅ Medication reminder scheduler started successfully
   - Email reminders: Every 1 minute
   - Daily chatbot check: 21:00 GMT+7
   - Cleanup old logs: 00:00 GMT+7
```

**Lưu ý:** Tables `MedicationSchedules` và `MedicationLogs` sẽ được tạo tự động khi server start (qua `db.create_all()` trong `src/__init__.py`).

## Bước 4: Test API

Mở http://localhost:5000/docs và test các endpoints:

1. **Login** → Lấy JWT token
2. **POST /api/medication/schedules** → Tạo lịch uống thuốc
3. **GET /api/medication/schedules** → Xem danh sách
4. **GET /api/medication/logs/stats** → Xem thống kê

## Troubleshooting

### Nếu thiếu dependencies:
```bash
pip install -r requirements.txt
```

### Nếu scheduler không start:
Kiểm tra log có dòng này không:
```
Warning: Failed to initialize scheduler: ...
```

Nếu có, chạy lại:
```bash
pip install APScheduler==3.10.4 pytz==2024.1
```

### Kiểm tra tables đã tạo chưa:
```bash
python check_medication_tables.py
```
