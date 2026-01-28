"""
Medication Controller
=====================
REST API endpoints để quản lý lịch uống thuốc và theo dõi việc tuân thủ uống thuốc.
Đây là tính năng cốt lõi giúp nhắc nhở bệnh nhân uống thuốc đúng giờ.

Endpoints chính:
1. Quản lý Lịch (Schedule): Tạo, sửa, xóa lịch uống thuốc (VD: Paracetamol, 8:00 sáng hàng ngày).
2. Quản lý Nhật ký (Logs): Ghi nhận kết quả uống (Đã uống, Bỏ qua) cho từng lần nhắc.
3. Thống kê (Stats): Xem tỷ lệ tuân thủ để bác sĩ/người thân theo dõi.

Toàn bộ API đều được bảo vệ bằng JWT Token.
"""

from flask import request
from flask_restx import Namespace, Resource, fields  # Thư viện hỗ trợ tạo API chuẩn RESTful và Swagger Document
import logging
from src.services import medication_service  # Service xử lý logic nghiệp vụ
from src.utils.auth_middleware import token_required  # Middleware kiểm tra đăng nhập
from src.models.base import db  # Database session

logger = logging.getLogger(__name__)

# Tạo Namespace 'medication' -> đường dẫn gốc sẽ là /api/medication
medication_ns = Namespace(
    'medication',
    description='Medication Reminder - Quản lý lịch uống thuốc và nhắc nhở'
)

# ============================================================================
# API MODELS (Định nghĩa cấu trúc dữ liệu cho Swagger UI & Validation)
# ============================================================================

# Model Input: Dữ liệu user gửi lên khi tạo/sửa lịch uống thuốc
medication_schedule_input = medication_ns.model('MedicationScheduleInput', {
    'medication_name': fields.String(
        required=True,
        description='Tên thuốc (bắt buộc)',
        example='Paracetamol'
    ),
    'dosage': fields.String(
        description='Liều lượng (VD: 1 viên, 500mg)',
        example='500mg'
    ),
    'frequency': fields.String(
        description='Tần suất lặp lại (daily, weekly...) - Mặc định là daily',
        example='daily',
        default='daily'
    ),
    'time_of_day': fields.List(
        fields.String,
        required=True,
        description='Danh sách thời gian uống trong ngày (định dạng HH:MM)',
        example=['08:00', '20:00']
    ),
    'start_date': fields.String(
        description='Ngày bắt đầu uống (YYYY-MM-DD)',
        example='2025-12-10'
    ),
    'end_date': fields.String(
        description='Ngày kết thúc đợt thuốc (YYYY-MM-DD, có thể để trống nếu uống dài hạn)',
        example='2025-12-31'
    ),
    'notes': fields.String(
        description='Ghi chú thêm (VD: Uống sau ăn)',
        example='Uống sau ăn'
    )
})

# Model Output: Dữ liệu lịch uống thuốc trả về cho Client
medication_schedule_output = medication_ns.model('MedicationScheduleOutput', {
    'schedule_id': fields.Integer(description='ID duy nhất của lịch'),
    'user_id': fields.Integer(description='ID người dùng sở hữu'),
    'medication_name': fields.String(description='Tên thuốc'),
    'dosage': fields.String(description='Liều lượng'),
    'frequency': fields.String(description='Tần suất'),
    'time_of_day': fields.List(fields.String, description='Các giờ uống trong ngày'),
    'start_date': fields.String(description='Ngày bắt đầu'),
    'end_date': fields.String(description='Ngày kết thúc'),
    'notes': fields.String(description='Ghi chú'),
    'is_active': fields.Boolean(description='Trạng thái kích hoạt (True=Đang dùng, False=Đã dừng/Xóa)'),
    'created_at': fields.String(description='Thời gian tạo'),
    'updated_at': fields.String(description='Thời gian cập nhật')
})

# Model Input: Dữ liệu khi user đánh dấu đã uống thuốc (Check-in)
medication_log_input = medication_ns.model('MedicationLogInput', {
    'log_id': fields.Integer(
        required=True,
        description='ID của lần nhắc thuốc cụ thể (Log ID)',
        example=1
    ),
    'status': fields.String(
        required=True,
        description='Trạng thái cập nhật: `taken` (đã uống) hoặc `skipped` (bỏ qua)',
        example='taken',
        enum=['taken', 'skipped']
    ),
    'note': fields.String(
        description='Ghi chú lý do (VD: Quên mang thuốc, Tác dụng phụ...)',
        example='Uống muộn 30 phút'
    )
})

# Model Output: Dữ liệu chi tiết một lần nhắc thuốc
medication_log_output = medication_ns.model('MedicationLogOutput', {
    'log_id': fields.Integer(description='ID log'),
    'schedule_id': fields.Integer(description='ID lịch gốc'),
    'user_id': fields.Integer(description='ID người dùng'),
    'scheduled_time': fields.String(description='Thời gian dự kiến uống (theo lịch)'),
    'actual_time': fields.String(description='Thời gian thực tế user bấm xác nhận'),
    'status': fields.String(description='Trạng thái: pending (chờ), taken (đã uống), skipped (bỏ qua)'),
    'note': fields.String(description='Ghi chú của người dùng'),
    'is_overdue': fields.Boolean(description='Cờ đánh dấu đã quá giờ uống chưa'),
    'created_at': fields.String(description='Thời gian tạo bản ghi'),
    'updated_at': fields.String(description='Thời gian cập nhật bản ghi')
})

# Model Output: Thống kê tuân thủ điều trị
compliance_stats_output = medication_ns.model('ComplianceStatsOutput', {
    'total': fields.Integer(description='Tổng số lần phải uống'),
    'taken': fields.Integer(description='Số lần đã uống đúng hạn/muộn'),
    'skipped': fields.Integer(description='Số lần chủ động bỏ qua'),
    'pending': fields.Integer(description='Số lần đang chờ (chưa đến giờ hoặc chưa confirm)'),
    'compliance_rate': fields.Float(description='Tỷ lệ tuân thủ (%) - Công thức: Taken / (Taken + Skipped)')
})


# ============================================================================
# API ENDPOINTS - MEDICATION SCHEDULES (QUẢN LÝ LỊCH)
# ============================================================================

@medication_ns.route('/schedules')
class MedicationScheduleList(Resource):
    """
    Endpoint quản lý danh sách lịch uống thuốc.
    URI: /api/medication/schedules
    """
    
    @medication_ns.response(200, 'Success', [medication_schedule_output])
    @medication_ns.response(401, 'Unauthorized - Cần JWT token')
    @medication_ns.doc(security='Bearer')
    @token_required
    def get(self, current_user):
        """
        Lấy danh sách TOÀN BỘ lịch uống thuốc của user hiện tại.
        Bao gồm cả lịch đang active và inactive (tùy logic service).
        """
        try:
            user_id = current_user['user_id']
            # Gọi service lấy danh sách
            schedules = medication_service.get_schedules_by_user(user_id)
            
            # Convert sang dict để trả về JSON
            return {
                'message': 'Success',
                'count': len(schedules),
                'schedules': [s.to_dict() for s in schedules]
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting medication schedules: {e}", exc_info=True)
            return {'message': f'Internal server error: {str(e)}'}, 500
    
    @medication_ns.expect(medication_schedule_input)  # Validate body
    @medication_ns.response(201, 'Created', medication_schedule_output)
    @medication_ns.response(400, 'Bad Request - Thiếu trường bắt buộc')
    @medication_ns.response(401, 'Unauthorized')
    @medication_ns.doc(security='Bearer')
    @token_required
    def post(self, current_user):
        """
        Tạo lịch uống thuốc mới.
        
        Logic quan trọng:
        - Khi tạo lịch, hệ thống sẽ TỰ ĐỘNG tạo ra các Log nhắc nhở (MedicationLog) cho 7 ngày tới.
        - Giúp App không cần tính toán local, chỉ cần query Log là biết hôm nay uống gì.
        """
        try:
            user_id = current_user['user_id']
            data = request.json
            
            if not data:
                return {'message': 'Request body is required'}, 400
            
            # Kiểm tra trường bắt buộc
            if 'medication_name' not in data or 'time_of_day' not in data:
                return {'message': 'medication_name and time_of_day are required'}, 400
            
            # Gọi service để tạo lịch + sinh logs tự động
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
    Endpoint quản lý chi tiết 1 lịch uống thuốc cụ thể.
    URI: /api/medication/schedules/{id}
    """
    
    @medication_ns.response(200, 'Success', medication_schedule_output)
    @medication_ns.response(404, 'Schedule not found')
    @medication_ns.response(401, 'Unauthorized')
    @medication_ns.doc(security='Bearer')
    @token_required
    def get(self, current_user, schedule_id):
        """Lấy chi tiết 1 lịch uống thuốc."""
        try:
            user_id = current_user['user_id']
            # Lấy chi tiết và kiểm tra quyền sở hữu
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
        
        Lưu ý: Nếu thay đổi giờ uống (time_of_day), hệ thống sẽ phải:
        1. Xóa các Logs chưa uống (pending) trong tương lai.
        2. Tạo lại Logs mới theo giờ mới.
        """
        try:
            user_id = current_user['user_id']
            data = request.json
            
            if not data:
                return {'message': 'Request body is required'}, 400
            
            # Update schedule
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
            # Ghi log chi tiết để debug
            logger.error(f"❌ Error updating schedule {schedule_id} for user {user_id}")
            logger.error(f"Request data: {data}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            db.session.rollback()
            return {'message': f'Internal server error: {str(e)}'}, 500
    
    @medication_ns.response(200, 'Deleted')
    @medication_ns.response(404, 'Schedule not found')
    @medication_ns.response(401, 'Unauthorized')
    @medication_ns.doc(security='Bearer')
    @token_required
    def delete(self, current_user, schedule_id):
        """
        Xóa lịch uống thuốc.
        Thực tế là "Soft Delete" (đánh dấu is_active = False) để giữ lại lịch sử.
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
# API ENDPOINTS - MEDICATION LOGS (NHẬT KÝ UỐNG THUỐC)
# ============================================================================

@medication_ns.route('/logs')
class MedicationLogList(Resource):
    """
    Endpoint quản lý lịch sử/nhật ký uống thuốc.
    URI: /api/medication/logs
    """
    
    @medication_ns.response(200, 'Success', [medication_log_output])
    @medication_ns.response(401, 'Unauthorized')
    @medication_ns.doc(security='Bearer')
    @medication_ns.param('start_date', 'Ngày bắt đầu filter (YYYY-MM-DD)', type='string')
    @medication_ns.param('end_date', 'Ngày kết thúc filter (YYYY-MM-DD)', type='string')
    @token_required
    def get(self, current_user):
        """
        Lấy danh sách các lần nhắc uống thuốc (Logs).
        Thường dùng để hiển thị Calendar hoặc danh sách "Hôm nay".
        
        Query Params:
        - start_date, end_date: Dùng để lọc theo khoảng thời gian.
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
        API quan trọng: Đánh dấu đã uống thuốc (Check-in).
        
        Client có thể gửi lên theo 2 cách:
        1. Cách chuẩn: log_id + status
        2. Cách thay thế: schedule_id + scheduled_time + status (hệ thống sẽ tự tìm log_id)
        """
        try:
            user_id = current_user['user_id']
            data = request.json
            
            # Debug logging
            logger.info(f"📥 Received medication log request from user {user_id}")
            logger.info(f"📦 Request data: {data}")
            
            # Hỗ trợ cả log_id (snake_case) và logId (camelCase từ Flutter)
            raw_log_id = data.get('log_id') or data.get('logId')
            schedule_id = data.get('schedule_id') or data.get('scheduleId')
            scheduled_time_str = data.get('scheduled_time') or data.get('scheduledTime')
            status = data.get('status')
            note = data.get('note')
            
            # CASE 1: Client gửi schedule_id + scheduled_time thay vì log_id
            # Cần tìm log_id tương ứng từ schedule_id và scheduled_time
            if not raw_log_id and schedule_id and scheduled_time_str:
                logger.info(f"🔍 Client sent schedule_id={schedule_id} + scheduled_time={scheduled_time_str}, finding log_id...")
                
                from src.models.medication_log import MedicationLog
                from datetime import datetime
                import pytz
                
                # Parse scheduled_time (có thể là ISO format với milliseconds)
                try:
                    # Xử lý format: '2026-01-24T08:00:00.000' hoặc '2026-01-24T08:00:00'
                    if '.' in scheduled_time_str:
                        scheduled_time_str = scheduled_time_str.split('.')[0]  # Bỏ milliseconds
                    
                    # Parse thành datetime (giả sử client gửi theo múi giờ VN)
                    scheduled_dt = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
                    
                    # Nếu không có timezone info, giả sử là VN timezone
                    if scheduled_dt.tzinfo is None:
                        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
                        scheduled_dt = vietnam_tz.localize(scheduled_dt)
                    
                    # Tìm log tương ứng với schedule_id và scheduled_time
                    # Cho phép sai lệch ±5 phút để xử lý trường hợp làm tròn thời gian
                    from datetime import timedelta
                    time_tolerance = timedelta(minutes=5)
                    
                    matching_log = MedicationLog.query.filter(
                        MedicationLog.schedule_id == schedule_id,
                        MedicationLog.user_id == user_id,
                        MedicationLog.scheduled_time >= scheduled_dt - time_tolerance,
                        MedicationLog.scheduled_time <= scheduled_dt + time_tolerance
                    ).first()
                    
                    if matching_log:
                        raw_log_id = matching_log.log_id
                        logger.info(f"✅ Found matching log_id={raw_log_id}")
                    else:
                        logger.info(f"🔍 No pre-generated log found. Checking if we should create one on-the-fly...")
                        
                        from src.models.medication_schedule import MedicationSchedule
                        schedule = MedicationSchedule.query.filter_by(
                            schedule_id=schedule_id, 
                            user_id=user_id
                        ).first()
                        
                        if not schedule:
                            return {'message': f'Medication schedule {schedule_id} not found or access denied'}, 404
                        
                        # Verify the time matches the schedule's time_of_day
                        target_time_str = scheduled_dt.strftime('%H:%M')
                        valid_times = schedule.get_time_of_day_list()
                        
                        if target_time_str not in valid_times:
                            return {
                                'message': f'Scheduled time {target_time_str} is not valid for this schedule',
                                'valid_times': valid_times,
                                'received': target_time_str
                            }, 400
                        
                        # Create the log on-the-fly
                        logger.info(f"✨ Creating new log for schedule {schedule_id} at {scheduled_dt}")
                        new_log = MedicationLog(
                            schedule_id=schedule_id,
                            user_id=user_id,
                            scheduled_time=scheduled_dt.astimezone(pytz.utc),
                            status='pending'  # Will be updated to 'taken'/'skipped' below
                        )
                        db.session.add(new_log)
                        db.session.flush() # To get the auto-incremented log_id
                        raw_log_id = new_log.log_id
                        
                except Exception as parse_error:
                    logger.error(f"❌ Error logic in on-the-fly creation: {parse_error}", exc_info=True)
                    return {
                        'message': f'Error processing request: {str(parse_error)}'
                    }, 500
            
            # CASE 2: Validation - Phải có log_id hoặc (schedule_id + scheduled_time)
            if not raw_log_id or not status:
                logger.warning(f"❌ Missing required fields. Received data: {data}")
                return {
                    'message': 'Required: (log_id OR schedule_id+scheduled_time) AND status',
                    'received_data': data,
                    'required_fields': {
                        'option_1': ['log_id', 'status'],
                        'option_2': ['schedule_id', 'scheduled_time', 'status']
                    },
                    'hint': 'Make sure to send JSON with Content-Type: application/json'
                }, 400
            
            # EXPLICIT TYPE CASTING: Ensure log_id is an integer
            try:
                log_id = int(raw_log_id)
            except (ValueError, TypeError):
                 return {'message': f'log_id must be an integer, got {type(raw_log_id)}: {raw_log_id}'}, 400

            if status not in ['taken', 'skipped']:
                return {'message': 'status must be either "taken" or "skipped"'}, 400
            
            logger.info(f"✅ Processing: log_id={log_id}, status={status}, note={note}")
            
            # Gọi service ghi nhận trạng thái
            if status == 'taken':
                log = medication_service.record_medication_taken(log_id, user_id, note)
            else:
                log = medication_service.record_medication_skipped(log_id, user_id, note)
            
            if not log:
                # DEBUGGING 404: Find out WHY it failed
                from src.models.medication_log import MedicationLog
                debug_log = MedicationLog.query.get(log_id)
                
                reason = "Unknown error"
                if not debug_log:
                     reason = f"Log ID {log_id} does not exist in database"
                     logger.error(f"❌ 404 REASON: {reason}")
                elif debug_log.user_id != user_id:
                     reason = f"Log ID {log_id} belongs to user {debug_log.user_id}, NOT current user {user_id}"
                     logger.error(f"❌ 404 REASON: {reason}")
                else:
                     reason = f"Log {log_id} exists and belongs to user {user_id}, but service returned None (Logic Error)"
                     logger.error(f"❌ 404 REASON: {reason}")
                
                return {
                    'message': 'Medication log not found (or access denied)',
                    'debug_reason': reason
                }, 404
            
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
    Endpoint thống kê tuân thủ.
    URI: /api/medication/logs/stats
    """
    
    @medication_ns.response(200, 'Success', compliance_stats_output)
    @medication_ns.response(401, 'Unauthorized')
    @medication_ns.doc(security='Bearer')
    @medication_ns.param('days', 'Số ngày gần đây để tính (mặc định 30)', type='int', default=30)
    @token_required
    def get(self, current_user):
        """
        Tính toán tỷ lệ tuân thủ trong X ngày qua.
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


@medication_ns.route('/logs/upcoming')
class MedicationUpcoming(Resource):
    """
    Endpoint tiện ích: Lấy danh sách thuốc SẮP PHẢI UỐNG.
    Dùng cho Feature Widget hoặc thông báo nhanh ngoài trang chủ.
    """
    
    @medication_ns.response(200, 'Success')
    @medication_ns.response(401, 'Unauthorized')
    @medication_ns.doc(security='Bearer')
    @medication_ns.param('hours', 'Số giờ tới (mặc định 24)', type='int', default=24)
    @token_required
    def get(self, current_user):
        """
        Lấy danh sách các liều thuốc cần uống trong vòng X giờ tới.
        """
        try:
            user_id = current_user['user_id']
            hours = int(request.args.get('hours', 24))
            
            upcoming = medication_service.get_upcoming_medications(user_id, hours)
            
            return {
                'message': 'Success',
                'count': len(upcoming),
                'upcoming': upcoming
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting upcoming medications: {e}", exc_info=True)
            return {'message': f'Internal server error: {str(e)}'}, 500
