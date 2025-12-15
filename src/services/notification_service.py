"""
Notification Service
====================
Service layer xử lý logic gửi và quản lý thông báo.

Chức năng:
1. Tạo thông báo (Nhắc thuốc, Nhắc lịch trình...).
2. Quản lý trạng thái thông báo (Đã đọc, Đã xóa).
3. Gửi thông báo qua Email (tích hợp email_service).
4. Truy vấn danh sách thông báo cho User.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from src.models.notification import Notification
from src.models.itinerary import Itinerary
from src.models.user import User
from src.models.base import db
from src.services.email_service import send_notification_email

# ============================================================================
# CREATION LOGIC (TẠO THÔNG BÁO)
# ============================================================================

def create_medication_reminder_notification(
    user_id: int, 
    medication_name: str, 
    time: str
) -> Tuple[bool, str]:
    """
    [NEW] Tạo thông báo nhắc uống thuốc.
    
    Args:
        user_id: ID người nhận
        medication_name: Tên thuốc
        time: Giờ uống (VD: 08:00)
    
    Returns:
        tuple (success, message)
    """
    try:
        # Tạo thông báo mới
        notification = Notification(
            user_id=user_id,
            title=f"Nhắc nhở uống thuốc: {medication_name}",
            message=f"Chào bạn, đã đến giờ uống thuốc {medication_name} ({time}). Hãy uống đúng giờ nhé!",
            notification_type='medication_reminder',
            scheduled_for=datetime.utcnow() # Gửi ngay (hoặc logic schedule tùy chỉnh)
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # Có thể gọi hàm send_notification ở đây nếu muốn gửi email ngay
        # send_notification(notification)
        
        return True, "Medication reminder created successfully"
    except Exception as e:
        db.session.rollback()
        return False, str(e)


def create_itinerary_reminder_notification(itinerary_id: int) -> Tuple[bool, str]:
    """
    [LEGACY] Tạo thông báo nhắc nhở lịch trình (từ dự án Chatbot Travel cũ).
    Vẫn giữ lại để tham khảo hoặc hỗ trợ tính năng liên quan đến lịch khám bệnh sau này.
    
    Args:
        itinerary_id: ID lịch trình
        
    Returns:
        tuple (success, message)
    """
    try:
        # Lấy thông tin lịch trình
        itinerary = Itinerary.query.get(itinerary_id)
        if not itinerary:
            return False, f"Itinerary with ID {itinerary_id} not found"
        
        # Tính thời gian nhắc: 1 ngày trước khi đi
        notification_time = datetime.combine(itinerary.selected_date, datetime.min.time()) - timedelta(days=1)
        
        # Kiểm tra thời gian có hợp lệ không
        if notification_time <= datetime.utcnow():
            return False, "Cannot create reminder for past or current date"
        
        # Kiểm tra xem đã có thông báo chưa (tránh spam)
        existing_notification = Notification.query.filter_by(
            itinerary_id=itinerary_id,
            notification_type='itinerary_reminder',
            is_deleted=False
        ).first()
        
        if existing_notification:
            return False, "Reminder notification already exists for this itinerary"
        
        # Tạo thông báo
        notification = Notification(
            user_id=itinerary.user_id,
            itinerary_id=itinerary_id,
            title=f"Reminder: Your itinerary for {itinerary.selected_date.strftime('%B %d, %Y')}",
            message=f"You have a planned itinerary for {itinerary.selected_date.strftime('%B %d, %Y')}. "
                   f"Don't forget to check your schedule!",
            notification_type='itinerary_reminder',
            scheduled_for=notification_time
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return True, f"Reminder notification scheduled for {notification_time.strftime('%Y-%m-%d %H:%M:%S')}"
        
    except Exception as e:
        db.session.rollback()
        return False, str(e)


# ============================================================================
# SENDING LOGIC (GỬI THÔNG BÁO)
# ============================================================================

def get_pending_notifications() -> List[Notification]:
    """
    Lấy danh sách các thông báo đang chờ gửi (scheduled_for <= now, chưa gửi).
    Hàm này thường được Scheduler gọi định kỳ.
    """
    now = datetime.utcnow()
    return Notification.query.filter(
        Notification.scheduled_for <= now,
        Notification.sent_at.is_(None),  # Chưa có thời gian gửi -> Chưa gửi
        Notification.is_deleted == False
    ).all()


def send_notification(notification: Notification) -> bool:
    """
    Thực hiện gửi thông báo (qua Email).
    
    Args:
        notification: Object Notification cần gửi
        
    Returns:
        bool: True nếu gửi thành công
    """
    try:
        # Lấy thông tin user để biết email
        user = User.query.get(notification.user_id)
        if not user:
            return False
        
        # Gọi Email Service
        success = send_notification_email(
            user.email,
            notification.title,
            notification.message,
            user.full_name
        )
        
        if success:
            # Cập nhật thời gian đã gửi
            notification.sent_at = datetime.utcnow()
            db.session.commit()
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error sending notification {notification.id}: {e}")
        return False


# ============================================================================
# USER INTERACTION (QUẢN LÝ CỦA USER)
# ============================================================================

def get_user_notifications(user_id: int, limit: int = 50) -> Tuple[bool, List[Dict[str, Any]] | str]:
    """
    Lấy danh sách thông báo của user.
    Hỗ trợ phân trang đơn giản bằng limit.
    """
    try:
        notifications = Notification.query.filter_by(
            user_id=user_id,
            is_deleted=False
        ).order_by(Notification.created_at.desc()).limit(limit).all()
        
        # Convert sang Dictionary
        result = [notification.to_dict() for notification in notifications]
        return True, result
        
    except Exception as e:
        return False, str(e)


def mark_notification_as_read(notification_id: int, user_id: int) -> Tuple[bool, str]:
    """Đánh dấu đã đọc."""
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            return False, "Notification not found"
        
        # Check quyền sở hữu
        if notification.user_id != user_id:
            return False, "Not authorized to modify this notification"
        
        notification.is_read = True
        db.session.commit()
        
        return True, "Notification marked as read"
        
    except Exception as e:
        db.session.rollback()
        return False, str(e)


def delete_notification(notification_id: int, user_id: int) -> Tuple[bool, str]:
    """Xóa thông báo (Soft Delete)."""
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            return False, "Notification not found"
        
        if notification.user_id != user_id:
            return False, "Not authorized to delete this notification"
        
        notification.is_deleted = True
        db.session.commit()
        
        return True, "Notification deleted successfully"
        
    except Exception as e:
        db.session.rollback()
        return False, str(e)