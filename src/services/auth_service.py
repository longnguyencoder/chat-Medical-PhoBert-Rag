from datetime import datetime, timedelta  # Import thư viện xử lý thời gian (lấy giờ hiện tại, cộng trừ thời gian)
import jwt  # Import thư viện JWT để tạo và giải mã token xác thực
import random  # Import thư viện random để sinh số ngẫu nhiên (dùng cho OTP)
import string  # Import thư viện string để lấy tập hợp các ký tự số/chữ
from werkzeug.security import generate_password_hash, check_password_hash  # Import hàm băm mật khẩu và kiểm tra mật khẩu để bảo mật
from src.models.user import User  # Import Model User để thao tác với bảng users trong database
from src.models.otp import OTP  # Import Model OTP để thao tác với bảng otps trong database
from src.config.config import Config  # Import cấu hình hệ thống (như SECRET_KEY)
from src.services.email_service import send_otp_email  # Import hàm gửi email OTP từ service email
from src import db  # Import đối tượng database session để thực hiện các câu lệnh SQL

def generate_otp():
    """Hàm sinh mã OTP ngẫu nhiên gồm 6 chữ số"""
    # random.choices(string.digits, k=6): Chọn ngẫu nhiên 6 ký tự số từ '0123456789'
    # ''.join(...): Nối 6 ký tự đó thành 1 chuỗi string (VD: "123456")
    return ''.join(random.choices(string.digits, k=6))

def register_user(email, password, full_name, language_preference='en'):
    """
    Hàm xử lý nghiệp vụ đăng ký tài khoản mới.
    Input: email, password, full_name, ngôn ngữ
    Output: (True/False, Message)
    """
    # Bước 1: Kiểm tra email đã tồn tại trong database chưa (SELECT * FROM users WHERE email = ...)
    if User.query.filter_by(email=email).first():
        # Nếu tìm thấy user -> Trả về False và thông báo lỗi
        return False, 'Email already registered'
    
    # Bước 2: Sinh mã OTP để xác thực email
    otp_code = generate_otp()  # Gọi hàm sinh 6 số ngẫu nhiên
    expires_at = datetime.utcnow() + timedelta(minutes=10)  # Tính thời gian hết hạn: Thời gian hiện tại (UTC) + 10 phút
    
    # In log ra console để debug (tiện theo dõi khi chạy server)
    print(f"\n[DEBUG REGISTER] Creating OTP:")
    print(f"  Email: {email}")
    print(f"  OTP Code: {otp_code}")
    print(f"  Expires: {expires_at}")
    
    # Bước 3: Lưu OTP vào database
    otp = OTP(  # Khởi tạo đối tượng OTP mới
        email=email,  # Email nhận OTP
        otp_code=otp_code,  # Mã vừa sinh ra
        purpose='register',  # Mục đích: đăng ký (để phân biệt với reset password)
        expires_at=expires_at  # Thời điểm hết hạn
    )
    db.session.add(otp)  # Thêm vào session (hàng đợi chờ ghi)
    db.session.commit()  # Thực thi lệnh INSERT vào database
    print(f"  ✅ OTP saved to database\n")

    # Bước 4: Lưu thông tin User vào database (nhưng chưa kích hoạt)
    hashed_password = generate_password_hash(password)  # Băm mật khẩu (VD: "123456" -> "sha256$...") để bảo mật, không lưu plain text
    new_user = User(  # Khởi tạo đối tượng User mới
        email=email,
        password_hash=hashed_password,  # Lưu mật khẩu đã băm
        full_name=full_name,
        language_preference=language_preference,
        is_verified=False  # Đặt là False vì email chưa được xác thực bằng OTP
    )
    db.session.add(new_user)  # Thêm user vào session
    db.session.commit()  # Thực thi lệnh INSERT vào bảng users

    # Bước 5: Gửi email chứa OTP cho người dùng
    # Gọi service gửi email (chức năng này xử lý việc kết nối SMTP server)
    send_otp_email(email, otp_code, 'register')
    
    # Trả về True báo hiệu thành công
    return True, 'Registration initiated. Please check your email for OTP verification.'

def verify_otp(email, otp_code, purpose):
    """
    Hàm xác thực mã OTP người dùng gửi lên.
    Input: email, mã otp người nhập, mục đích (register/reset_password)
    """
    # Log thông tin verification
    print(f"\n[DEBUG VERIFY] Searching for OTP:")
    print(f"  Email: {email}")
    print(f"  Code: {otp_code}")
    print(f"  Purpose: {purpose}")
    
    # Bước 1: Tìm OTP trong database khớp với email, code, purpose và chưa sử dụng
    # SELECT * FROM otps WHERE email=... AND otp_code=... AND purpose=... AND is_used=False LIMIT 1
    otp = OTP.query.filter_by(
        email=email,
        otp_code=otp_code,
        purpose=purpose,
        is_used=False
    ).first()
    
    # Bước 2: Kiểm tra xem có tìm thấy OTP không
    if not otp:
        print(f"  ❌ OTP NOT FOUND")
        # Debug: In ra tất cả OTP của email này để xem tại sao sai (giúp dev sửa lỗi)
        all_otps = OTP.query.filter_by(email=email).all()
        print(f"  Total OTPs for {email}: {len(all_otps)}")
        for o in all_otps:
            print(f"    - Code: {o.otp_code}, Purpose: {o.purpose}, Used: {o.is_used}, Expires: {o.expires_at}")
        return False, 'Invalid or expired OTP'  # Trả về lỗi nếu không khớp
    
    print(f"  ✅ OTP FOUND")
    print(f"  Expires at: {otp.expires_at}")
    print(f"  Current time: {datetime.utcnow()}")
    
    # Bước 3: Kiểm tra xem OTP đã hết hạn chưa
    if otp.expires_at < datetime.utcnow():  # Nếu thời gian hết hạn < thời gian hiện tại
        print(f"  ❌ OTP EXPIRED\n")
        return False, 'Invalid or expired OTP'  # Báo lỗi hết hạn
    
    print(f"  ✅ OTP VALID\n")
    
    # Bước 4: Đánh dấu OTP đã được sử dụng
    otp.is_used = True  # Cập nhật state để không dùng lại được nữa
    
    # Bước 5: Xử lý nghiệp vụ sau khi OTP đúng
    if purpose == 'register':  # Nếu là xác thực đăng ký
        # Tìm user tương ứng
        user = User.query.filter_by(email=email).first()
        # Kích hoạt tài khoản
        user.is_verified = True  # UPDATE users SET is_verified=True WHERE email=...

        # Dọn dẹp: Xóa tất cả OTP đăng ký của user này dể database sạch sẽ
        OTP.query.filter_by(
            email=email,
            purpose='register'
        ).delete()
        
    db.session.commit()  # Lưu tất cả thay đổi (otp update, user verify, delete old otps) vào DB
    
    return True, 'OTP verified successfully'

def login_user(email, password):
    """
    Hàm xử lý đăng nhập.
    Input: email, password
    Output: (True/False, Token/Message)
    """
    # Bước 1: Tìm user trong DB theo email
    user = User.query.filter_by(email=email).first()
    
    # Bước 2: Kiểm tra user có tồn tại VÀ mật khẩu có khớp hash không
    if not user or not check_password_hash(user.password_hash, password):
        return False, 'Invalid email or password'  # Sai email hoặc pass
    
    # Bước 3: Kiểm tra user đã xác thực email (Verify OTP) chưa
    if not user.is_verified:
        return False, 'Please verify your email first'  # Chưa xác thực
    
    # Bước 4: Tạo JWT Token (Chìa khóa đăng nhập)
    token = jwt.encode({
        'user_id': user.user_id,  # Lưu user_id vào token để định danh
        'exp': datetime.utcnow() + timedelta(days=1)  # Token hết hạn sau 1 ngày (24h)
    }, Config.SECRET_KEY)  # Ký token bằng SECRET_KEY của server
    
    # Bước 5: Trả về thành công kèm Token và thông tin user
    return True, {
        'token': token,  # Token dạng string "ey..."
        'user': {  # Thông tin user (không trả về password)
            'id': user.user_id,
            'email': user.email,
            'full_name': user.full_name,
            'language_preference': user.language_preference,
            'is_verified': user.is_verified
        }
    }

def forgot_password(email):
    """
    Hàm xử lý yêu cầu quên mật khẩu.
    """
    # Bước 1: Kiểm tra email có tồn tại không
    user = User.query.filter_by(email=email).first()
    if not user:
        return False, 'Email not found'  # Không tìm thấy email
    
    # Bước 2: Sinh OTP mới cho việc reset pass
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=5)  # Hết hạn sau 5 phút
    
    # Bước 3: Lưu OTP vào DB
    otp = OTP(
        email=email,
        otp_code=otp_code,
        purpose='reset_password',  # Mục đích là reset pass
        expires_at=expires_at
    )
    db.session.add(otp)
    db.session.commit()

    # Bước 4: Gửi email OTP
    send_otp_email(email, otp_code, 'reset_password')
    
    return True, 'Password reset OTP sent'

def reset_password(email, otp_code, new_password):
    """
    Hàm thực hiện đổi mật khẩu mới (sau khi user có OTP).
    """
    # Bước 1: Kiểm tra OTP có đúng và ĐÃ ĐƯỢC verify chưa (is_used=True)
    # Lưu ý: Client thường gọi verify-otp trước, hàm verify-otp sẽ set is_used=True.
    # Hàm này check lại is_used=True để đảm bảo user đã qua bước verify.
    otp = OTP.query.filter_by(
        email=email,
        otp_code=otp_code,
        purpose='reset_password',
        is_used=True  # Quan trọng: Phải là OTP đã được verify thành công
    ).first()
    
    if not otp:
        return False, 'Please verify OTP first'  # Nếu chưa verify thì bắt verify trước
    
    # Bước 2: Cập nhật mật khẩu mới cho user
    user = User.query.filter_by(email=email).first()
    user.password_hash = generate_password_hash(new_password)  # Băm mật khẩu mới

    # Bước 3: Dọn dẹp - Xóa các OTP cũ
    OTP.query.filter_by(
        email=email,
        purpose='reset_password'
    ).delete()
    
    db.session.commit()  # Lưu thay đổi pass vào DB
    
    return True, 'Password has been reset successfully'

def update_user_name(user_id, new_full_name):
    """Hàm cập nhật tên user"""
    # Tìm user theo ID
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return False, 'User not found'
    
    # Cập nhật tên
    user.full_name = new_full_name
    db.session.commit()
    return True, 'User name updated successfully'

def resend_register_otp(email):
    """Hàm gửi lại OTP đăng ký (nếu user làm mất hoặc hết hạn)"""
    # Tìm user
    user = User.query.filter_by(email=email).first()
    if not user or user.is_verified:
        # Nếu không có user hoặc user đã verify rồi thì không gửi nữa
        return False, 'User not found or already verified'
        
    # Xóa các OTP cũ chưa dùng cho email này để tránh rác
    OTP.query.filter_by(email=email, purpose='register', is_used=False).delete()
    db.session.commit()
    
    # Sinh OTP mới
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Lưu OTP mới
    otp = OTP(
        email=email,
        otp_code=otp_code,
        purpose='register',
        expires_at=expires_at
    )
    db.session.add(otp)
    db.session.commit()
    
    # Gửi email
    send_otp_email(email, otp_code, 'register')
    return True, 'OTP resent successfully'

def resend_forgot_password_otp(email):
    """Hàm gửi lại OTP quên mật khẩu"""
    user = User.query.filter_by(email=email).first()
    if not user:
        return False, 'User not found'
    
    # Xóa các OTP cũ
    OTP.query.filter_by(email=email, purpose='reset_password', is_used=False).delete()
    db.session.commit()
    
    # Tạo OTP mới
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    otp = OTP(
        email=email,
        otp_code=otp_code,
        purpose='reset_password',
        expires_at=expires_at
    )
    db.session.add(otp)
    db.session.commit()
    
    send_otp_email(email, otp_code, 'reset_password')
    return True, 'OTP resent successfully'