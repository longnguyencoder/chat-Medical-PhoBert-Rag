"""
Test Script - JWT Authentication
=================================
Script này test tính năng JWT authentication cho chatbot API.

Test cases:
1. Login để lấy token
2. Gọi /chat-secure với token hợp lệ → Success
3. Gọi /chat-secure không có token → 401
4. Gọi /chat-secure với token sai → 401
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_jwt_authentication():
    print("\n" + "="*60)
    print("TEST JWT AUTHENTICATION")
    print("="*60)
    
    # ========================================
    # BƯỚC 1: Đăng nhập để lấy token
    # ========================================
    print("\n[1] Đăng nhập để lấy JWT token...")
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "test_user_named@example.com",
            "password": "hashed_password"  # Thay bằng password thật
        }
    )
    
    if login_resp.status_code != 200:
        print(f"❌ Login thất bại: {login_resp.json()}")
        print("⚠️ Hãy tạo user trước bằng /auth/register")
        return
    
    token = login_resp.json()['token']
    print(f"✅ Login thành công!")
    print(f"Token: {token[:30]}...")
    
    # ========================================
    # BƯỚC 2: Chat với token hợp lệ
    # ========================================
    print("\n[2] Gọi /chat-secure VỚI token...")
    chat_resp = requests.post(
        f"{BASE_URL}/medical-chatbot/chat-secure",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "Triệu chứng cảm cúm là gì?"}
    )
    
    print(f"Status: {chat_resp.status_code}")
    if chat_resp.status_code == 200:
        data = chat_resp.json()
        print(f"✅ PASS: Chat thành công!")
        print(f"User: {data.get('user_info', {}).get('name')}")
        print(f"Answer: {data['answer'][:80]}...")
    else:
        print(f"❌ FAIL: {chat_resp.json()}")
    
    # ========================================
    # BƯỚC 3: Chat KHÔNG CÓ token
    # ========================================
    print("\n[3] Gọi /chat-secure KHÔNG CÓ token...")
    no_token_resp = requests.post(
        f"{BASE_URL}/medical-chatbot/chat-secure",
        json={"question": "Test"}
    )
    
    print(f"Status: {no_token_resp.status_code}")
    if no_token_resp.status_code == 401:
        print(f"✅ PASS: Đúng là bị từ chối (401)")
        print(f"Message: {no_token_resp.json()['message']}")
    else:
        print(f"❌ FAIL: Không nên cho phép truy cập!")
    
    # ========================================
    # BƯỚC 4: Chat với token SAI
    # ========================================
    print("\n[4] Gọi /chat-secure với token SAI...")
    fake_token_resp = requests.post(
        f"{BASE_URL}/medical-chatbot/chat-secure",
        headers={"Authorization": "Bearer fake_token_123"},
        json={"question": "Test"}
    )
    
    print(f"Status: {fake_token_resp.status_code}")
    if fake_token_resp.status_code == 401:
        print(f"✅ PASS: Token giả bị từ chối")
        print(f"Message: {fake_token_resp.json()['message']}")
    else:
        print(f"❌ FAIL: Token giả không nên được chấp nhận!")
    
    # ========================================
    # SO SÁNH: API cũ vs API mới
    # ========================================
    print("\n" + "="*60)
    print("SO SÁNH: /chat (cũ) vs /chat-secure (mới)")
    print("="*60)
    
    print("\n✅ /chat (không JWT):")
    print("   - Cần truyền: user_id trong body")
    print("   - Bảo mật: ❌ Ai cũng fake được user_id")
    print("   - Dùng cho: Test, demo nội bộ")
    
    print("\n✅ /chat-secure (có JWT):")
    print("   - Cần truyền: Token trong header")
    print("   - Bảo mật: ✅ Không fake được")
    print("   - Dùng cho: Production, app thật")

if __name__ == "__main__":
    try:
        test_jwt_authentication()
        print("\n" + "="*60)
        print("✅ HOÀN THÀNH TEST JWT")
        print("="*60)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
