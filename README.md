# Medical Chatbot API - PhoBERT RAG System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.2-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)
![PhoBERT](https://img.shields.io/badge/PhoBERT-RAG-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Hệ thống API Chatbot Y tế thông minh sử dụng PhoBERT và RAG cho tiếng Việt**

[Features](#tính-năng) • [Installation](#cài-đặt) • [API Documentation](#tài-liệu-api) • [Contributing](#đóng-góp)

</div>

---

## 📋 Tổng quan

Medical Chatbot API là một hệ thống chatbot y tế thông minh được phát triển như đồ án tốt nghiệp, sử dụng PhoBERT (mô hình BERT cho tiếng Việt) kết hợp với RAG (Retrieval-Augmented Generation) để trả lời các câu hỏi y tế bằng tiếng Việt. Hệ thống tích hợp công nghệ AI/ML để cung cấp thông tin y tế chính xác và đáng tin cậy.

### 🎯 Mục tiêu dự án

- Xây dựng hệ thống chatbot y tế thông minh cho người Việt Nam
- Sử dụng PhoBERT để hiểu ngữ nghĩa tiếng Việt tốt hơn
- Tích hợp RAG để truy xuất và tạo câu trả lời chính xác
- Cung cấp API RESTful cho ứng dụng frontend
- Quản lý lịch sử hội thoại và phân quyền admin

## ✨ Tính năng

### 🤖 AI Chatbot Y tế với PhoBERT

- **PhoBERT Model**: Sử dụng vinai/phobert-base-v2 cho tiếng Việt
- **RAG System**: Retrieval-Augmented Generation cho câu trả lời chính xác
- **Hybrid Search**: Kết hợp BM25 và Vector Search
- **ChromaDB**: Vector database cho semantic search
- **Caching**: Tối ưu hiệu suất với caching thông minh

### � Tìm kiếm Y tế Thông minh

- **Semantic Search**: Tìm kiếm dựa trên ngữ nghĩa
- **BM25 Ranking**: Xếp hạng kết quả theo độ liên quan
- **Medical Knowledge Base**: Cơ sở dữ liệu y tế tiếng Việt
- **Context-aware**: Hiểu ngữ cảnh câu hỏi

### 👤 Hệ thống Xác thực & Quản lý Người dùng

- **Đăng ký/Đăng nhập**: Với xác thực email OTP
- **Quản lý profile**: Cập nhật thông tin cá nhân
- **Quên mật khẩu**: Gửi OTP qua email
- **JWT Authentication**: Bảo mật API endpoints
- **Role-based Access Control**: Phân quyền Admin/User

### 💬 Hệ thống Chat & Lịch sử

- **Tạo cuộc trò chuyện**: Quản lý các phiên chat y tế
- **Lưu trữ tin nhắn**: Lịch sử trò chuyện đầy đủ
- **Conversation Summary**: Tóm tắt cuộc hội thoại tự động
- **Voice-to-Text**: Hỗ trợ nhập câu hỏi bằng giọng nói
- **Text-to-Speech**: Đọc câu trả lời bằng giọng nói

### 📊 Admin Dashboard (Mới)

- **User Statistics**: Thống kê người dùng (tổng, verified, unverified)
- **Conversation Stats**: Thống kê hội thoại và tin nhắn
- **Admin-only Access**: Chỉ admin mới truy cập được
- **Real-time Metrics**: Số liệu thời gian thực

### 🔔 Hệ thống Thông báo

- **Email notifications**: Thông báo qua email
- **Real-time updates**: Cập nhật trạng thái real-time
- **Notification management**: Quản lý thông báo

## 🛠️ Công nghệ sử dụng

### Backend

- **Python 3.8+**: Ngôn ngữ lập trình chính
- **Flask 3.0.2**: Web framework
- **Flask-RESTX**: API documentation và validation
- **SQLAlchemy**: ORM cho database
- **PostgreSQL**: Database chính
- **JWT**: Authentication

### AI/ML

- **PhoBERT**: vinai/phobert-base-v2 - BERT model cho tiếng Việt
- **ChromaDB**: Vector database cho semantic search
- **Sentence-Transformers**: Embedding models
- **BM25**: Ranking algorithm cho hybrid search
- **Transformers**: Hugging Face transformers library

### External Services

- **Flask-Mail**: Gửi email
- **SpeechRecognition**: Xử lý voice-to-text
- **gTTS**: Text-to-speech cho tiếng Việt

## 📦 Cài đặt

### Yêu cầu hệ thống

- Python 3.8 hoặc cao hơn
- PostgreSQL 13+
- Git
- pip (Python package manager)
- 4GB RAM trở lên (cho PhoBERT model)
- xem video hướng dẫn: https://drive.google.com/file/d/1r9NcBVBnb-qIWovHCr28ykBUnGZ7Wg0s/view?usp=sharing

### Bước 1: Clone Repository

```bash
git clone https://github.com/yourusername/ChatbotMedical_server.git
cd ChatbotMedical_server
```

### Bước 2: Tạo môi trường ảo

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

### Bước 4: Cấu hình Database

1. **Cài đặt PostgreSQL** (nếu chưa có):

   - Windows: Tải từ [postgresql.org](https://www.postgresql.org/download/windows/)
   - macOS: `brew install postgresql`
   - Ubuntu: `sudo apt-get install postgresql postgresql-contrib`

2. **Tạo database**:

   ```sql
   CREATE DATABASE medical1_db;
   CREATE USER postgres WITH PASSWORD 'root';
   GRANT ALL PRIVILEGES ON DATABASE medical1_db TO postgres;
   ```

### Bước 5: Cấu hình Environment Variables

Tạo file `.env` trong thư mục gốc:

```env
# Database Configuration
DATABASE_POSTGRESQL_URL=postgresql://postgres:root@localhost:5432/medical1_db
DB_HOST=localhost
DB_NAME=medical1_db
DB_USER=postgres
DB_PASSWORD=root
DB_PORT=5432

# JWT Configuration
SECRET_KEY=your-secret-key-here

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Cache Configuration
CACHE_ENABLED=True
CACHE_MAX_SIZE=1000
CACHE_TTL_SEARCH=3600
CACHE_TTL_RESPONSE=1800
```

### Bước 6: Chạy Database Migrations

```bash
# Thêm cột is_admin và tạo admin user
python add_admin_column.py
```

**Kết quả:**
- Thêm cột `is_admin` vào bảng Users
- Tạo admin user: `admin@medical.com` / `admin123`

### Bước 7: Import Medical Data (Tùy chọn)

```bash
# Import dữ liệu y tế vào ChromaDB
python src/nlp_model/import_medical_data.py
```

### Bước 8: Khởi chạy ứng dụng

```bash
python main.py
```

Ứng dụng sẽ chạy tại `http://localhost:5000`

### Bước 9: Kiểm tra API Documentation

Truy cập Swagger UI tại: `http://localhost:5000/docs`

## 📚 Tài liệu API

### Base URL

```
http://localhost:5000/api
```

### Các Endpoints chính

#### Authentication (`/api/auth`)

- `POST /register` - Đăng ký tài khoản
- `POST /login` - Đăng nhập
- `POST /verify-otp` - Xác thực OTP
- `POST /forgot-password` - Quên mật khẩu
- `POST /reset-password` - Đặt lại mật khẩu
- `PUT /update-name` - Cập nhật tên người dùng

#### Medical Chatbot (`/api/medical-chatbot`)

- `POST /chat` - Chat với AI chatbot y tế
- `POST /search` - Tìm kiếm thông tin y tế
- `GET /conversations` - Lấy danh sách cuộc hội thoại
- `GET /conversations/<id>` - Lấy chi tiết cuộc hội thoại
- `DELETE /conversations/<id>` - Xóa cuộc hội thoại
- `GET /conversations/<id>/messages` - Lấy tin nhắn của cuộc hội thoại

#### Speech (`/api/speech`)

- `POST /speech-to-text` - Chuyển giọng nói thành text
- `POST /text-to-speech` - Chuyển text thành giọng nói

#### Admin Statistics (`/api/admin`) 🔒 Admin Only

- `GET /stats/users` - Thống kê người dùng
- `GET /stats/conversations` - Thống kê hội thoại
- `GET /stats/all` - Tất cả thống kê

#### Notifications (`/api/notification`)

- `GET /list` - Lấy danh sách thông báo
- `PUT /<id>/read` - Đánh dấu đã đọc
- `DELETE /<id>` - Xóa thông báo

### Ví dụ sử dụng API

#### Đăng ký tài khoản

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "Nguyễn Văn A",
    "language_preference": "vi"
  }'
```

#### Chat với AI Chatbot Y tế

```bash
curl -X POST http://localhost:5000/api/medical-chatbot/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "conversation_id": 1,
    "message": "Triệu chứng của bệnh tiểu đường là gì?"
  }'
```

#### Lấy thống kê admin (Admin only)

```bash
curl -X GET http://localhost:5000/api/admin/stats/all \
  -H "Authorization: Bearer <admin_token>"
```

## 🧪 Testing

### Chạy tests

```bash
# Cài đặt pytest (nếu chưa có)
pip install pytest pytest-cov

# Chạy tất cả tests
python -m pytest

# Chạy tests với coverage
python -m pytest --cov=src

# Chạy tests cụ thể
python -m pytest tests/test_auth.py
```

### Kiểm tra kết nối database

```bash
python test_db_connection.py
```

## 🚀 Deployment

### Production Setup

1. **Cấu hình Production**:

   ```bash
   export FLASK_ENV=production
   export FLASK_DEBUG=0
   ```

2. **Sử dụng Gunicorn**:

   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 main:app
   ```

3. **Docker Deployment** (tùy chọn):

   ```bash
   docker build -t medical-chatbot-api .
   docker run -p 5000:5000 medical-chatbot-api
   ```

## 📁 Cấu trúc dự án

```
ChatbotMedical_server/
├── src/
│   ├── controllers/          # API endpoints
│   │   ├── auth_controller.py
│   │   ├── medical_chatbot_controller.py
│   │   ├── speech_controller.py
│   │   ├── admin_controller.py
│   │   └── notification_controller.py
│   ├── models/              # Database models
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── notification.py
│   │   └── otp.py
│   ├── services/            # Business logic
│   │   ├── auth_service.py
│   │   ├── medical_chatbot_service.py
│   │   ├── bm25_search.py
│   │   ├── cached_chatbot_service.py
│   │   ├── admin_service.py
│   │   └── notification_service.py
│   ├── utils/               # Utilities
│   │   └── auth_middleware.py
│   ├── config/              # Configuration
│   │   └── config.py
│   └── nlp_model/           # AI/ML components
│       ├── data/
│       ├── phobert_model/
│       └── chroma_db/
├── add_admin_column.py      # Migration script
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
└── README.md               # Project documentation
```

## 🔐 Admin Access

### Default Admin Account

```
Email: admin@medical.com
Password: admin123
```

⚠️ **Quan trọng**: Hãy đổi password sau khi đăng nhập lần đầu!

### Tạo Admin mới

**Option 1: Qua Database**
```sql
UPDATE "Users" SET is_admin = TRUE WHERE email = 'user@example.com';
```

**Option 2: Qua Python Script**
```python
from src import create_app
from src.models.user import User
from src.models.base import db

app = create_app()
with app.app_context():
    user = User.query.filter_by(email='user@example.com').first()
    if user:
        user.is_admin = True
        db.session.commit()
```

## 🤝 Đóng góp

Chúng tôi rất hoan nghênh mọi đóng góp từ cộng đồng! Vui lòng đọc [CONTRIBUTING.md](CONTRIBUTING.md) để biết thêm chi tiết về quy trình đóng góp.

### Cách đóng góp

1. Fork repository này
2. Tạo branch mới cho feature/fix
3. Commit các thay đổi
4. Push lên branch
5. Tạo Pull Request

### Báo cáo lỗi

Nếu bạn phát hiện lỗi, vui lòng tạo issue với:

- Mô tả chi tiết lỗi
- Các bước để tái hiện
- Môi trường thực thi
- Screenshots (nếu có)

## 📄 License

Dự án này được cấp phép theo [MIT License](LICENSE.md).

## 👥 Tác giả

**Sinh viên thực hiện**: Nguyễn Văn Long  
**Giảng viên hướng dẫn**: Nguyễn Thiện Dương  
**Trường**: Đại học Giao Thông Vận Tải  
**Khoa**: Khoa CNTT  
**Năm**: 2025

## 📞 Liên hệ

- 📱 0398481719
- 📧 long0398481719@gmail.com

## 🙏 Lời cảm ơn

- VinAI Research cho PhoBERT model
- ChromaDB team cho vector database
- Flask community cho web framework
- Hugging Face cho transformers library
- Tất cả contributors đã đóng góp cho dự án

---

<div align="center">

**⭐ Nếu dự án này hữu ích, hãy cho chúng tôi một star! ⭐**

</div>
