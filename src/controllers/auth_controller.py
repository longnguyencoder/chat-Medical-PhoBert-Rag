from flask_restx import Resource, fields, Namespace  # Import các công cụ để tạo API bằng thư viện flask-restx
# Import các hàm xử lý logic từ auth_service (Core logic nằm ở đây)
from src.services.auth_service import (
    register_user,
    verify_otp,
    login_user,
    forgot_password,
    reset_password,
    update_user_name,
    resend_register_otp,
    resend_forgot_password_otp
)
from src.services.email_service import send_otp_email  # Import hàm gửi email
from src.models.base import db  # Import database
from src.utils.auth_middleware import token_required  # Import decorator để bảo vệ API (yêu cầu login)

# Tạo một Namespace cho Auth. Namespace giúp nhóm các API lại với nhau (VD: /auth/login, /auth/register)
auth_ns = Namespace('auth', description='Authentication operations')

# ==================== ĐỊNH NGHĨA MODEL INPUT DOCS (SWAGGER) ====================
# Các model này dùng để validate dữ liệu đầu vào và hiển thị trên Swagger UI

# Model cho API Đăng ký
register_model = auth_ns.model('Register', {
    'email': fields.String(required=True, description='User email'),  # Bắt buộc phải có email
    'password': fields.String(required=True, description='User password'),  # Bắt buộc phải có pass
    'full_name': fields.String(required=True, description='User full name'),  # Bắt buộc tên
    'language_preference': fields.String(description='User language preference', default='en')  # Tùy chọn, mặc định en
})

# Model cho API Xác thực OTP
verify_otp_model = auth_ns.model('VerifyOTP', {
    'email': fields.String(required=True, description='User email'),
    'otp_code': fields.String(required=True, description='OTP code')  # Mã OTP 6 số
})

# Model cho API Đăng nhập
login_model = auth_ns.model('Login', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password')
})

# Model cho API Quên mật khẩu
forgot_password_model = auth_ns.model('ForgotPassword', {
    'email': fields.String(required=True, description='User email')
})

# Model cho API Đặt lại mật khẩu (Bước cuối)
reset_password_model = auth_ns.model('ResetPassword', {
    'email': fields.String(required=True, description='User email'),
    'otp_code': fields.String(required=True, description='OTP code'),
    'password': fields.String(required=True, description='New password')  # Mật khẩu mới
})

# Model hiển thị thông tin User (Output)
user_model = auth_ns.model('User', {
    'id': fields.Integer(description='User ID'),
    'email': fields.String(description='User email'),
    'full_name': fields.String(description='User full name'),
    'language_preference': fields.String(description='User language preference'),
    'is_verified': fields.Boolean(description='Email verification status')
})

# Model phản hồi khi đăng nhập thành công
login_response = auth_ns.model('LoginResponse', {
    'token': fields.String(description='JWT token'),  # Chuỗi Token dùng để xác thực sau này
    'user': fields.Nested(user_model)  # Lồng thông tin user vào
})

# Model cập nhật tên
update_name_model = auth_ns.model('UpdateName', {
    'full_name': fields.String(required=True, description='New full name')
})

# ==================== CÁC API ENDPOINTS ====================

@auth_ns.route('/register')  # Định nghĩa đường dẫn: POST /auth/register
class Register(Resource):
    @auth_ns.expect(register_model)  # Yêu cầu body check theo model register_model
    @auth_ns.response(201, 'Registration initiated. Please check your email for OTP verification.') # Tài liệu hóa
    @auth_ns.response(400, 'Missing required fields or email already registered')
    def post(self):
        """API Đăng ký tài khoản mới"""
        data = auth_ns.payload  # Lấy dữ liệu user gửi lên từ body
        
        # Kiểm tra dữ liệu đầu vào có đủ 3 trường bắt buộc không
        if not all(k in data for k in ('email', 'password', 'full_name')):
            return {'message': 'Missing required fields'}, 400
        
        # Gọi xuống Service để xử lý nghiệp vụ đăng ký
        success, message = register_user(
            data['email'],
            data['password'],
            data['full_name'],
            data.get('language_preference', 'en')
        )
        
        if not success:
            return {'message': message}, 400  # Trả về lỗi nếu service báo fail (VD: trùng email)
        
        db.session.commit()  # Commit giao dịch DB (thường service đã commit, dòng này để chắc chắn)
        return {'message': message}, 201  # HTTP 201 Created

@auth_ns.route('/verify-otp')  # Định nghĩa: POST /auth/verify-otp
class VerifyOTP(Resource):
    @auth_ns.expect(verify_otp_model)
    @auth_ns.response(200, 'Email verified successfully')
    @auth_ns.response(400, 'Invalid or expired OTP')
    def post(self):
        """API Xác thực OTP (dùng cho đăng ký)"""
        data = auth_ns.payload
        
        # Check input
        if not all(k in data for k in ('email', 'otp_code')):
            return {'message': 'Missing email or OTP code'}, 400
        
        # Gọi service xác thực OTP với mục đích 'register'
        success, message = verify_otp(data['email'], data['otp_code'], 'register')
        
        if not success:
            return {'message': message}, 400
        
        db.session.commit()
        return {'message': message}

@auth_ns.route('/login')  # Định nghĩa: POST /auth/login
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Login successful', login_response)
    @auth_ns.response(400, 'Missing email or password')
    @auth_ns.response(401, 'Invalid email or password or email not verified')
    def post(self):
        """API Đăng nhập"""
        data = auth_ns.payload
        
        if not all(k in data for k in ('email', 'password')):
            return {'message': 'Missing email or password'}, 400
        
        # Gọi service login
        # Kết quả result sẽ chứa {token: "...", user: {...}} nếu thành công
        success, result = login_user(data['email'], data['password'])
        
        if not success:
            return {'message': result}, 401  # 401 Unauthorized nếu sai pass/email
        
        return result  # Trả về JSON chứa token

@auth_ns.route('/forgot-password')  # Định nghĩa: POST /auth/forgot-password
class ForgotPassword(Resource):
    @auth_ns.expect(forgot_password_model)
    @auth_ns.response(200, 'Password reset OTP sent')
    @auth_ns.response(404, 'Email not found')
    def post(self):
        """API Yêu cầu quên mật khẩu (gửi OTP)"""
        data = auth_ns.payload
        
        if 'email' not in data:
            return {'message': 'Email is required'}, 400
        
        # Gọi service quên mật khẩu
        success, message = forgot_password(data['email'])
        
        if not success:
            return {'message': message}, 404
        
        db.session.commit()
        return {'message': message}

@auth_ns.route('/verify-reset-otp')
class VerifyResetOTP(Resource):
    @auth_ns.expect(verify_otp_model)
    @auth_ns.response(200, 'OTP verified successfully')
    @auth_ns.response(400, 'Invalid or expired OTP')
    def post(self):
        """API Validation OTP cho việc reset pass"""
        data = auth_ns.payload
        
        if not all(k in data for k in ('email', 'otp_code')):
            return {'message': 'Missing email or OTP code'}, 400
        
        # Gọi service verify_otp với mục đích 'reset_password'
        success, message = verify_otp(data['email'], data['otp_code'], 'reset_password')
        
        if not success:
            return {'message': message}, 400
        
        db.session.commit()
        return {'message': message}

@auth_ns.route('/reset-password')
class ResetPassword(Resource):
    @auth_ns.expect(reset_password_model)
    @auth_ns.response(200, 'Password has been reset successfully')
    @auth_ns.response(400, 'Invalid request or OTP')
    def post(self):
        """API Đặt lại mật khẩu mới"""
        data = auth_ns.payload
        
        if not all(k in data for k in ('email', 'otp_code', 'password')):
            return {'message': 'Missing required fields'}, 400
        
        # Gọi service reset_password
        success, message = reset_password(data['email'], data['otp_code'], data['password'])
        
        if not success:
            return {'message': message}, 400
        
        db.session.commit()
        return {'message': message}

@auth_ns.route('/update-username')
class UpdateName(Resource):
    @auth_ns.expect(update_name_model)
    @auth_ns.response(200, 'User name updated successfully')
    @auth_ns.response(401, 'Unauthorized')
    @auth_ns.response(404, 'User not found')
    @token_required  # <--- QUAN TRỌNG: API này được bảo vệ, phải có Token mới gọi được
    def put(self, current_user):  # current_user được inject từ decorator @token_required
        """API Cập nhật tên người dùng (Yêu cầu đăng nhập)"""
        data = auth_ns.payload
        
        # Validate input
        if 'full_name' not in data:
            return {'message': 'Missing full_name field'}, 400
        
        # Lấy user_id từ thông tin trong Token (An toàn hơn lấy từ body request)
        user_id = current_user['user_id']
        
        # Update user name gọi xuống service
        success, message = update_user_name(user_id, data['full_name'])
        
        if not success:
            return {'message': message}, 404
        
        return {
            'message': message,
            'user': {
                'user_id': user_id,
                'full_name': data['full_name']
            }
        }, 200

@auth_ns.route('/resend-register-otp')
class ResendRegisterOTP(Resource):
    @auth_ns.expect(forgot_password_model)
    @auth_ns.response(200, 'OTP resent successfully')
    @auth_ns.response(404, 'User not found or already verified')
    def post(self):
        """API Gửi lại OTP đăng ký"""
        data = auth_ns.payload
        if 'email' not in data:
            return {'message': 'Email is required'}, 400
        success, message = resend_register_otp(data['email'])
        if not success:
            return {'message': message}, 404
        return {'message': message}, 200

@auth_ns.route('/resend-forgot-password-otp')
class ResendForgotPasswordOTP(Resource):
    @auth_ns.expect(forgot_password_model)
    @auth_ns.response(200, 'OTP resent successfully')
    @auth_ns.response(404, 'User not found')
    def post(self):
        """API Gửi lại OTP quên mật khẩu"""
        data = auth_ns.payload
        if 'email' not in data:
            return {'message': 'Email is required'}, 400
        success, message = resend_forgot_password_otp(data['email'])
        if not success:
            return {'message': message}, 404
        return {'message': message}, 200