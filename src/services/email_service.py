from flask_mail import Message
from src.config.config import Config
from src import mail

def send_otp_email(email, otp_code, purpose):
    subject = 'Email Verification' if purpose == 'register' else 'Password Reset'
    msg = Message(subject,
                  sender=Config.MAIL_DEFAULT_SENDER,
                  recipients=[email])
    # HTML template cho email OTP
    msg.html = f'''
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; border: 1px solid #eee; border-radius: 8px; box-shadow: 0 2px 8px #f0f0f0; padding: 32px 24px; background: #fff;">
        <h2 style="color: #2d8cf0; text-align: center;">{subject}</h2>
        <p style="font-size: 16px; color: #333; text-align: center;">Your verification code is:</p>
        <div style="font-size: 32px; font-weight: bold; color: #2d8cf0; text-align: center; letter-spacing: 8px; margin: 24px 0;">{otp_code}</div>
        <p style="font-size: 15px; color: #555; text-align: center;">This code will expire in <b>1 minutes</b>.</p>
        <hr style="margin: 32px 0; border: none; border-top: 1px solid #eee;">
        <p style="font-size: 13px; color: #999; text-align: center;">If you did not request this code, please ignore this email.</p>
        <p style="font-size: 13px; color: #bbb; text-align: center; margin-top: 16px;">&copy; {subject} - Travel Assistant Chatbot</p>
    </div>
    '''
    msg.body = f"Your verification code is: {otp_code}\n\nThis code will expire in 1 minutes.\n\nIf you did not request this code, please ignore this email."
    mail.send(msg)

def send_notification_email(email, title, message, user_name):
    """
    Send notification email to user
    
    Args:
        email (str): User's email address
        title (str): Email title
        message (str): Email message content
        user_name (str): User's name
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        msg = Message(title,
                     sender=Config.MAIL_DEFAULT_SENDER,
                     recipients=[email])
        
        # Convert plain text to HTML with proper formatting
        html_message = message.replace('\n', '<br>')
        
        # HTML template cho notification email
        msg.html = f'''
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: auto; border: 1px solid #e0e0e0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 40px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <div style="background: white; border-radius: 8px; padding: 30px; color: #333;">
                <h1 style="color: #667eea; text-align: center; margin-bottom: 30px; font-size: 28px; font-weight: 600;">{title}</h1>
                
                <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
                    {html_message}
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <div style="display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px 30px; border-radius: 25px; font-weight: 600; font-size: 16px;">
                        🌟 Have a wonderful trip! 🌟
                    </div>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 2px solid #e0e0e0;">
                
                <div style="text-align: center; color: #666; font-size: 14px;">
                    <p style="margin: 5px 0;">This is an automated reminder from</p>
                    <p style="margin: 5px 0; font-weight: 600; color: #667eea;">Travel Assistant Chatbot</p>
                    <p style="margin: 5px 0; font-size: 12px;">Your AI-powered travel companion</p>
                </div>
            </div>
        </div>
        '''
        
        msg.body = message
        
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"Error sending notification email to {email}: {e}")
        return False

def send_medication_reminder_email(email, user_name, medication_name, dosage, scheduled_time):
    """
    Send medication reminder email to user
    
    Args:
        email (str): User's email address
        user_name (str): User's name
        medication_name (str): Name of medication
        dosage (str): Dosage information
        scheduled_time (str): Scheduled time (HH:MM format)
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        title = "💊 Nhắc nhở Uống thuốc"
        msg = Message(title,
                     sender=Config.MAIL_DEFAULT_SENDER,
                     recipients=[email])
        
        # HTML template cho medication reminder email
        msg.html = f'''
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: auto; border: 1px solid #e0e0e0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 40px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <div style="background: white; border-radius: 8px; padding: 30px; color: #333;">
                <h1 style="color: #667eea; text-align: center; margin-bottom: 20px; font-size: 28px; font-weight: 600;">💊 Nhắc nhở Uống thuốc</h1>
                
                <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
                    <p style="font-size: 18px; margin: 10px 0;"><strong>Xin chào {user_name},</strong></p>
                    <p style="font-size: 16px; margin: 10px 0;">Đây là lời nhắc uống thuốc của bạn:</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 15px 0; border: 2px solid #667eea;">
                        <p style="font-size: 20px; margin: 5px 0; color: #667eea;"><strong>📋 {medication_name}</strong></p>
                        <p style="font-size: 16px; margin: 5px 0; color: #666;">💊 Liều lượng: <strong>{dosage}</strong></p>
                        <p style="font-size: 16px; margin: 5px 0; color: #666;">⏰ Thời gian: <strong>{scheduled_time}</strong></p>
                    </div>
                    
                    <p style="font-size: 14px; margin: 15px 0; color: #666;">
                        ⚠️ Vui lòng uống thuốc đúng giờ để đảm bảo hiệu quả điều trị tốt nhất.
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <div style="display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px 30px; border-radius: 25px; font-weight: 600; font-size: 16px;">
                        🌟 Chúc bạn sức khỏe! 🌟
                    </div>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 2px solid #e0e0e0;">
                
                <div style="text-align: center; color: #666; font-size: 14px;">
                    <p style="margin: 5px 0;">Đây là email nhắc nhở tự động từ</p>
                    <p style="margin: 5px 0; font-weight: 600; color: #667eea;">Medical Chatbot</p>
                    <p style="margin: 5px 0; font-size: 12px;">Trợ lý sức khỏe thông minh của bạn</p>
                </div>
            </div>
        </div>
        '''
        
        msg.body = f"""
Nhắc nhở Uống thuốc

Xin chào {user_name},

Đây là lời nhắc uống thuốc của bạn:

Thuốc: {medication_name}
Liều lượng: {dosage}
Thời gian: {scheduled_time}

Vui lòng uống thuốc đúng giờ để đảm bảo hiệu quả điều trị tốt nhất.

Chúc bạn sức khỏe!

---
Medical Chatbot - Trợ lý sức khỏe thông minh của bạn
        """
        
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"Error sending medication reminder email to {email}: {e}")
        return False