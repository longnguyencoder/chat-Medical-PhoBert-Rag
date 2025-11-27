# Vietnam Travel Assistant API

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.2-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5--turbo-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Hệ thống API thông minh hỗ trợ du lịch Việt Nam với AI Chatbot đa ngôn ngữ**

[Features](#tính-năng) • [Installation](#cài-đặt) • [API Documentation](#tài-liệu-api) • [Contributing](#đóng-góp)

</div>

---

## 📋 Tổng quan

Vietnam Travel Assistant API là một hệ thống thông minh được phát triển như đồ án tốt nghiệp, cung cấp thông tin chi tiết về các địa điểm du lịch tại Việt Nam và trả lời câu hỏi của người dùng thông qua AI Chatbot đa ngôn ngữ. Hệ thống tích hợp công nghệ AI/ML để cung cấp trải nghiệm du lịch tối ưu.

### 🎯 Mục tiêu dự án

- Xây dựng hệ thống tư vấn du lịch thông minh cho Việt Nam
- Hỗ trợ đa ngôn ngữ (Tiếng Việt, Anh, Trung, Nhật, Hàn)
- Tích hợp AI để phân tích và trả lời câu hỏi du lịch
- Cung cấp API RESTful cho ứng dụng frontend
- Quản lý lịch trình du lịch cá nhân hóa

## ✨ Tính năng

### 🤖 AI Chatbot Đa ngôn ngữ

- **Nhận diện ngôn ngữ tự động**: Hỗ trợ 5 ngôn ngữ (Việt, Anh, Trung, Nhật, Hàn)
- **Xử lý câu hỏi thông minh**: Sử dụng OpenAI GPT-3.5-turbo
- **Tìm kiếm ngữ nghĩa**: ChromaDB với sentence-transformers
- **Trả lời tự nhiên**: Tạo câu trả lời như hướng dẫn viên thực thụ

### 🗺️ Quản lý Địa điểm Du lịch

- **Cơ sở dữ liệu địa điểm**: Hơn 1000+ địa điểm tại TP.HCM
- **Phân loại địa điểm**: Bảo tàng, công viên, nhà hàng, khách sạn, chợ, v.v.
- **Thông tin chi tiết**: Mô tả, địa chỉ, loại hình, khu vực
- **Tìm kiếm thông minh**: Dựa trên từ khóa và ngữ nghĩa

### 👤 Hệ thống Xác thực & Quản lý Người dùng

- **Đăng ký/Đăng nhập**: Với xác thực email OTP
- **Quản lý profile**: Cập nhật thông tin cá nhân
- **Quên mật khẩu**: Gửi OTP qua email
- **JWT Authentication**: Bảo mật API endpoints

### 💬 Hệ thống Chat & Lịch sử

- **Tạo cuộc trò chuyện**: Quản lý các phiên chat
- **Lưu trữ tin nhắn**: Lịch sử trò chuyện đầy đủ
- **Đa ngôn ngữ**: Hỗ trợ chat bằng nhiều ngôn ngữ
- **Voice messages**: Hỗ trợ tin nhắn thoại

### 📅 Quản lý Lịch trình Du lịch

- **Tạo lịch trình**: Thêm địa điểm vào lịch trình
- **Quản lý thời gian**: Sắp xếp theo ngày và thời gian
- **Nhắc nhở tự động**: Hệ thống scheduler gửi email nhắc nhở
- **Chia sẻ lịch trình**: Chia sẻ với bạn bè

### 🗺️ Tích hợp Bản đồ

- **Mapbox Integration**: Hiển thị địa điểm trên bản đồ
- **Tìm kiếm theo khu vực**: Lọc địa điểm theo quận/huyện
- **Định tuyến**: Gợi ý đường đi giữa các địa điểm

### 🔔 Hệ thống Thông báo

- **Email notifications**: Thông báo qua email
- **Scheduled reminders**: Nhắc nhở lịch trình tự động
- **Real-time updates**: Cập nhật trạng thái real-time

## 🛠️ Công nghệ sử dụng

### Backend

- **Python 3.8+**: Ngôn ngữ lập trình chính
- **Flask 3.0.2**: Web framework
- **Flask-RESTX**: API documentation và validation
- **SQLAlchemy**: ORM cho database
- **PostgreSQL**: Database chính
- **JWT**: Authentication

### AI/ML

- **OpenAI GPT-3.5-turbo**: Xử lý ngôn ngữ tự nhiên
- **ChromaDB**: Vector database cho semantic search
- **Sentence-Transformers**: Embedding models
- **LangDetect**: Nhận diện ngôn ngữ

### External Services

- **Mapbox**: Bản đồ và geocoding
- **Flask-Mail**: Gửi email
- **SpeechRecognition**: Xử lý voice messages

## 📦 Cài đặt

### Yêu cầu hệ thống

- Python 3.8 hoặc cao hơn
- PostgreSQL 13+
- Git
- pip (Python package manager)

### Bước 1: Clone Repository

```bash
git clone https://github.com/phamvangjang/ChatbotTravel_server
cd ChatbotTravel_server
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
   CREATE DATABASE vietnam_travel_assistant;
   CREATE USER travel_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE vietnam_travel_assistant TO travel_user;
   ```

### Bước 5: Cấu hình Environment Variables

Tạo file `.env` trong thư mục gốc:

```env
# Database Configuration
DATABASE_POSTGRESQL_URL=
DB_HOST=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_PORT=

# JWT Configuration
SECRET_KEY=
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=

# OpenAI Configuration
OPENAI_API_KEY=

# Mapbox Configuration
MAPBOX_ACCESS_TOKEN=
# Frontend URL
FRONTEND_URL=http://localhost:3000
```

### Bước 6: Chạy Database Migrations

```bash
# Chạy migration cho notifications table
python migrate_notifications.py

# Hoặc chạy migration PostgreSQL (nếu cần)
python migrate_to_postgresql.py
```

### Bước 7: Khởi chạy ứng dụng

```bash
python main.py
```

Ứng dụng sẽ chạy tại `http://localhost:5000`

### Bước 8: Kiểm tra API Documentation

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

#### Travel Chatbot (`/api/travel-chatbot`)

- `POST /search` - Tìm kiếm địa điểm với AI chatbot
- `GET /metadata` - Lấy metadata địa điểm

#### Chatting (`/api/chatting`)

- `POST /conversations` - Tạo cuộc trò chuyện mới
- `GET /conversations/list` - Lấy danh sách cuộc trò chuyện
- `POST /messages` - Gửi tin nhắn
- `GET /conversations/messages` - Lấy tin nhắn của cuộc trò chuyện

#### Itinerary (`/api/itinerary`)

- `POST /create` - Tạo lịch trình mới
- `GET /list` - Lấy danh sách lịch trình
- `PUT /update` - Cập nhật lịch trình
- `DELETE /delete` - Xóa lịch trình

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

#### Tìm kiếm địa điểm với AI

```bash
curl -X POST http://localhost:5000/api/travel-chatbot/search \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Nhà hàng ngon ở quận 1"
  }'
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
   docker build -t vietnam-travel-api .
   docker run -p 5000:5000 vietnam-travel-api
   ```

## 📁 Cấu trúc dự án

```
ChatbotTravel_server/
├── src/
│   ├── controllers/          # API endpoints
│   │   ├── auth_controller.py
│   │   ├── chatting_controller.py
│   │   ├── travel_chatbot_controller.py
│   │   ├── itinerary_controller.py
│   │   ├── notification_controller.py
│   │   └── map_controller.py
│   ├── models/              # Database models
│   │   ├── user.py
│   │   ├── attraction.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── itinerary.py
│   │   └── notification.py
│   ├── services/            # Business logic
│   │   ├── auth_service.py
│   │   ├── travel_chatbot_service.py
│   │   ├── chatting_service.py
│   │   ├── itinerary_service.py
│   │   └── notification_service.py
│   ├── config/              # Configuration
│   │   └── config.py
│   └── nlp_model/           # AI/ML components
│       ├── data/
│       ├── process_diadiem.py
│       └── read_chroma.py
├── migrations/              # Database migrations
├── uploads/                 # File uploads
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
└── README.md               # Project documentation
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

**Sinh viên thực hiện**: [Phạm Văn Giang]
**Giảng viên hướng dẫn**: [ThS Cô Trần Thị Dung]
**Trường**: [Đại học Giao Thông Vận Tải ]
**Khoa**: [Tên khoa]
**Năm**: 2024

## 📞 Liên hệ

- **Email**: [vangiangpham.work@gmail.com]
- **GitHub**: [github.com/phamvangjang]
- **LinkedIn**: [linkedin.com/in/pham-van-giang]

## 🙏 Lời cảm ơn

- OpenAI cho việc cung cấp API GPT
- ChromaDB team cho vector database
- Flask community cho web framework
- Tất cả contributors đã đóng góp cho dự án

---

<div align="center">

**⭐ Nếu dự án này hữu ích, hãy cho chúng tôi một star! ⭐**

</div>
