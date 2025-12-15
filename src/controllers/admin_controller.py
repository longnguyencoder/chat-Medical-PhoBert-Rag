"""
Admin Controller
================
Controller quản lý các tính năng dành cho Admin.
Cung cấp các API thống kê số lượng người dùng, tin nhắn, và hội thoại.

Endpoints:
1. GET /api/admin/stats/users - Thống kê người dùng (Tổng, Đã xác thực, Chưa xác thực)
2. GET /api/admin/stats/conversations - Thống kê hội thoại (Tổng số đoạn chat, tin nhắn)
3. GET /api/admin/stats/all - Tổng hợp tất cả thống kê (Dashboard Overview)
"""

from flask_restx import Resource, Namespace, fields
from src.services.admin_service import get_total_users, get_conversation_stats, get_all_stats
from src.utils.auth_middleware import admin_required

# Khởi tạo Namespace
admin_ns = Namespace(
    'admin',
    description='Admin Dashboard - Thống kê và quản trị hệ thống'
)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@admin_ns.route('/stats/users')
class UserStats(Resource):
    """
    Endpoint thống kê User.
    URI: /api/admin/stats/users
    """
    
    @admin_ns.doc('get_user_statistics')
    @admin_ns.response(200, 'Success')
    @admin_ns.response(401, 'Unauthorized')
    @admin_ns.response(403, 'Forbidden - Không phải Admin')
    @admin_ns.doc(security='Bearer')
    @admin_required
    def get(self, current_user):
        """
        Lấy thống kê chi tiết về người dùng.
        - Tổng số user đăng ký.
        - Số user đã verify email.
        - Số user chưa verify.
        """
        result = get_total_users()
        
        if result['success']:
            return result, 200
        else:
            return result, 500


@admin_ns.route('/stats/conversations')
class ConversationStats(Resource):
    """
    Endpoint thống kê Hội thoại.
    URI: /api/admin/stats/conversations
    """
    
    @admin_ns.doc('get_conversation_statistics')
    @admin_ns.response(200, 'Success')
    @admin_ns.doc(security='Bearer')
    @admin_required
    def get(self, current_user):
        """
        Lấy thống kê về hoạt động chat.
        - Tổng số cuộc hội thoại (conversations).
        - Tổng số tin nhắn (messages).
        - Trung bình số tin nhắn / hội thoại.
        """
        result = get_conversation_stats()
        
        if result['success']:
            return result, 200
        else:
            return result, 500


@admin_ns.route('/stats/all')
class AllStats(Resource):
    """
    Endpoint Dashboard Overview.
    URI: /api/admin/stats/all
    """
    
    @admin_ns.doc('get_all_statistics')
    @admin_ns.response(200, 'Success')
    @admin_ns.doc(security='Bearer')
    @admin_required
    def get(self, current_user):
        """
        Lấy TẤT CẢ thống kê hệ thống (User + Chat).
        Dùng cho trang chủ Dashboard của Admin.
        """
        result = get_all_stats()
        
        if result['success']:
            return result, 200
        else:
            return result, 500
