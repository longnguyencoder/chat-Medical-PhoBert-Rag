"""
Auth Middleware - Xác thực JWT Token
=====================================
File này chứa decorator để bảo vệ các API bằng JWT token.

Cách hoạt động:
1. Đọc token từ HTTP Header "Authorization: Bearer <token>"
2. Decode token để lấy thông tin user
3. Kiểm tra token có hợp lệ không (chưa hết hạn, đúng SECRET_KEY)
4. Truyền thông tin user vào function được bảo vệ
"""

from functools import wraps  # Import wraps để giữ nguyên metadata của hàm được decorate
from flask import request  # Import request để truy cập HTTP headers
import jwt  # Thư viện xử lý JWT (Json Web Token)
from src.config.config import Config  # Import cấu hình lấy SECRET_KEY
from src.models.user import User  # Import Model Use

def token_required(f):
    """
    Decorator dùng để bảo vệ API. Chỉ cho phép request CÓ TOKEN hợp lệ đi qua.
    
    Tác dụng:
    - Chặn request không có token -> Trả về 401
    - Chặn request token giả/hết hạn -> Trả về 401
    - Nếu đúng -> Lấy thông tin user và truyền vào hàm xử lý
    """
    @wraps(f)  # Giữ nguyên tên hàm gốc (quan trọng cho Flask-RESTX)
    def decorated(*args, **kwargs):
        token = None
        
        # Bước 1: Kiểm tra Header Authorization
        # Client gửi lên dạng: "Authorization: Bearer <chuỗi_token_dài_ngoằng...>"
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # Tách chuỗi bằng dấu cách. Phần tử [0] là "Bearer", [1] là token
                token = auth_header.split(" ")[1]
            except IndexError:
                # Nếu format sai (không có dấu cách hoặc thiếu token)
                return {
                    'message': 'Token format không hợp lệ. Phải là: Bearer <token>'
                }, 401
        
        # Nếu không tìm thấy token trong header
        if not token:
            return {
                'message': 'Token bị thiếu. Vui lòng đăng nhập để lấy token.'
            }, 401
        
        try:
            # Bước 2: Giải mã (Decode) token
            # Dùng SECRET_KEY bí mật của server để mở khóa token
            # Nếu token bị hacker sửa đổi, hoặc hết hạn, hàm này sẽ bắn Exception
            data = jwt.decode(
                token, 
                Config.SECRET_KEY, 
                algorithms=["HS256"]  # Thuật toán mã hóa đối xứng
            )
            
            # Bước 3: Tìm user trong database dựa vào user_id trong token
            # Khi login, ta đã nhét user_id vào payload của token
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return {
                    'message': 'User không tồn tại (có thể đã bị xóa)'
                }, 401
            
            # Chuyển đối tượng User thành dictionary để dễ dùng
            current_user_data = {
                'user_id': current_user.user_id,
                'email': current_user.email,
                'full_name': current_user.full_name,
                'is_verified': current_user.is_verified,
                'is_admin': current_user.is_admin
            }
            
        except jwt.ExpiredSignatureError:
            # Lỗi: Token đã hết hạn (quá thời gian exp set lúc login)
            return {
                'message': 'Token đã hết hạn. Vui lòng đăng nhập lại.'
            }, 401
            
        except jwt.InvalidTokenError:
            # Lỗi: Token sai, không giải mã được
            return {
                'message': 'Token không hợp lệ.'
            }, 401
        
        
        # Bước 4: Gọi hàm gốc (bản chất của Middleware là bọc hàm gốc lại)
        # Truyền thêm tham số `current_user` vào để hàm controller dùng
        kwargs['current_user'] = current_user_data
        return f(*args, **kwargs)
    
    return decorated


def optional_token(f):
    """
    Decorator "Dễ tính": Có token cũng được, không có cũng được.
    
    Tác dụng:
    - Nếu có token -> Decode và lấy thông tin user (để lưu lịch sử cá nhân hóa)
    - Nếu không có token -> Vẫn cho qua, nhưng coi như khách vãng lai (Guest)
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        current_user_data = None  # Mặc định là None (Guest)
        
        # Kiểm tra header xem có gửi token không
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
                
                # Cố gắng decode token
                data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
                current_user = User.query.get(data['user_id'])
                
                if current_user:
                    # Nếu token đúng -> Lưu thông tin user
                    current_user_data = {
                        'user_id': current_user.user_id,
                        'email': current_user.email,
                        'full_name': current_user.full_name
                    }
            except:
                # Nếu token lỗi/hết hạn -> Bỏ qua, coi như không có login
                # Không return 401 ở đây vì đây là optional
                pass
        
        # Gọi hàm gốc, truyền current_user (có thể là data hoặc None)
        return f(*args, current_user=current_user_data, **kwargs)
    
    return decorated


def admin_required(f):
    """
    Decorator cấp cao: Chỉ dành cho ADMIN.
    
    Quy trình:
    1. Kiểm tra Token hợp lệ (giống token_required)
    2. Kiểm tra thêm quyền: user.is_admin có True không?
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 1. Lấy token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return {'message': 'Token format error'}, 401
        
        if not token:
            return {'message': 'Token missing'}, 401
        
        try:
            # 2. Decode token
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return {'message': 'User not found'}, 401
            
            # 3. KIỂM TRA QUYỀN ADMIN (Khác biệt so với token_required)
            if not current_user.is_admin:
                return {
                    'message': 'Truy cập bị từ chối. Bạn không phải là Admin.',
                    'required_role': 'admin'
                }, 403  # Trả về 403 Forbidden (Cấm)
            
            current_user_data = {
                'user_id': current_user.user_id,
                'email': current_user.email,
                'full_name': current_user.full_name,
                'is_verified': current_user.is_verified,
                'is_admin': current_user.is_admin
            }
            
        except jwt.ExpiredSignatureError:
            return {'message': 'Token expired'}, 401
        except jwt.InvalidTokenError:
            return {'message': 'Invalid token'}, 401
        
        kwargs['current_user'] = current_user_data
        return f(*args, **kwargs)
    
    return decorated
