"""
Scheduler Service
=================
Background scheduler sử dụng APScheduler để tự động:
1. Gửi email nhắc nhở uống thuốc (30 phút trước)
2. Chatbot tự động hỏi "Đã uống thuốc chưa?" cuối ngày (21:00)
3. Cleanup logs cũ (hàng ngày lúc 00:00)

Scheduler sẽ chạy trong background khi server khởi động.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import pytz
import logging
from src.models.base import db
from src.models.medication_schedule import MedicationSchedule
from src.models.medication_log import MedicationLog
from src.models.user import User
from src.models.message import Message
from src.models.conversation import Conversation
from src.services.email_service import send_medication_reminder_email

logger = logging.getLogger(__name__)

# Múi giờ Việt Nam
VIETNAM_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

# Global scheduler instance
scheduler = None


def init_scheduler(app):
    """
    Khởi tạo và start scheduler.
    
    Args:
        app: Flask app instance (cần để có app context)
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already initialized")
        return
    
    scheduler = BackgroundScheduler(timezone=VIETNAM_TZ)
    
    # Job 1: Kiểm tra và gửi email nhắc nhở (chạy mỗi phút)
    scheduler.add_job(
        func=lambda: check_and_send_medication_reminders(app),
        trigger='interval',
        minutes=1,
        id='medication_reminder_job',
        name='Check and send medication reminder emails',
        replace_existing=True
    )
    
    # Job 2: Chatbot hỏi cuối ngày (chạy lúc 21:00 mỗi ngày)
    scheduler.add_job(
        func=lambda: chatbot_daily_check(app),
        trigger='cron',
        hour=21,
        minute=0,
        id='chatbot_daily_check_job',
        name='Chatbot daily medication check',
        replace_existing=True
    )
    
    # Job 3: Cleanup logs cũ (chạy lúc 00:00 mỗi ngày)
    scheduler.add_job(
        func=lambda: cleanup_old_logs(app),
        trigger='cron',
        hour=0,
        minute=0,
        id='cleanup_logs_job',
        name='Cleanup old medication logs',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Medication reminder scheduler started successfully")
    logger.info(f"   - Email reminders: Every 1 minute")
    logger.info(f"   - Daily chatbot check: 21:00 GMT+7")
    logger.info(f"   - Cleanup old logs: 00:00 GMT+7")


def shutdown_scheduler():
    """
    Tắt scheduler khi server shutdown.
    """
    global scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler shut down")


def check_and_send_medication_reminders(app):
    """
    Job chạy mỗi phút để kiểm tra và gửi email nhắc nhở.
    
    Logic:
    - Tìm các logs có scheduled_time trong khoảng 30-31 phút nữa
    - Gửi email nhắc nhở cho user
    - Đánh dấu đã gửi (để không gửi lại)
    
    Args:
        app: Flask app instance
    """
    with app.app_context():
        try:
            now = datetime.now(VIETNAM_TZ)
            
            # Tìm logs cần nhắc nhở (30-31 phút nữa)
            reminder_start = now + timedelta(minutes=30)
            reminder_end = now + timedelta(minutes=31)
            
            # Query logs cần gửi email
            logs = db.session.query(MedicationLog).join(
                MedicationSchedule
            ).join(
                User
            ).filter(
                MedicationLog.status == 'pending',
                MedicationLog.scheduled_time >= reminder_start.astimezone(pytz.utc),
                MedicationLog.scheduled_time < reminder_end.astimezone(pytz.utc),
                MedicationSchedule.is_active == True
            ).all()
            
            if not logs:
                logger.debug(f"No medication reminders to send at {now.strftime('%H:%M')}")
                return
            
            logger.info(f"📧 Sending {len(logs)} medication reminder emails...")
            
            sent_count = 0
            for log in logs:
                try:
                    schedule = log.schedule
                    user = log.user
                    
                    # Format thời gian
                    scheduled_time_vn = log.scheduled_time.astimezone(VIETNAM_TZ)
                    time_str = scheduled_time_vn.strftime('%H:%M')
                    
                    # Gửi email
                    success = send_medication_reminder_email(
                        email=user.email,
                        user_name=user.full_name,
                        medication_name=schedule.medication_name,
                        dosage=schedule.dosage or "Theo chỉ định",
                        scheduled_time=time_str
                    )
                    
                    if success:
                        sent_count += 1
                        logger.info(f"   ✅ Sent reminder to {user.email} for {schedule.medication_name} at {time_str}")
                    else:
                        logger.error(f"   ❌ Failed to send reminder to {user.email}")
                        
                except Exception as e:
                    logger.error(f"Error sending reminder for log {log.log_id}: {e}")
            
            logger.info(f"📧 Sent {sent_count}/{len(logs)} medication reminder emails")
            
        except Exception as e:
            logger.error(f"Error in check_and_send_medication_reminders: {e}", exc_info=True)


def chatbot_daily_check(app):
    """
    Job chạy lúc 21:00 mỗi ngày để chatbot tự động hỏi "Đã uống thuốc chưa?".
    
    Logic:
    - Tìm tất cả users có lịch uống thuốc active
    - Tạo message tự động trong conversation của họ
    - Message sẽ xuất hiện trong chat khi họ mở app
    
    Args:
        app: Flask app instance
    """
    with app.app_context():
        try:
            logger.info("🤖 Running daily chatbot medication check...")
            
            # Tìm tất cả users có lịch uống thuốc active
            users_with_schedules = db.session.query(User).join(
                MedicationSchedule
            ).filter(
                MedicationSchedule.is_active == True
            ).distinct().all()
            
            if not users_with_schedules:
                logger.info("   No users with active medication schedules")
                return
            
            message_count = 0
            for user in users_with_schedules:
                try:
                    # Tìm hoặc tạo conversation cho user
                    conversation = Conversation.query.filter_by(
                        user_id=user.user_id
                    ).order_by(Conversation.created_at.desc()).first()
                    
                    if not conversation:
                        # Tạo conversation mới nếu chưa có
                        conversation = Conversation(
                            user_id=user.user_id,
                            title="Nhắc nhở uống thuốc"
                        )
                        db.session.add(conversation)
                        db.session.flush()
                    
                    # Tạo message tự động từ chatbot
                    bot_message = Message(
                        conversation_id=conversation.conversation_id,
                        sender='bot',
                        content=f"Chào {user.full_name}! 🌙\n\nHôm nay bạn đã uống thuốc đầy đủ chưa? Hãy cho tôi biết để tôi ghi nhận nhé! 💊\n\n✅ Đã uống đầy đủ\n⏭️ Bỏ qua một số liều\n❌ Chưa uống",
                        timestamp=datetime.utcnow()
                    )
                    db.session.add(bot_message)
                    message_count += 1
                    
                    logger.info(f"   ✅ Created daily check message for {user.email}")
                    
                except Exception as e:
                    logger.error(f"Error creating message for user {user.user_id}: {e}")
            
            db.session.commit()
            logger.info(f"🤖 Created {message_count} daily check messages")
            
        except Exception as e:
            logger.error(f"Error in chatbot_daily_check: {e}", exc_info=True)
            db.session.rollback()


def cleanup_old_logs(app):
    """
    Job chạy lúc 00:00 mỗi ngày để xóa logs cũ hơn 90 ngày.
    
    Args:
        app: Flask app instance
    """
    with app.app_context():
        try:
            logger.info("🧹 Cleaning up old medication logs...")
            
            cutoff_date = datetime.now(VIETNAM_TZ) - timedelta(days=90)
            
            # Xóa logs cũ hơn 90 ngày
            deleted_count = MedicationLog.query.filter(
                MedicationLog.scheduled_time < cutoff_date.astimezone(pytz.utc)
            ).delete()
            
            db.session.commit()
            logger.info(f"🧹 Deleted {deleted_count} old medication logs (older than 90 days)")
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_logs: {e}", exc_info=True)
            db.session.rollback()
