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

from functools import wraps
from flask import request
import jwt
from src.config.config import Config
from src.models.user import User

def token_required(f):
    """
    Decorator để bảo vệ API endpoint bằng JWT token.
    
    Cách sử dụng:
    -------------
    @medical_chatbot_ns.route('/chat')
    class Chat(Resource):
        @token_required
        def post(self, current_user):
            user_id = current_user['user_id']
            # ... xử lý logic
    
    Luồng hoạt động:
    ----------------
    1. Client gửi request với header: Authorization: Bearer <token>
    2. Decorator này sẽ:
       - Kiểm tra header có token không
       - Decode token
       - Lấy user_id từ token
       - Truyền current_user vào function
    3. Nếu token không hợp lệ → Trả về 401 Unauthorized
    
    Args:
        f: Function cần bảo vệ
        
    Returns:
        Decorated function với tham số current_user
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Bước 1: Lấy token từ HTTP Header
        # Header format: "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # Tách "Bearer" và token
                # VD: "Bearer abc123" -> ["Bearer", "abc123"]
                token = auth_header.split(" ")[1]
            except IndexError:
                return {
                    'message': 'Token format không hợp lệ. Phải là: Bearer <token>'
                }, 401
        
        # Nếu không có token -> Từ chối truy cập
        if not token:
            return {
                'message': 'Token bị thiếu. Vui lòng đăng nhập để lấy token.'
            }, 401
        
        try:
            # Bước 2: Decode (giải mã) token
            # jwt.decode() sẽ:
            # - Kiểm tra chữ ký (signature) có đúng SECRET_KEY không
            # - Kiểm tra token có hết hạn (exp) chưa
            # - Trả về payload (dữ liệu) bên trong token
            data = jwt.decode(
                token, 
                Config.SECRET_KEY, 
                algorithms=["HS256"]  # Thuật toán mã hóa
            )
            
            # Bước 3: Lấy thông tin user từ database
            # Token chỉ chứa user_id, ta cần lấy thông tin đầy đủ
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return {
                    'message': 'User không tồn tại'
                }, 401
            
            # Chuyển User object thành dictionary để dễ sử dụng
            current_user_data = {
                'user_id': current_user.user_id,
                'email': current_user.email,
                'full_name': current_user.full_name,
                'is_verified': current_user.is_verified
            }
            
        except jwt.ExpiredSignatureError:
            # Token đã hết hạn (quá 1 ngày)
            return {
                'message': 'Token đã hết hạn. Vui lòng đăng nhập lại.'
            }, 401
            
        except jwt.InvalidTokenError:
            # Token không hợp lệ (bị sửa đổi, sai SECRET_KEY...)
            return {
                'message': 'Token không hợp lệ.'
            }, 401
        
        
        # Bước 4: Gọi function gốc và truyền current_user vào kwargs
        # Flask-RESTX Resource methods cần current_user trong kwargs
        kwargs['current_user'] = current_user_data
        return f(*args, **kwargs)
    
    return decorated


def optional_token(f):
    """
    Decorator cho phép API hoạt động CẢ với và không có token.
    
    Sử dụng khi:
    - API có thể dùng cho cả guest (không đăng nhập) và user đã đăng nhập
    - VD: Tìm kiếm bệnh viện (guest có thể xem, user thì lưu lịch sử)
    
    Args:
        f: Function cần bảo vệ
        
    Returns:
        Decorated function với current_user=None nếu không có token
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        current_user_data = None
        
        # Thử lấy token (không bắt buộc)
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
                
                # Nếu có token, decode nó
                data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
                current_user = User.query.get(data['user_id'])
                
                if current_user:
                    current_user_data = {
                        'user_id': current_user.user_id,
                        'email': current_user.email,
                        'full_name': current_user.full_name
                    }
            except:
                # Nếu token lỗi, bỏ qua (vẫn cho phép truy cập)
                pass
        
        # Gọi function với current_user (có thể là None)
        return f(*args, current_user=current_user_data, **kwargs)
    
    return decorated
