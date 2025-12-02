"""
Test Script - Đăng Ký Tài Khoản (Email Mới)
============================================
"""

import requests
import json
import random

BASE_URL = "http://localhost:5000/api/auth"

def test_register_with_new_email():
    print("\n" + "="*60)
    print("TEST ĐĂNG KÝ TÀI KHOẢN - EMAIL MỚI")
    print("="*60)
    
    # Tạo email ngẫu nhiên để tránh trùng
    random_num = random.randint(1000, 9999)
    test_email = f"test_user_{random_num}@example.com"
    test_password = "password123"
    test_name = f"User Test {random_num}"
    
    print(f"\nEmail: {test_email}")
    print(f"Name: {test_name}")
    
    # ========================================
    # BƯỚC 1: Đăng ký
    # ========================================
    print("\n[1] Đăng ký tài khoản...")
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
    
    if register_resp.status_code == 200:
        print("✅ Đăng ký thành công!")
        print(f"Response: {register_resp.json()}")
        print("\n⚠️ Kiểm tra email để lấy OTP code!")
    else:
        print(f"❌ Lỗi: {register_resp.text}")
        return
    
    # ========================================
    # BƯỚC 2: Verify OTP (manual)
    # ========================================
    print("\n[2] Nhập OTP để verify...")
    print("(Kiểm tra email hoặc server console)")

if __name__ == "__main__":
    try:
        test_register_with_new_email()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
