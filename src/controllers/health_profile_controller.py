"""
Health Profile Controller
=========================
REST API endpoints để quản lý hồ sơ sức khỏe cá nhân.

Endpoints:
- GET /api/health-profile - Lấy hồ sơ của user hiện tại
- PUT /api/health-profile - Cập nhật hồ sơ của user hiện tại
- DELETE /api/health-profile - Xóa hồ sơ của user hiện tại

Tất cả endpoints đều yêu cầu JWT authentication.
"""

from flask import request
from flask_restx import Namespace, Resource, fields
import logging
from src.services.health_profile_service import health_profile_service
from src.utils.auth_middleware import token_required
from src.models.base import db

logger = logging.getLogger(__name__)

# Tạo namespace cho Health Profile API
health_profile_ns = Namespace(
    'health-profile',
    description='Health Profile Management - Quản lý hồ sơ sức khỏe cá nhân'
)

# ============================================================================
# API MODELS (Định nghĩa cấu trúc request/response cho Swagger UI)
# ============================================================================

# Model cho request body (PUT)
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
        description='Nhóm máu',
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
        description='Danh sách dị ứng',
        example=['Penicillin', 'Peanuts', 'Seafood']
    ),
    'chronic_conditions': fields.List(
        fields.String,
        description='Danh sách bệnh mãn tính',
        example=['Diabetes Type 2', 'Hypertension']
    ),
    'medications': fields.List(
        fields.String,
        description='Danh sách thuốc đang dùng',
        example=['Metformin 500mg', 'Aspirin 100mg']
    ),
    'family_history': fields.String(
        description='Tiền sử gia đình',
        example='Bố bị tiểu đường, mẹ bị cao huyết áp'
    )
})

# Model cho response body
health_profile_output = health_profile_ns.model('HealthProfileOutput', {
    'user_id': fields.Integer(description='ID người dùng'),
    'date_of_birth': fields.String(description='Ngày sinh'),
    'age': fields.Integer(description='Tuổi (tính tự động)'),
    'gender': fields.String(description='Giới tính'),
    'blood_type': fields.String(description='Nhóm máu'),
    'height': fields.Float(description='Chiều cao (cm)'),
    'weight': fields.Float(description='Cân nặng (kg)'),
    'bmi': fields.Float(description='Chỉ số BMI (tính tự động)'),
    'allergies': fields.List(fields.String, description='Danh sách dị ứng'),
    'chronic_conditions': fields.List(fields.String, description='Bệnh mãn tính'),
    'medications': fields.List(fields.String, description='Thuốc đang dùng'),
    'family_history': fields.String(description='Tiền sử gia đình'),
    'created_at': fields.String(description='Thời gian tạo'),
    'updated_at': fields.String(description='Thời gian cập nhật')
})


# ============================================================================
# API ENDPOINTS
# ============================================================================

@health_profile_ns.route('')
class HealthProfileResource(Resource):
    """
    Endpoint chính để quản lý hồ sơ sức khỏe.
    """
    
    @health_profile_ns.response(200, 'Success', health_profile_output)
    @health_profile_ns.response(404, 'Profile not found')
    @health_profile_ns.response(401, 'Unauthorized - Cần JWT token')
    @health_profile_ns.doc(security='Bearer')
    @token_required
    def get(self, current_user):
        """
        Lấy hồ sơ sức khỏe của user hiện tại.
        
        Yêu cầu:
        - Header: Authorization: Bearer <JWT_TOKEN>
        
        Returns:
            JSON chứa thông tin hồ sơ sức khỏe
        """
        try:
            user_id = current_user['user_id']
            
            # Lấy profile từ database
            profile = health_profile_service.get_profile(user_id)
            
            if not profile:
                return {
                    'message': 'Health profile not found. Please create one first.',
                    'user_id': user_id
                }, 404
            
            # Trả về dạng dictionary
            return profile.to_dict(), 200
            
        except Exception as e:
            logger.error(f"Error getting health profile: {e}", exc_info=True)
            return {'message': f'Internal server error: {str(e)}'}, 500
    
    @health_profile_ns.expect(health_profile_input)
    @health_profile_ns.response(200, 'Updated', health_profile_output)
    @health_profile_ns.response(201, 'Created', health_profile_output)
    @health_profile_ns.response(400, 'Bad Request - Dữ liệu không hợp lệ')
    @health_profile_ns.response(401, 'Unauthorized - Cần JWT token')
    @health_profile_ns.doc(security='Bearer')
    @token_required
    def put(self, current_user):
        """
        Tạo mới hoặc cập nhật hồ sơ sức khỏe.
        
        Yêu cầu:
        - Header: Authorization: Bearer <JWT_TOKEN>
        - Body: JSON chứa thông tin hồ sơ (xem model bên dưới)
        
        Lưu ý:
        - Nếu chưa có hồ sơ → Tạo mới (201)
        - Nếu đã có hồ sơ → Cập nhật (200)
        - Các trường để trống sẽ không bị thay đổi
        
        Returns:
            JSON chứa thông tin hồ sơ đã lưu
        """
        try:
            user_id = current_user['user_id']
            data = request.json
            
            if not data:
                return {'message': 'Request body is required'}, 400
            
            # Kiểm tra xem đã có profile chưa (để biết trả về 200 hay 201)
            existing_profile = health_profile_service.get_profile(user_id)
            is_new = existing_profile is None
            
            # Tạo hoặc cập nhật profile
            profile = health_profile_service.create_or_update_profile(user_id, data)
            
            status_code = 201 if is_new else 200
            message = 'Health profile created successfully' if is_new else 'Health profile updated successfully'
            
            return {
                'message': message,
                'profile': profile.to_dict()
            }, status_code
            
        except ValueError as e:
            # Lỗi validation
            logger.warning(f"Validation error: {e}")
            return {'message': str(e)}, 400
            
        except Exception as e:
            logger.error(f"Error saving health profile: {e}", exc_info=True)
            db.session.rollback()
            return {'message': f'Internal server error: {str(e)}'}, 500
    
    @health_profile_ns.response(200, 'Deleted')
    @health_profile_ns.response(404, 'Profile not found')
    @health_profile_ns.response(401, 'Unauthorized - Cần JWT token')
    @health_profile_ns.doc(security='Bearer')
    @token_required
    def delete(self, current_user):
        """
        Xóa hồ sơ sức khỏe của user hiện tại.
        
        Yêu cầu:
        - Header: Authorization: Bearer <JWT_TOKEN>
        
        Returns:
            Thông báo xóa thành công
        """
        try:
            user_id = current_user['user_id']
            
            # Xóa profile
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
    Endpoint để lấy tóm tắt hồ sơ dạng text (dùng cho chatbot).
    """
    
    @health_profile_ns.response(200, 'Success')
    @health_profile_ns.response(404, 'Profile not found')
    @health_profile_ns.response(401, 'Unauthorized')
    @health_profile_ns.doc(security='Bearer')
    @token_required
    def get(self, current_user):
        """
        Lấy tóm tắt hồ sơ sức khỏe dạng text.
        
        Endpoint này trả về thông tin hồ sơ đã được format sẵn,
        phù hợp để đưa vào prompt của chatbot.
        
        Returns:
            JSON với trường 'summary' chứa text tóm tắt
        """
        try:
            user_id = current_user['user_id']
            
            # Lấy summary từ service
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
