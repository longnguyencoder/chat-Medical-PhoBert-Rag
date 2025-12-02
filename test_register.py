"""
Test Script - Đăng Ký Tài Khoản
================================
Test toàn bộ flow đăng ký: Register → Verify OTP → Login
"""

import requests
import json

BASE_URL = "http://localhost:5000/api/auth"

def test_register_flow():
    print("\n" + "="*60)
    print("TEST ĐĂNG KÝ TÀI KHOẢN")
    print("="*60)
    
    # Thông tin test
    test_email = "test_register_new@example.com"
    test_password = "password123"
    test_name = "Nguyễn Văn Test"
    
    # ========================================
    # BƯỚC 1: Đăng ký tài khoản
    # ========================================
    print("\n[1] Đăng ký tài khoản mới...")
    register_resp = requests.post(
        f"{BASE_URL}/register",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": test_name,
            "language_preference": "vi"
        }
    )
    
    print(f"Status: {register_resp.status_code}")
    print(f"Response: {json.dumps(register_resp.json(), indent=2, ensure_ascii=False)}")
    
    if register_resp.status_code != 200:
        print(f"❌ Đăng ký thất bại!")
        if "already registered" in register_resp.json().get('message', ''):
            print("⚠️ Email đã tồn tại. Thử email khác...")
        return
    
    print("✅ Đăng ký thành công! OTP đã được gửi.")
    
    # ========================================
    # BƯỚC 2: Nhập OTP để verify
    # ========================================
    print("\n[2] Verify OTP...")
    otp_code = input("Nhập OTP code từ email (hoặc check console log): ").strip()
    
    if not otp_code:
        print("⚠️ Bỏ qua bước verify OTP")
        return
    
    verify_resp = requests.post(
        f"{BASE_URL}/verify-otp",
        json={
            "email": test_email,
            "otp_code": otp_code,
            "purpose": "register"
        }
    )
    
    print(f"Status: {verify_resp.status_code}")
    print(f"Response: {json.dumps(verify_resp.json(), indent=2, ensure_ascii=False)}")
    
    if verify_resp.status_code != 200:
        print(f"❌ Verify OTP thất bại!")
        return
    
    print("✅ Verify OTP thành công!")
    
    # ========================================
    # BƯỚC 3: Đăng nhập
    # ========================================
    print("\n[3] Đăng nhập với tài khoản vừa tạo...")
    login_resp = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": test_email,
            "password": test_password
        }
    )
    
    print(f"Status: {login_resp.status_code}")
    
    if login_resp.status_code == 200:
        data = login_resp.json()
        print("✅ Đăng nhập thành công!")
        print(f"Token: {data['token'][:30]}...")
        print(f"User: {data['user']['full_name']}")
        print(f"Email: {data['user']['email']}")
    else:
        print(f"❌ Đăng nhập thất bại!")
        print(f"Response: {json.dumps(login_resp.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    try:
        test_register_flow()
        print("\n" + "="*60)
        print("✅ HOÀN THÀNH TEST ĐĂNG KÝ")
        print("="*60)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
