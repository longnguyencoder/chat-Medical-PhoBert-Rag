# Test Scripts

Thư mục này chứa các script test cho Medical Chatbot API.

## Cấu trúc

### Authentication Tests
- `test_register.py` - Test đăng ký tài khoản
- `test_register_new.py` - Test đăng ký với email ngẫu nhiên
- `test_verify_otp.py` - Test verify OTP
- `test_verify_quick.py` - Test verify OTP nhanh
- `test_jwt_auth.py` - Test JWT authentication
- `test_jwt_protected_apis.py` - Test các API được bảo vệ bằng JWT

### Chatbot Tests
- `test_medical_simple.py` - Test chatbot đơn giản
- `test_chat_history.py` - Test lịch sử chat
- `test_personalization.py` - Test cá nhân hóa
- `test_search.py` - Test tìm kiếm
- `test_search_simple.py` - Test tìm kiếm đơn giản
- `test_eval_simple.py` - Test đánh giá

### Conversation Tests
- `test_conversation_api.py` - Test API conversation
- `test_messages.py` - Test tin nhắn
- `test_advanced_features.py` - Test tính năng nâng cao

### Debug Scripts
- `debug_otp.py` - Debug OTP trong database
- `check_otp_db.py` - Kiểm tra OTP database
- `check_chromadb.py` - Kiểm tra ChromaDB
- `test_db_connection.py` - Test kết nối database

## Cách chạy

```bash
# Chạy từ root directory
python tests/test_jwt_auth.py
python tests/test_register.py
```
