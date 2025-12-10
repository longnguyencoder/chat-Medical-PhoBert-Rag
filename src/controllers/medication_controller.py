"""
Medication Controller
=====================
REST API endpoints để quản lý lịch uống thuốc và lịch sử tuân thủ.

Endpoints:
- POST /api/medication/schedules - Tạo lịch mới
- GET /api/medication/schedules - Lấy danh sách lịch
- GET /api/medication/schedules/{id} - Lấy chi tiết 1 lịch
- PUT /api/medication/schedules/{id} - Cập nhật lịch
- DELETE /api/medication/schedules/{id} - Xóa lịch
- POST /api/medication/logs - Ghi nhận đã uống/bỏ qua
- GET /api/medication/logs - Lấy lịch sử
- GET /api/medication/logs/stats - Thống kê tuân thủ

Tất cả endpoints đều yêu cầu JWT authentication.
"""

from flask import request
from flask_restx import Namespace, Resource, fields
import logging
from src.services import medication_service
from src.utils.auth_middleware import token_required
from src.models.base import db

logger = logging.getLogger(__name__)

# Tạo namespace cho Medication API
medication_ns = Namespace(
    'medication',
    description='Medication Reminder - Quản lý lịch uống thuốc và nhắc nhở'
)

# ============================================================================
# API MODELS (Định nghĩa cấu trúc request/response cho Swagger UI)
# ============================================================================

# Model cho request tạo/cập nhật lịch
medication_schedule_input = medication_ns.model('MedicationScheduleInput', {
    'medication_name': fields.String(
        required=True,
        description='Tên thuốc',
        example='Paracetamol'
    ),
    'dosage': fields.String(
        description='Liều lượng',
        example='500mg'
    ),
    'frequency': fields.String(
        description='Tần suất: daily, twice_daily, three_times_daily, weekly, custom',
        example='daily',
        default='daily'
    ),
    'time_of_day': fields.List(
        fields.String,
        required=True,
        description='Thời gian trong ngày (HH:MM)',
        example=['08:00', '20:00']
    ),
    'start_date': fields.String(
        description='Ngày bắt đầu (YYYY-MM-DD)',
        example='2025-12-10'
    ),
    'end_date': fields.String(
        description='Ngày kết thúc (YYYY-MM-DD, nullable)',
        example='2025-12-31'
    ),
    'notes': fields.String(
        description='Ghi chú',
        example='Uống sau ăn'
    )
})

# Model cho response lịch uống thuốc
medication_schedule_output = medication_ns.model('MedicationScheduleOutput', {
    'schedule_id': fields.Integer(description='ID lịch'),
    'user_id': fields.Integer(description='ID người dùng'),
    'medication_name': fields.String(description='Tên thuốc'),
    'dosage': fields.String(description='Liều lượng'),
    'frequency': fields.String(description='Tần suất'),
    'time_of_day': fields.List(fields.String, description='Thời gian trong ngày'),
    'start_date': fields.String(description='Ngày bắt đầu'),
    'end_date': fields.String(description='Ngày kết thúc'),
    'notes': fields.String(description='Ghi chú'),
    'is_active': fields.Boolean(description='Trạng thái kích hoạt'),
    'created_at': fields.String(description='Thời gian tạo'),
    'updated_at': fields.String(description='Thời gian cập nhật')
})

# Model cho request ghi nhận log
medication_log_input = medication_ns.model('MedicationLogInput', {
    'log_id': fields.Integer(
        required=True,
        description='ID log cần cập nhật',
        example=1
    ),
    'status': fields.String(
        required=True,
        description='Trạng thái: taken hoặc skipped',
        example='taken',
        enum=['taken', 'skipped']
    ),
    'note': fields.String(
        description='Ghi chú',
        example='Uống muộn 30 phút'
    )
})

# Model cho response log
medication_log_output = medication_ns.model('MedicationLogOutput', {
    'log_id': fields.Integer(description='ID log'),
    'schedule_id': fields.Integer(description='ID lịch'),
    'user_id': fields.Integer(description='ID người dùng'),
    'scheduled_time': fields.String(description='Thời gian dự kiến'),
    'actual_time': fields.String(description='Thời gian thực tế'),
    'status': fields.String(description='Trạng thái: pending, taken, skipped'),
    'note': fields.String(description='Ghi chú'),
    'is_overdue': fields.Boolean(description='Có quá hạn không'),
    'created_at': fields.String(description='Thời gian tạo'),
    'updated_at': fields.String(description='Thời gian cập nhật')
})

# Model cho thống kê
compliance_stats_output = medication_ns.model('ComplianceStatsOutput', {
    'total': fields.Integer(description='Tổng số lần'),
    'taken': fields.Integer(description='Số lần đã uống'),
    'skipped': fields.Integer(description='Số lần bỏ qua'),
    'pending': fields.Integer(description='Số lần đang chờ'),
    'compliance_rate': fields.Float(description='Tỷ lệ tuân thủ (%)')
})


# ============================================================================
# API ENDPOINTS - MEDICATION SCHEDULES
# ============================================================================

@medication_ns.route('/schedules')
class MedicationScheduleList(Resource):
    """
    Endpoint quản lý danh sách lịch uống thuốc.
    """
    
    @medication_ns.response(200, 'Success', [medication_schedule_output])
    @medication_ns.response(401, 'Unauthorized - Cần JWT token')
    @medication_ns.doc(security='Bearer')
    @token_required
    def get(self, current_user):
        """
        Lấy danh sách lịch uống thuốc của user hiện tại.
        
        Returns:
            List[MedicationSchedule]
        """
        try:
            user_id = current_user['user_id']
            schedules = medication_service.get_schedules_by_user(user_id)
            
            return {
                'message': 'Success',
                'count': len(schedules),
                'schedules': [s.to_dict() for s in schedules]
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting medication schedules: {e}", exc_info=True)
            return {'message': f'Internal server error: {str(e)}'}, 500
    
    @medication_ns.expect(medication_schedule_input)
    @medication_ns.response(201, 'Created', medication_schedule_output)
    @medication_ns.response(400, 'Bad Request')
    @medication_ns.response(401, 'Unauthorized')
    @medication_ns.doc(security='Bearer')
    @token_required
    def post(self, current_user):
        """
        Tạo lịch uống thuốc mới.
        
        Lịch sẽ tự động tạo logs cho 7 ngày tới.
        
        Returns:
            MedicationSchedule vừa tạo
        """
        try:
            user_id = current_user['user_id']
            data = request.json
            
            if not data:
                return {'message': 'Request body is required'}, 400
            
            # Validate required fields
            if 'medication_name' not in data or 'time_of_day' not in data:
                return {'message': 'medication_name and time_of_day are required'}, 400
            
            # Tạo schedule
            schedule = medication_service.create_schedule(user_id, data)
            
            return {
                'message': 'Medication schedule created successfully',
                'schedule': schedule.to_dict()
            }, 201
            
        except ValueError as e:
            logger.warning(f"Validation error: {e}")
            return {'message': str(e)}, 400
            
        except Exception as e:
            logger.error(f"Error creating medication schedule: {e}", exc_info=True)
            db.session.rollback()
            return {'message': f'Internal server error: {str(e)}'}, 500


@medication_ns.route('/schedules/<int:schedule_id>')
class MedicationScheduleDetail(Resource):
    """
    Endpoint quản lý chi tiết 1 lịch uống thuốc.
    """
    
    @medication_ns.response(200, 'Success', medication_schedule_output)
    @medication_ns.response(404, 'Schedule not found')
    @medication_ns.response(401, 'Unauthorized')
    @medication_ns.doc(security='Bearer')
    @token_required
    def get(self, current_user, schedule_id):
        """
        Lấy chi tiết 1 lịch uống thuốc.
        
        Args:
            schedule_id: ID lịch
        
        Returns:
            MedicationSchedule
        """
        try:
            user_id = current_user['user_id']
            schedule = medication_service.get_schedule_by_id(schedule_id, user_id)
            
            if not schedule:
                return {'message': 'Medication schedule not found'}, 404
            
            return schedule.to_dict(), 200
            
        except Exception as e:
            logger.error(f"Error getting medication schedule: {e}", exc_info=True)
            return {'message': f'Internal server error: {str(e)}'}, 500
    
    @medication_ns.expect(medication_schedule_input)
    @medication_ns.response(200, 'Updated', medication_schedule_output)
    @medication_ns.response(404, 'Schedule not found')
    @medication_ns.response(400, 'Bad Request')
    @medication_ns.response(401, 'Unauthorized')
    @medication_ns.doc(security='Bearer')
    @token_required
    def put(self, current_user, schedule_id):
        """
        Cập nhật lịch uống thuốc.
        
        Nếu thay đổi time_of_day, logs trong tương lai sẽ được regenerate.
        
        Args:
            schedule_id: ID lịch
        
        Returns:
            MedicationSchedule đã cập nhật
        """
        try:
            user_id = current_user['user_id']
            data = request.json
            
            if not data:
                return {'message': 'Request body is required'}, 400
            
            # Cập nhật schedule
            schedule = medication_service.update_schedule(schedule_id, user_id, data)
            
            if not schedule:
                return {'message': 'Medication schedule not found'}, 404
            
            return {
                'message': 'Medication schedule updated successfully',
                'schedule': schedule.to_dict()
            }, 200
            
        except ValueError as e:
            logger.warning(f"Validation error: {e}")
            return {'message': str(e)}, 400
            
        except Exception as e:
            logger.error(f"Error updating medication schedule: {e}", exc_info=True)
            db.session.rollback()
            return {'message': f'Internal server error: {str(e)}'}, 500
    
    @medication_ns.response(200, 'Deleted')
    @medication_ns.response(404, 'Schedule not found')
    @medication_ns.response(401, 'Unauthorized')
    @medication_ns.doc(security='Bearer')
    @token_required
    def delete(self, current_user, schedule_id):
        """
        Xóa lịch uống thuốc (soft delete).
        
        Args:
            schedule_id: ID lịch
        
        Returns:
            Thông báo xóa thành công
        """
        try:
            user_id = current_user['user_id']
            success = medication_service.delete_schedule(schedule_id, user_id)
            
            if not success:
                return {'message': 'Medication schedule not found'}, 404
            
            return {'message': 'Medication schedule deleted successfully'}, 200
            
        except Exception as e:
            logger.error(f"Error deleting medication schedule: {e}", exc_info=True)
            db.session.rollback()
            return {'message': f'Internal server error: {str(e)}'}, 500


# ============================================================================
# API ENDPOINTS - MEDICATION LOGS
# ============================================================================

@medication_ns.route('/logs')
class MedicationLogList(Resource):
    """
    Endpoint quản lý lịch sử uống thuốc.
    """
    
    @medication_ns.response(200, 'Success', [medication_log_output])
    @medication_ns.response(401, 'Unauthorized')
    @medication_ns.doc(security='Bearer')
    @medication_ns.param('start_date', 'Ngày bắt đầu filter (YYYY-MM-DD)', type='string')
    @medication_ns.param('end_date', 'Ngày kết thúc filter (YYYY-MM-DD)', type='string')
    @token_required
    def get(self, current_user):
        """
        Lấy lịch sử uống thuốc của user.
        
        Query params:
        - start_date: Ngày bắt đầu (YYYY-MM-DD)
        - end_date: Ngày kết thúc (YYYY-MM-DD)
        
        Returns:
            List[MedicationLog]
        """
        try:
            user_id = current_user['user_id']
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            logs = medication_service.get_logs_by_user(user_id, start_date, end_date)
            
            return {
                'message': 'Success',
                'count': len(logs),
                'logs': [log.to_dict() for log in logs]
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting medication logs: {e}", exc_info=True)
            return {'message': f'Internal server error: {str(e)}'}, 500
    
    @medication_ns.expect(medication_log_input)
    @medication_ns.response(200, 'Updated', medication_log_output)
    @medication_ns.response(404, 'Log not found')
    @medication_ns.response(400, 'Bad Request')
    @medication_ns.response(401, 'Unauthorized')
    @medication_ns.doc(security='Bearer')
    @token_required
    def post(self, current_user):
        """
        Ghi nhận đã uống hoặc bỏ qua thuốc.
        
        Body:
        - log_id: ID log cần cập nhật
        - status: 'taken' hoặc 'skipped'
        - note: Ghi chú (optional)
        
        Returns:
            MedicationLog đã cập nhật
        """
        try:
            user_id = current_user['user_id']
            data = request.json
            
            if not data or 'log_id' not in data or 'status' not in data:
                return {'message': 'log_id and status are required'}, 400
            
            log_id = data['log_id']
            status = data['status']
            note = data.get('note')
            
            if status not in ['taken', 'skipped']:
                return {'message': 'status must be either "taken" or "skipped"'}, 400
            
            # Ghi nhận log
            if status == 'taken':
                log = medication_service.record_medication_taken(log_id, user_id, note)
            else:
                log = medication_service.record_medication_skipped(log_id, user_id, note)
            
            if not log:
                return {'message': 'Medication log not found'}, 404
            
            return {
                'message': f'Medication marked as {status}',
                'log': log.to_dict()
            }, 200
            
        except Exception as e:
            logger.error(f"Error recording medication log: {e}", exc_info=True)
            db.session.rollback()
            return {'message': f'Internal server error: {str(e)}'}, 500


@medication_ns.route('/logs/stats')
class MedicationLogStats(Resource):
    """
    Endpoint thống kê tuân thủ uống thuốc.
    """
    
    @medication_ns.response(200, 'Success', compliance_stats_output)
    @medication_ns.response(401, 'Unauthorized')
    @medication_ns.doc(security='Bearer')
    @medication_ns.param('days', 'Số ngày gần đây để tính (mặc định 30)', type='int', default=30)
    @token_required
    def get(self, current_user):
        """
        Lấy thống kê tuân thủ uống thuốc.
        
        Query params:
        - days: Số ngày gần đây (mặc định 30)
        
        Returns:
            Thống kê: total, taken, skipped, pending, compliance_rate
        """
        try:
            user_id = current_user['user_id']
            days = int(request.args.get('days', 30))
            
            stats = medication_service.get_compliance_stats(user_id, days)
            
            return {
                'message': 'Success',
                'period_days': days,
                'stats': stats
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting compliance stats: {e}", exc_info=True)
            return {'message': f'Internal server error: {str(e)}'}, 500
