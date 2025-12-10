"""
Medication Service
==================
Business logic cho tính năng nhắc nhở uống thuốc.

Chức năng:
- Quản lý lịch uống thuốc (CRUD)
- Tự động tạo logs cho các lần uống thuốc
- Ghi nhận tuân thủ (đã uống/bỏ qua)
- Tính toán thống kê tuân thủ
"""

from datetime import datetime, timedelta, time
from typing import List, Dict, Optional
import pytz
from src.models.base import db
from src.models.medication_schedule import MedicationSchedule
from src.models.medication_log import MedicationLog
from src.models.user import User

# Múi giờ Việt Nam
VIETNAM_TZ = pytz.timezone('Asia/Ho_Chi_Minh')


def create_schedule(user_id: int, data: dict) -> MedicationSchedule:
    """
    Tạo lịch uống thuốc mới và tự động tạo logs cho 7 ngày tới.
    
    Args:
        user_id: ID người dùng
        data: Dictionary chứa thông tin lịch
            - medication_name (str): Tên thuốc
            - dosage (str, optional): Liều lượng
            - frequency (str): Tần suất (daily, twice_daily, etc.)
            - time_of_day (list): Danh sách thời gian ["08:00", "20:00"]
            - start_date (str, optional): Ngày bắt đầu (YYYY-MM-DD)
            - end_date (str, optional): Ngày kết thúc (YYYY-MM-DD)
            - notes (str, optional): Ghi chú
    
    Returns:
        MedicationSchedule: Lịch vừa tạo
    """
    # Tạo schedule
    schedule = MedicationSchedule(
        user_id=user_id,
        medication_name=data['medication_name'],
        dosage=data.get('dosage'),
        frequency=data.get('frequency', 'daily'),
        notes=data.get('notes'),
        is_active=True
    )
    
    # Set time_of_day
    schedule.set_time_of_day_list(data['time_of_day'])
    
    # Parse dates
    if 'start_date' in data:
        schedule.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    else:
        schedule.start_date = datetime.now(VIETNAM_TZ).date()
    
    if 'end_date' in data and data['end_date']:
        schedule.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    
    db.session.add(schedule)
    db.session.flush()  # Get schedule_id
    
    # Tạo logs cho 7 ngày tới
    _generate_logs_for_schedule(schedule, days=7)
    
    db.session.commit()
    return schedule


def update_schedule(schedule_id: int, user_id: int, data: dict) -> Optional[MedicationSchedule]:
    """
    Cập nhật lịch uống thuốc.
    
    Args:
        schedule_id: ID lịch
        user_id: ID người dùng (để verify ownership)
        data: Dictionary chứa thông tin cần cập nhật
    
    Returns:
        MedicationSchedule hoặc None nếu không tìm thấy
    """
    schedule = MedicationSchedule.query.filter_by(
        schedule_id=schedule_id,
        user_id=user_id
    ).first()
    
    if not schedule:
        return None
    
    # Update fields
    if 'medication_name' in data:
        schedule.medication_name = data['medication_name']
    if 'dosage' in data:
        schedule.dosage = data['dosage']
    if 'frequency' in data:
        schedule.frequency = data['frequency']
    if 'time_of_day' in data:
        schedule.set_time_of_day_list(data['time_of_day'])
    if 'start_date' in data:
        schedule.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    if 'end_date' in data:
        if data['end_date']:
            schedule.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        else:
            schedule.end_date = None
    if 'notes' in data:
        schedule.notes = data['notes']
    if 'is_active' in data:
        schedule.is_active = data['is_active']
    
    # Regenerate future logs if time changed
    if 'time_of_day' in data:
        _delete_future_pending_logs(schedule)
        _generate_logs_for_schedule(schedule, days=7)
    
    db.session.commit()
    return schedule


def delete_schedule(schedule_id: int, user_id: int) -> bool:
    """
    Xóa lịch uống thuốc (soft delete bằng cách set is_active=False).
    
    Args:
        schedule_id: ID lịch
        user_id: ID người dùng
    
    Returns:
        bool: True nếu xóa thành công
    """
    schedule = MedicationSchedule.query.filter_by(
        schedule_id=schedule_id,
        user_id=user_id
    ).first()
    
    if not schedule:
        return False
    
    schedule.is_active = False
    db.session.commit()
    return True


def get_schedules_by_user(user_id: int, include_inactive: bool = False) -> List[MedicationSchedule]:
    """
    Lấy danh sách lịch uống thuốc của user.
    
    Args:
        user_id: ID người dùng
        include_inactive: Có lấy cả lịch đã tắt không
    
    Returns:
        List[MedicationSchedule]
    """
    query = MedicationSchedule.query.filter_by(user_id=user_id)
    
    if not include_inactive:
        query = query.filter_by(is_active=True)
    
    return query.order_by(MedicationSchedule.created_at.desc()).all()


def get_schedule_by_id(schedule_id: int, user_id: int) -> Optional[MedicationSchedule]:
    """
    Lấy chi tiết 1 lịch.
    
    Args:
        schedule_id: ID lịch
        user_id: ID người dùng
    
    Returns:
        MedicationSchedule hoặc None
    """
    return MedicationSchedule.query.filter_by(
        schedule_id=schedule_id,
        user_id=user_id
    ).first()


def record_medication_taken(log_id: int, user_id: int, note: Optional[str] = None) -> Optional[MedicationLog]:
    """
    Ghi nhận đã uống thuốc.
    
    Args:
        log_id: ID log
        user_id: ID người dùng
        note: Ghi chú (optional)
    
    Returns:
        MedicationLog hoặc None
    """
    log = MedicationLog.query.filter_by(log_id=log_id, user_id=user_id).first()
    
    if not log:
        return None
    
    log.mark_as_taken(note)
    db.session.commit()
    return log


def record_medication_skipped(log_id: int, user_id: int, note: Optional[str] = None) -> Optional[MedicationLog]:
    """
    Ghi nhận bỏ qua uống thuốc.
    
    Args:
        log_id: ID log
        user_id: ID người dùng
        note: Ghi chú lý do (optional)
    
    Returns:
        MedicationLog hoặc None
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
    Lấy lịch sử uống thuốc của user.
    
    Args:
        user_id: ID người dùng
        start_date: Ngày bắt đầu filter (YYYY-MM-DD)
        end_date: Ngày kết thúc filter (YYYY-MM-DD)
    
    Returns:
        List[MedicationLog]
    """
    query = MedicationLog.query.filter_by(user_id=user_id)
    
    if start_date:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(MedicationLog.scheduled_time >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(MedicationLog.scheduled_time < end_dt)
    
    return query.order_by(MedicationLog.scheduled_time.desc()).all()


def get_compliance_stats(user_id: int, days: int = 30) -> Dict:
    """
    Tính toán thống kê tuân thủ uống thuốc.
    
    Args:
        user_id: ID người dùng
        days: Số ngày gần đây để tính (mặc định 30 ngày)
    
    Returns:
        Dict chứa thống kê:
        {
            'total': int,
            'taken': int,
            'skipped': int,
            'pending': int,
            'compliance_rate': float (%)
        }
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
    
    # Tính compliance rate (chỉ tính trên các log đã có kết quả)
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
    Lấy danh sách thuốc sắp uống trong X giờ tới (cho chatbot).
    
    Args:
        user_id: ID người dùng
        hours: Số giờ tới (mặc định 24h)
    
    Returns:
        List[Dict] chứa thông tin thuốc sắp uống
    """
    now = datetime.now(VIETNAM_TZ)
    end_time = now + timedelta(hours=hours)
    
    logs = MedicationLog.query.join(MedicationSchedule).filter(
        MedicationLog.user_id == user_id,
        MedicationLog.status == 'pending',
        MedicationLog.scheduled_time >= now,
        MedicationLog.scheduled_time <= end_time,
        MedicationSchedule.is_active == True
    ).order_by(MedicationLog.scheduled_time).all()
    
    result = []
    for log in logs:
        result.append({
            'log_id': log.log_id,
            'medication_name': log.schedule.medication_name,
            'dosage': log.schedule.dosage,
            'scheduled_time': log.scheduled_time.astimezone(VIETNAM_TZ).strftime('%H:%M'),
            'notes': log.schedule.notes
        })
    
    return result


# ============================================================================
# PRIVATE HELPER FUNCTIONS
# ============================================================================

def _generate_logs_for_schedule(schedule: MedicationSchedule, days: int = 7):
    """
    Tạo logs cho lịch uống thuốc trong X ngày tới.
    
    Args:
        schedule: MedicationSchedule object
        days: Số ngày tạo logs
    """
    now = datetime.now(VIETNAM_TZ)
    start_date = max(schedule.start_date, now.date())
    
    time_list = schedule.get_time_of_day_list()
    
    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        
        # Kiểm tra có vượt quá end_date không
        if schedule.end_date and current_date > schedule.end_date:
            break
        
        # Tạo log cho mỗi thời gian trong ngày
        for time_str in time_list:
            hour, minute = map(int, time_str.split(':'))
            scheduled_dt = VIETNAM_TZ.localize(
                datetime.combine(current_date, time(hour, minute))
            )
            
            # Chỉ tạo log cho thời gian trong tương lai
            if scheduled_dt > now:
                log = MedicationLog(
                    schedule_id=schedule.schedule_id,
                    user_id=schedule.user_id,
                    scheduled_time=scheduled_dt.astimezone(pytz.utc),  # Lưu UTC trong DB
                    status='pending'
                )
                db.session.add(log)


def _delete_future_pending_logs(schedule: MedicationSchedule):
    """
    Xóa các logs pending trong tương lai của lịch (khi update time).
    
    Args:
        schedule: MedicationSchedule object
    """
    now = datetime.now(VIETNAM_TZ)
    
    MedicationLog.query.filter(
        MedicationLog.schedule_id == schedule.schedule_id,
        MedicationLog.status == 'pending',
        MedicationLog.scheduled_time > now
    ).delete()
