"""
Check OTP in Database - Quick Debug
====================================
"""

from src.config.config import Config
from src.models.base import db
from src.models.otp import OTP
from src.models.user import User
from main import create_app
from datetime import datetime

app = create_app()
with app.app_context():
    email = "giupviecgiahoang8@gmail.com"
    
    print("\n" + "="*60)
    print(f"KIỂM TRA OTP CHO: {email}")
    print("="*60)
    
    # Check User
    user = User.query.filter_by(email=email).first()
    if user:
        print(f"\n✅ User exists:")
        print(f"   ID: {user.user_id}")
        print(f"   Name: {user.full_name}")
        print(f"   Verified: {user.is_verified}")
    else:
        print(f"\n❌ User NOT found!")
    
    # Check OTP
    print(f"\n🔍 Checking OTP records...")
    otps = OTP.query.filter_by(email=email).all()
    
    if not otps:
        print("❌ NO OTP records found!")
    else:
        print(f"✅ Found {len(otps)} OTP(s):")
        for otp in otps:
            print(f"\n   Code: {otp.otp_code}")
            print(f"   Purpose: {otp.purpose}")
            print(f"   Used: {otp.is_used}")
            print(f"   Expires: {otp.expires_at}")
            print(f"   Now: {datetime.utcnow()}")
            
            if otp.expires_at < datetime.utcnow():
                print(f"   ⚠️ EXPIRED!")
            else:
                mins = (otp.expires_at - datetime.utcnow()).total_seconds() / 60
                print(f"   ✅ Valid for {mins:.1f} more minutes")
