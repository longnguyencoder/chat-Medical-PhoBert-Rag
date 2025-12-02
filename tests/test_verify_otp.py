"""
Test Verify OTP
===============
"""

import requests
import json

BASE_URL = "http://localhost:5000/api/auth"

def test_verify_otp():
    print("\n" + "="*60)
    print("TEST VERIFY OTP")
    print("="*60)
    
    # Nhập thông tin
    email = input("\nNhập email: ").strip()
    otp_code = input("Nhập OTP code (6 chữ số): ").strip()
    
    print(f"\n📧 Email: {email}")
    print(f"🔢 OTP: {otp_code}")
    print(f"📏 Length: {len(otp_code)}")
    
    # Gọi API
    print("\nGọi API /verify-otp...")
    resp = requests.post(
        f"{BASE_URL}/verify-otp",
        json={
            "email": email,
            "otp_code": otp_code,
            "purpose": "register"
        }
    )
    
    print(f"\nStatus: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
    
    if resp.status_code == 200:
        print("\n✅ VERIFY THÀNH CÔNG!")
    else:
        print("\n❌ VERIFY THẤT BẠI!")
        print("\nKiểm tra:")
        print("1. Email có đúng không?")
        print("2. OTP có đúng 6 chữ số không?")
        print("3. OTP có hết hạn chưa? (10 phút)")

if __name__ == "__main__":
    try:
        test_verify_otp()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
