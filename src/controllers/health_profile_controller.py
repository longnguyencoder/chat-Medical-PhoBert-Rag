"""
Health Profile Controller
=========================
REST API endpoints để quản lý hồ sơ sức khỏe cá nhân của người dùng.
Hồ sơ này rất quan trọng để Chatbot có thể tư vấn chính xác hơn (ví dụ: tránh dị ứng, tương tác thuốc).

Endpoints:
- GET /api/health-profile - Lấy hồ sơ của user hiện tại
- PUT /api/health-profile - Cập nhật hồ sơ của user hiện tại
- DELETE /api/health-profile - Xóa hồ sơ của user hiện tại
- GET /api/health-profile/summary - Lấy bản tóm tắt text cho Chatbot

Tất cả endpoints đều yêu cầu JWT authentication để đảm bảo bảo mật.
"""

from flask import request  # Import đối tượng request để lấy data từ client
from flask_restx import Namespace, Resource, fields  # Các công cụ tạo API Document
import logging  # Ghi log
from src.services.health_profile_service import health_profile_service  # Import logic xử lý
from src.utils.auth_middleware import token_required  # Decorator check login
from src.models.base import db  # Database session

logger = logging.getLogger(__name__)  # Khởi tạo logger

# Tạo namespace (nhóm API) cho Health Profile
health_profile_ns = Namespace(
    'health-profile',
    description='Health Profile Management - Quản lý hồ sơ sức khỏe cá nhân'
)

# ============================================================================
# API MODELS (Định nghĩa cấu trúc request/response cho Swagger UI)
# ============================================================================

# Model Input: Dữ liệu client gửi lên khi tạo/sửa hồ sơ
health_profile_input = health_profile_ns.model('HealthProfileInput', {
    'date_of_birth': fields.String(
        description='Ngày sinh (YYYY-MM-DD)',
        example='1990-05-15'
    ),
    'gender': fields.String(
        description='Giới tính: Male, Female, Other',
        example='Male',
        enum=['Male', 'Female', 'Other']
    ),
    'blood_type': fields.String(
        description='Nhóm máu (VD: O+, A-, AB+)',
        example='O+'
    ),
    'height': fields.Float(
        description='Chiều cao (cm)',
        example=170.5
    ),
    'weight': fields.Float(
        description='Cân nặng (kg)',
        example=65.0
    ),
    'allergies': fields.List(
        fields.String,
        description='Danh sách các chất gây dị ứng (thuốc, thức ăn...)',
        example=['Penicillin', 'Peanuts', 'Seafood']
    ),
    'chronic_conditions': fields.List(
        fields.String,
        description='Danh sách bệnh mãn tính (tiểu đường, huyết áp...)',
        example=['Diabetes Type 2', 'Hypertension']
    ),
    'medications': fields.List(
        fields.String,
        description='Danh sách thuốc đang sử dụng thường xuyên',
        example=['Metformin 500mg', 'Aspirin 100mg']
    ),
    'family_history': fields.String(
        description='Tiền sử bệnh trong gia đình',
        example='Bố bị tiểu đường, mẹ bị cao huyết áp'
    )
})

# Model Output: Dữ liệu server trả về
health_profile_output = health_profile_ns.model('HealthProfileOutput', {
    'user_id': fields.Integer(description='ID người dùng'),
    'date_of_birth': fields.String(description='Ngày sinh'),
    'age': fields.Integer(description='Tuổi được tính tự động từ ngày sinh'),
    'gender': fields.String(description='Giới tính'),
    'blood_type': fields.String(description='Nhóm máu'),
    'height': fields.Float(description='Chiều cao (cm)'),
    'weight': fields.Float(description='Cân nặng (kg)'),
    'bmi': fields.Float(description='Chỉ số BMI (tính tự động từ chiều cao và cân nặng)'),
    'allergies': fields.List(fields.String, description='Danh sách dị ứng'),
    'chronic_conditions': fields.List(fields.String, description='Bệnh mãn tính'),
    'medications': fields.List(fields.String, description='Thuốc đang dùng'),
    'family_history': fields.String(description='Tiền sử gia đình'),
    'created_at': fields.String(description='Thời gian tạo hồ sơ'),
    'updated_at': fields.String(description='Thời gian cập nhật gần nhất')
})


# ============================================================================
# API ENDPOINTS
# ============================================================================

@health_profile_ns.route('')
class HealthProfileResource(Resource):
    """
    Class xử lý các request tới đường dẫn /api/health-profile
    """
    
    # --- GET: LẤY HỒ SƠ ---
    @health_profile_ns.response(200, 'Success', health_profile_output)
    @health_profile_ns.response(404, 'Profile not found - Chưa có hồ sơ')
    @health_profile_ns.response(401, 'Unauthorized - Cần JWT token')
    @health_profile_ns.doc(security='Bearer')  # Yêu cầu nút Authorize trên Swagger
    @token_required  # Middleware kiểm tra đăng nhập
    def get(self, current_user):
        """
        Lấy hồ sơ sức khỏe của user hiện tại.
        
        Logic:
        1. Lấy user_id từ token đã giải mã (`current_user`).
        2. Gọi service để tìm hồ sơ trong DB.
        3. Nếu có -> Trả về JSON (200).
        4. Nếu không -> Trả về lỗi 404 (nhắc user tạo hồ sơ).
        """
        try:
            # Token payload chứa user_id
            user_id = current_user['user_id']
            
            # Gọi Service để lấy dữ liệu
            profile = health_profile_service.get_profile(user_id)
            
            if not profile:
                logger.info(f"Health profile not found for user_id={user_id}")
                return {
                    'message': 'Health profile not found. Please create one first.',
                    'user_id': user_id
                }, 404
            
            # Chuyển object thành dictionary để trả về JSON
            return profile.to_dict(), 200
            
        except Exception as e:
            # Log lỗi server nếu có sự cố
            logger.error(f"Error getting health profile: {e}", exc_info=True)
            return {'message': f'Internal server error: {str(e)}'}, 500
    
    # --- PUT: TẠO HOẶC CẬP NHẬT HỒ SƠ ---
    @health_profile_ns.expect(health_profile_input)  # Validate input theo model
    @health_profile_ns.response(200, 'Updated - Cập nhật thành công', health_profile_output)
    @health_profile_ns.response(201, 'Created - Tạo mới thành công', health_profile_output)
    @health_profile_ns.response(400, 'Bad Request - Dữ liệu đầu vào sai')
    @health_profile_ns.response(401, 'Unauthorized - Cần JWT token')
    @health_profile_ns.doc(security='Bearer')
    @token_required
    def put(self, current_user):
        """
        Tạo mới (nếu chưa có) hoặc cập nhật (nếu đã có) hồ sơ sức khỏe.
        Cơ chế này gọi là Upsert (Update or Insert).
        
        Logic:
        1. Lấy user_id từ token.
        2. Lấy dữ liệu JSON client gửi lên.
        3. Kiểm tra xem user này đã có hồ sơ chưa.
        4. Gọi service `create_or_update_profile` để xử lý logic lưu DB.
        5. Trả về mã 201 (Created) nếu mới tạo, hoặc 200 (OK) nếu cập nhật.
        """
        try:
            user_id = current_user['user_id']
            data = request.json  # Dữ liệu body
            
            if not data:
                return {'message': 'Request body is required'}, 400
            
            # Kiểm tra state hiện tại để quyết định status code
            existing_profile = health_profile_service.get_profile(user_id)
            is_new = existing_profile is None
            
            # Gọi service xử lý logic nghiệp vụ (validate, format, save)
            profile = health_profile_service.create_or_update_profile(user_id, data)
            
            # Quyết định message và code trả về
            status_code = 201 if is_new else 200
            message = 'Health profile created successfully' if is_new else 'Health profile updated successfully'
            
            return {
                'message': message,
                'profile': profile.to_dict()
            }, status_code
            
        except ValueError as e:
            # Bắt các lỗi validation từ service (VD: ngày sinh sai format)
            logger.warning(f"Validation error for user {user_id}: {e}")
            return {'message': str(e)}, 400
            
        except Exception as e:
            # Lỗi hệ thống khác
            logger.error(f"Error saving health profile: {e}", exc_info=True)
            db.session.rollback()  # Rollback transaction nếu lỗi DB
            return {'message': f'Internal server error: {str(e)}'}, 500
    
    # --- DELETE: XÓA HỒ SƠ ---
    @health_profile_ns.response(200, 'Deleted - Xóa thành công')
    @health_profile_ns.response(404, 'Profile not found - Không tìm thấy để xóa')
    @health_profile_ns.response(401, 'Unauthorized')
    @health_profile_ns.doc(security='Bearer')
    @token_required
    def delete(self, current_user):
        """
        Xóa hoàn toàn hồ sơ sức khỏe của user.
        """
        try:
            user_id = current_user['user_id']
            
            # Gọi service xóa
            success = health_profile_service.delete_profile(user_id)
            
            if not success:
                return {'message': 'Health profile not found'}, 404
            
            return {'message': 'Health profile deleted successfully'}, 200
            
        except Exception as e:
            logger.error(f"Error deleting health profile: {e}", exc_info=True)
            db.session.rollback()
            return {'message': f'Internal server error: {str(e)}'}, 500


@health_profile_ns.route('/summary')
class HealthProfileSummary(Resource):
    """
    Endpoint phụ trợ cho AI Chatbot.
    Mục đích: Lấy thông tin tóm tắt dạng văn bản để nhúng vào Prompt của LLM.
    """
    
    @health_profile_ns.response(200, 'Success')
    @health_profile_ns.response(404, 'Profile not found')
    @health_profile_ns.response(401, 'Unauthorized')
    @health_profile_ns.doc(security='Bearer')
    @token_required
    def get(self, current_user):
        """
        Lấy tóm tắt hồ sơ sức khỏe dạng text string.
        
        Output ví dụ:
        "Tuổi: 25 | Giới tính: Nam | Dị ứng: Hải sản | Bệnh: Không"
        """
        try:
            user_id = current_user['user_id']
            
            # Service sẽ format dữ liệu thành chuỗi string dễ đọc cho AI
            summary = health_profile_service.format_profile_for_chatbot(user_id)
            
            if not summary:
                return {
                    'message': 'Health profile not found',
                    'summary': None
                }, 404
            
            return {
                'user_id': user_id,
                'summary': summary
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting profile summary: {e}", exc_info=True)
            return {'message': f'Internal server error: {str(e)}'}, 500
