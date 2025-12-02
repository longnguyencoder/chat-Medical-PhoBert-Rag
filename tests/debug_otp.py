"""
Debug Script - Kiểm tra OTP trong Database
===========================================
"""

from src.config.config import Config
from src.models.base import db
from src.models.otp import OTP
from src.models.user import User
from main import create_app
from datetime import datetime

def check_otp_in_db():
    app = create_app()
    with app.app_context():
        print("\n" + "="*60)
        print("KIỂM TRA OTP TRONG DATABASE")
        print("="*60)
        
        # Lấy email vừa đăng ký
        email = input("\nNhập email vừa đăng ký: ").strip()
        
        # Kiểm tra User
        user = User.query.filter_by(email=email).first()
        if user:
            print(f"\n✅ User tồn tại:")
            print(f"   - ID: {user.user_id}")
            print(f"   - Name: {user.full_name}")
            print(f"   - Verified: {user.is_verified}")
        else:
            print(f"\n❌ User không tồn tại!")
            return
        
        # Kiểm tra OTP
        otps = OTP.query.filter_by(email=email, purpose='register').all()
        
        if not otps:
            print(f"\n❌ Không có OTP nào cho email này!")
            return
        
        print(f"\n✅ Tìm thấy {len(otps)} OTP record(s):")
        for i, otp in enumerate(otps, 1):
            print(f"\n   OTP #{i}:")
            print(f"   - Code: {otp.otp_code}")
            print(f"   - Purpose: {otp.purpose}")
            print(f"   - Is Used: {otp.is_used}")
            print(f"   - Expires At: {otp.expires_at}")
            print(f"   - Now: {datetime.utcnow()}")
            
            if otp.expires_at < datetime.utcnow():
                print(f"   ⚠️ OTP ĐÃ HẾT HẠN!")
            else:
                remaining = (otp.expires_at - datetime.utcnow()).total_seconds() / 60
                print(f"   ✅ Còn {remaining:.1f} phút")

if __name__ == "__main__":
    try:
        check_otp_in_db()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
