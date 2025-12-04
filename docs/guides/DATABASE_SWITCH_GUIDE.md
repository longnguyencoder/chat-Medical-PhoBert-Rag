# Hướng Dẫn Switch Database
# ==========================

## Cách Chuyển Đổi Giữa SQLite và PostgreSQL

### 📍 File cần sửa:
`src/config/config.py`

---

## Option 1: Dùng SQLite (Development)

**Khi nào dùng:**
- Development/Testing
- Chạy local trên máy
- Không cần nhiều users đồng thời

**Cách bật:**
```python
# Trong src/config/config.py (dòng 16-18):

# OPTION 1: SQLite - UNCOMMENT dòng này
SQLALCHEMY_DATABASE_URI = f'sqlite:///{SQLITE_DB_PATH}'

# OPTION 2: PostgreSQL - COMMENT dòng này
# SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_POSTGRESQL_URL')
```

**Restart server:**
```bash
python main.py
```

---

## Option 2: Dùng PostgreSQL (Production)

**Khi nào dùng:**
- Production/Deployment
- Nhiều users đồng thời
- Cần performance cao

**Bước 1: Cài PostgreSQL**
- Download: https://www.postgresql.org/download/
- Hoặc dùng Docker: `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres`

**Bước 2: Tạo database**
```sql
CREATE DATABASE chatbot_db;
```

**Bước 3: Thêm vào `.env`**
```env
DATABASE_POSTGRESQL_URL=postgresql://username:password@localhost:5432/chatbot_db
```

**Bước 4: Sửa config**
```python
# Trong src/config/config.py (dòng 16-18):

# OPTION 1: SQLite - COMMENT dòng này
# SQLALCHEMY_DATABASE_URI = f'sqlite:///{SQLITE_DB_PATH}'

# OPTION 2: PostgreSQL - UNCOMMENT dòng này
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_POSTGRESQL_URL')
```

**Bước 5: Migrate database**
```bash
# Tạo tables trong PostgreSQL
python
>>> from src import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

**Bước 6: Restart server**
```bash
python main.py
```

---

## ⚠️ Lưu Ý Quan Trọng

### Khi chuyển từ SQLite → PostgreSQL:
- ✅ Data trong SQLite KHÔNG tự động chuyển sang PostgreSQL
- ✅ Cần export/import data nếu muốn giữ lại
- ✅ PostgreSQL cần cài đặt riêng

### Khi chuyển từ PostgreSQL → SQLite:
- ✅ Data trong PostgreSQL KHÔNG tự động chuyển sang SQLite
- ✅ SQLite file sẽ được tạo tự động nếu chưa có
- ✅ Không cần cài đặt gì thêm

---

## 🔍 Kiểm Tra Database Đang Dùng

```bash
python -c "from src.config.config import Config; print('Database:', Config.SQLALCHEMY_DATABASE_URI[:30])"
```

**Output:**
- `sqlite:///...` → Đang dùng SQLite
- `postgresql://...` → Đang dùng PostgreSQL

---

## 📊 So Sánh

| Tính năng | SQLite | PostgreSQL |
|-----------|--------|------------|
| **Setup** | ✅ Dễ (không cần cài) | ⚠️ Cần cài server |
| **Performance** | ⚠️ Tốt cho <100 users | ✅ Tốt cho >1000 users |
| **Concurrent writes** | ❌ Hạn chế | ✅ Tốt |
| **Deployment** | ⚠️ Chỉ 1 server | ✅ Scale được |
| **Backup** | ✅ Copy file .db | ⚠️ Cần pg_dump |

---

## 🚀 Quick Commands

**Switch to SQLite:**
```bash
# 1. Edit config (uncomment SQLite line)
# 2. Restart
python main.py
```

**Switch to PostgreSQL:**
```bash
# 1. Start PostgreSQL server
# 2. Add DATABASE_POSTGRESQL_URL to .env
# 3. Edit config (uncomment PostgreSQL line)
# 4. Create tables: python -c "from src import create_app, db; app=create_app(); app.app_context().push(); db.create_all()"
# 5. Restart
python main.py
```
