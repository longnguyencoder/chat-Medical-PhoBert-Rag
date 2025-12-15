"""
Medication Service
==================
Business Logic Layer xử lý toàn bộ logic liên quan đến nhắc nhở uống thuốc.

Chức năng chính:
1. Quản lý Lịch (CRUD): Tạo lịch, sửa lịch, xóa lịch.
2. Sinh Log tự động (`_generate_logs_for_schedule`):
   - Khi tạo lịch, hệ thống tự tính toán các mốc thời gian (VD: 8:00, 20:00) cho 7 ngày tới.
   - Lưu trước vào bảng `MedicationLog` với trạng thái `pending`.
3. Cập nhật trạng thái (`record_medication_taken/skipped`): Khi user check-in.
4. Thống kê tuân thủ (`get_compliance_stats`): Tính % uống đúng giờ.

Tại sao cần sinh Log trước?
- Để App Mobile có thể query danh sách "Hôm nay phải uống gì" dễ dàng mà không cần thuật toán phức tạp ở Client.
- Để hệ thống scheduler có thể quét DB và gửi thông báo Notification dễ dàng.
"""

from datetime import datetime, timedelta, time
from typing import List, Dict, Optional
import pytz
from src.models.base import db
from src.models.medication_schedule import MedicationSchedule
from src.models.medication_log import MedicationLog
from src.models.user import User

# Múi giờ Việt Nam - Quan trọng để tính ngày giờ nhắc thuốc chính xác
VIETNAM_TZ = pytz.timezone('Asia/Ho_Chi_Minh')


# ============================================================================
# SCHEDULE MANAGEMENT (QUẢN LÝ LỊCH)
# ============================================================================

def create_schedule(user_id: int, data: dict) -> MedicationSchedule:
    """
    Tạo một lịch uống thuốc mới.
    Đồng thời tự động kích hoạt tiến trình tạo Logs nhắc nhở cho tương lai.
    
    Args:
        user_id: ID người tạo
        data: Dữ liệu từ Controller (medication_name, time_of_day, frequency...)
    
    Returns:
        MedicationSchedule object vừa tạo
    """
    # 1. Khởi tạo đối tượng Schedule
    schedule = MedicationSchedule(
        user_id=user_id,
        medication_name=data['medication_name'],
        dosage=data.get('dosage'),
        frequency=data.get('frequency', 'daily'),
        notes=data.get('notes'),
        is_active=True  # Mặc định kích hoạt ngay
    )
    
    # 2. Set danh sách giờ uống (Method này handle việc chuyển list -> JSON string)
    schedule.set_time_of_day_list(data['time_of_day'])
    
    # 3. Parse ngày bắt đầu/kết thúc
    if 'start_date' in data and data['start_date']:
        schedule.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    else:
        # Mặc định bắt đầu từ hôm nay
        schedule.start_date = datetime.now(VIETNAM_TZ).date()
    
    if 'end_date' in data and data['end_date']:
        schedule.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    
    # Lưu Schedule vào DB trước để có ID
    db.session.add(schedule)
    db.session.flush()  # Commit tạm để lấy schedule.schedule_id
    
    # 4. QUAN TRỌNG: Sinh Logs nhắc nhở cho 7 ngày tiếp theo
    _generate_logs_for_schedule(schedule, days=7)
    
    db.session.commit()
    return schedule


def update_schedule(schedule_id: int, user_id: int, data: dict) -> Optional[MedicationSchedule]:
    """
    Cập nhật thông tin lịch uống thuốc.
    Nếu user đổi giờ uống, cần xóa Logs cũ chưa uống và tạo Logs mới.
    """
    schedule = MedicationSchedule.query.filter_by(
        schedule_id=schedule_id,
        user_id=user_id
    ).first()
    
    if not schedule:
        return None
    
    # Cập nhật các trường thông tin đơn giản
    if 'medication_name' in data:
        schedule.medication_name = data['medication_name']
    if 'dosage' in data:
        schedule.dosage = data['dosage']
    if 'frequency' in data:
        schedule.frequency = data['frequency']
    if 'notes' in data:
        schedule.notes = data['notes']
    if 'is_active' in data:
        schedule.is_active = data['is_active']
        
    if 'start_date' in data and data['start_date']:
        schedule.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        
    if 'end_date' in data:
        if data['end_date']:
            schedule.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        else:
            schedule.end_date = None

    # XỬ LÝ ĐẶC BIỆT KHI THAY ĐỔI GIỜ UỐNG
    time_changed = False
    if 'time_of_day' in data:
        new_times = sorted(data['time_of_day'])
        old_times = sorted(schedule.get_time_of_day_list())
        if new_times != old_times:
            schedule.set_time_of_day_list(data['time_of_day'])
            time_changed = True
    
    # Nếu giờ thay đổi:
    # 1. Xóa các log tương lai chưa thực hiện (vì sai giờ rồi)
    # 2. Sinh lại log theo giờ mới
    if time_changed:
        _delete_future_pending_logs(schedule)
        _generate_logs_for_schedule(schedule, days=7)
    
    db.session.commit()
    return schedule


def delete_schedule(schedule_id: int, user_id: int) -> bool:
    """
    Soft Delete: Chỉ set is_active = False chứ không xóa khỏi DB.
    Giúp giữ lại lịch sử đã uống thuốc để thống kê.
    """
    schedule = MedicationSchedule.query.filter_by(
        schedule_id=schedule_id,
        user_id=user_id
    ).first()
    
    if not schedule:
        return False
    
    schedule.is_active = False
    
    # Tùy chọn: Có thể xóa các log pending tương lai để không nhắc nữa
    _delete_future_pending_logs(schedule)
    
    db.session.commit()
    return True


def get_schedules_by_user(user_id: int, include_inactive: bool = False) -> List[MedicationSchedule]:
    """Lấy danh sách lịch uống thuốc của user."""
    query = MedicationSchedule.query.filter_by(user_id=user_id)
    
    if not include_inactive:
        # Mặc định chỉ lấy các lịch đang hoạt động
        query = query.filter_by(is_active=True)
    
    return query.order_by(MedicationSchedule.created_at.desc()).all()


def get_schedule_by_id(schedule_id: int, user_id: int) -> Optional[MedicationSchedule]:
    """Lấy chi tiết 1 lịch (kiểm tra đúng chủ sở hữu)."""
    return MedicationSchedule.query.filter_by(
        schedule_id=schedule_id,
        user_id=user_id
    ).first()


# ============================================================================
# LOGGING & TRACKING (GHI NHẬN TRẠNG THÁI)
# ============================================================================

def record_medication_taken(log_id: int, user_id: int, note: Optional[str] = None) -> Optional[MedicationLog]:
    """
    User xác nhận đã uống thuốc (Mark as Taken).
    """
    log = MedicationLog.query.filter_by(log_id=log_id, user_id=user_id).first()
    
    if not log:
        return None
    
    # Hàm mark_as_taken trong model sẽ cập nhật status='taken' và actual_time=Now
    log.mark_as_taken(note)
    db.session.commit()
    return log


def record_medication_skipped(log_id: int, user_id: int, note: Optional[str] = None) -> Optional[MedicationLog]:
    """
    User xác nhận bỏ qua liều thuốc này (Mark as Skipped).
    """
    log = MedicationLog.query.filter_by(log_id=log_id, user_id=user_id).first()
    
    if not log:
        return None
    
    log.mark_as_skipped(note)
    db.session.commit()
    return log


def get_logs_by_user(user_id: int, start_date: Optional[str] = None, 
                     end_date: Optional[str] = None) -> List[MedicationLog]:
    """
    Lấy danh sách Logs để hiển thị lên lịch/danh sách.
    Hỗ trợ lọc theo khoảng ngày.
    """
    query = MedicationLog.query.filter_by(user_id=user_id)
    
    if start_date:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(MedicationLog.scheduled_time >= start_dt)
    
    if end_date:
        # End date phải cộng thêm 1 ngày để lấy hết ngày đó (vì DB lưu datetime)
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(MedicationLog.scheduled_time < end_dt)
    
    return query.order_by(MedicationLog.scheduled_time.desc()).all()


def get_compliance_stats(user_id: int, days: int = 30) -> Dict:
    """
    Tính toán thống kê tuân thủ trong X ngày gần nhất.
    """
    start_date = datetime.now(VIETNAM_TZ) - timedelta(days=days)
    
    logs = MedicationLog.query.filter(
        MedicationLog.user_id == user_id,
        MedicationLog.scheduled_time >= start_date
    ).all()
    
    total = len(logs)
    taken = sum(1 for log in logs if log.status == 'taken')
    skipped = sum(1 for log in logs if log.status == 'skipped')
    pending = sum(1 for log in logs if log.status == 'pending')
    
    # Công thức tỷ lệ tuân thủ: Đã uống / (Đã uống + Bỏ qua)
    # Không tính các liều 'pending' (vì chưa đến giờ hoặc chưa action)
    completed = taken + skipped
    compliance_rate = (taken / completed * 100) if completed > 0 else 0
    
    return {
        'total': total,
        'taken': taken,
        'skipped': skipped,
        'pending': pending,
        'compliance_rate': round(compliance_rate, 2)
    }


def get_upcoming_medications(user_id: int, hours: int = 24) -> List[Dict]:
    """
    Lấy các liều thuốc sắp đến giờ uống.
    Hữu ích cho Widget hoặc màn hình Home của Chatbot.
    """
    now = datetime.now(VIETNAM_TZ)
    end_time = now + timedelta(hours=hours)
    
    # Join bảng Logs với Schedule để lấy tên thuốc
    logs = MedicationLog.query.join(MedicationSchedule).filter(
        MedicationLog.user_id == user_id,
        MedicationLog.status == 'pending', # Chỉ lấy cái chưa uống
        MedicationLog.scheduled_time >= now,
        MedicationLog.scheduled_time <= end_time,
        MedicationSchedule.is_active == True # Lịch phải đang active
    ).order_by(MedicationLog.scheduled_time).all()
    
    result = []
    for log in logs:
        scheduled_vn = log.scheduled_time.astimezone(VIETNAM_TZ)
        
        # Logic hiển thị nhãn ngày (Hôm nay, Ngày mai...)
        today = now.date()
        scheduled_date = scheduled_vn.date()
        
        if scheduled_date == today:
            date_label = "Hôm nay"
        elif scheduled_date == today + timedelta(days=1):
            date_label = "Ngày mai"
        else:
            date_label = scheduled_vn.strftime('%d/%m/%Y')
        
        result.append({
            'log_id': log.log_id,
            'schedule_id': log.schedule_id,
            'medication_name': log.schedule.medication_name,
            'dosage': log.schedule.dosage,
            'scheduled_time': scheduled_vn.isoformat(),
            'time': scheduled_vn.strftime('%H:%M'),
            'date': scheduled_vn.strftime('%Y-%m-%d'),
            'date_label': date_label,
            'display': f"{date_label} {scheduled_vn.strftime('%H:%M')}",
            'notes': log.schedule.notes
        })
    
    return result


# ============================================================================
# PRIVATE HELPER FUNCTIONS
# ============================================================================

def _generate_logs_for_schedule(schedule: MedicationSchedule, days: int = 7):
    """
    Logic sinh logs tự động (Core Logic).
    Duyệt qua từng ngày từ start_date -> start_date + days.
    Duyệt qua từng khung giờ trong time_of_day.
    Nếu thời gian đó > hiện tại -> Tạo Log pending.
    """
    now = datetime.now(VIETNAM_TZ)
    # Bắt đầu từ ngày start_date của lịch, hoặc hôm nay (nếu start_date < hôm nay)
    start_date = max(schedule.start_date, now.date())
    
    time_list = schedule.get_time_of_day_list()  # ['08:00', '20:00']
    
    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        
        # Nếu đã quá end_date của lịch thì dừng
        if schedule.end_date and current_date > schedule.end_date:
            break
        
        # Duyệt qua từng giờ uống
        for time_str in time_list:
            hour, minute = map(int, time_str.split(':'))
            
            # Kết hợp ngày + giờ thành datetime (có múi giờ VN)
            scheduled_dt = VIETNAM_TZ.localize(
                datetime.combine(current_date, time(hour, minute))
            )
            
            # Chỉ tạo log nếu thời điểm đó chưa qua
            if scheduled_dt > now:
                log = MedicationLog(
                    schedule_id=schedule.schedule_id,
                    user_id=schedule.user_id,
                    scheduled_time=scheduled_dt.astimezone(pytz.utc),  # DB lưu UTC chuẩn
                    status='pending'
                )
                db.session.add(log)


def _delete_future_pending_logs(schedule: MedicationSchedule):
    """
    Xóa các logs trạng thái 'pending' trong tương lai.
    Dùng khi user sửa đổi lịch hoặc xóa lịch.
    """
    now = datetime.now(VIETNAM_TZ)
    
    MedicationLog.query.filter(
        MedicationLog.schedule_id == schedule.schedule_id,
        MedicationLog.status == 'pending',  # Chỉ xóa cái chưa uống
        MedicationLog.scheduled_time > now  # Chỉ xóa tương lai
    ).delete()
