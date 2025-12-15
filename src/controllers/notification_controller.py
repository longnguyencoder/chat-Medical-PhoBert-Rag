"""
Notification Controller
=======================
REST API endpoints để quản lý thông báo (Notifications).
Hỗ trợ việc lấy danh sách, đánh dấu đã đọc, và xóa thông báo.

Endpoints:
- GET /api/notification/list - Lấy danh sách thông báo của user
- PUT /api/notification/{id}/read - Đánh dấu đã đọc
- DELETE /api/notification/{id} - Xóa thông báo

Lưu ý: System này được thiết kế để generic, có thể mở rộng cho nhiều loại thông báo khác nhau 
(nhắc thuốc, lịch khám, tin tức y tế...).
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from src.services.notification_service import (
    get_user_notifications,
    mark_notification_as_read,
    delete_notification
)

# Tạo Namespace
notification_ns = Namespace(
    'notification', 
    description='Notification Management - Quản lý thông báo và nhắc nhở'
)

# ============================================================================
# API MODELS
# ============================================================================

# Model đại diện cho 1 thông báo
notification_model = notification_ns.model('Notification', {
    'id': fields.Integer(description='ID thông báo'),
    'user_id': fields.Integer(description='ID người nhận'),
    'itinerary_id': fields.Integer(description='ID lịch trình (Legacy - Nếu có)'),
    'title': fields.String(description='Tiêu đề thông báo'),
    'message': fields.String(description='Nội dung thông báo'),
    'notification_type': fields.String(description='Loại thông báo (medication_reminder, system, etc.)'),
    'is_read': fields.Boolean(description='Trạng thái đã đọc'),
    'scheduled_for': fields.String(description='Thời gian dự kiến gửi (ISO format)'),
    'sent_at': fields.String(description='Thời gian thực tế đã gửi (ISO format)'),
    'created_at': fields.String(description='Thời gian tạo (ISO format)'),
    'is_deleted': fields.Boolean(description='Trạng thái đã xóa')
})

# Model wrap response trả về
notification_response_model = notification_ns.model('NotificationResponse', {
    'status': fields.String(description='Trạng thái request (success/error)'),
    'message': fields.String(description='Thông báo từ server'),
    'data': fields.Nested(notification_model, description='Dữ liệu thông báo chi tiết')
})

notification_list_response_model = notification_ns.model('NotificationListResponse', {
    'status': fields.String(description='Trạng thái request'),
    'message': fields.String(description='Thông báo từ server'),
    'data': fields.List(fields.Nested(notification_model), description='Danh sách thông báo')
})


# ============================================================================
# API ENDPOINTS
# ============================================================================

@notification_ns.route('/list')
class UserNotificationsResource(Resource):
    """
    Endpoint lấy danh sách thông báo.
    URI: /api/notification/list
    """
    
    @notification_ns.doc(params={
        'user_id': 'User ID (Bắt buộc)',
        'limit': 'Số lượng tối đa (Mặc định: 50)'
    })
    @notification_ns.response(200, 'Success', notification_list_response_model)
    @notification_ns.response(400, 'Bad Request')
    @notification_ns.response(500, 'Internal Server Error')
    def get(self):
        """
        Lấy tất cả thông báo của user (chưa bị xóa).
        Sắp xếp theo thời gian mới nhất.
        """
        # Lưu ý: Nên dùng token_required và lấy user_id từ token thay vì query param để bảo mật
        # Nhưng hiện tại giữ nguyên logic cũ và thêm comment.
        user_id = request.args.get('user_id', type=int)
        limit = request.args.get('limit', type=int, default=50)
        
        if not user_id:
            return {'message': 'user_id parameter is required'}, 400
        
        try:
            success, result = get_user_notifications(user_id, limit)
            
            if not success:
                return {'message': str(result)}, 500
                
            return {
                'status': 'success',
                'message': f'Successfully retrieved notifications for user {user_id}',
                'data': result
            }
            
        except Exception as e:
            return {'message': f'Error processing request: {str(e)}'}, 500


@notification_ns.route('/<int:notification_id>/read')
class MarkNotificationReadResource(Resource):
    """
    Endpoint đánh dấu đã đọc.
    URI: /api/notification/{id}/read
    """
    
    @notification_ns.doc(params={
        'user_id': 'User ID (required for authorization check)'
    })
    @notification_ns.response(200, 'Success')
    @notification_ns.response(404, 'Notification not found')
    @notification_ns.response(403, 'Unauthorized access to notification')
    def put(self, notification_id):
        """Đánh dấu một thông báo là đã đọc (is_read = True)."""
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return {'message': 'user_id parameter is required'}, 400
        
        try:
            success, result = mark_notification_as_read(notification_id, user_id)
            
            if not success:
                if "not found" in str(result):
                    return {'message': str(result)}, 404
                if "not authorized" in str(result):
                    return {'message': str(result)}, 403
                return {'message': str(result)}, 500
                
            return {
                'status': 'success',
                'message': result
            }
            
        except Exception as e:
            return {'message': f'Error processing request: {str(e)}'}, 500


@notification_ns.route('/<int:notification_id>')
class DeleteNotificationResource(Resource):
    """
    Endpoint xóa thông báo.
    URI: /api/notification/{id}
    """
    
    @notification_ns.doc(params={
        'user_id': 'User ID (required for authorization check)'
    })
    @notification_ns.response(200, 'Success')
    @notification_ns.response(404, 'Notification not found')
    def delete(self, notification_id):
        """Xóa thông báo (Soft delete)."""
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return {'message': 'user_id parameter is required'}, 400
        
        try:
            success, result = delete_notification(notification_id, user_id)
            
            if not success:
                if "not found" in str(result):
                    return {'message': str(result)}, 404
                if "not authorized" in str(result):
                    return {'message': str(result)}, 403
                return {'message': str(result)}, 500
                
            return {
                'status': 'success',
                'message': result
            }
            
        except Exception as e:
            return {'message': f'Error processing request: {str(e)}'}, 500