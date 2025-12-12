import requests
import json
import base64
import time

BASE_URL = "http://localhost:5000/api"
EMAIL = f"test_image_{int(time.time())}@example.com"
PASSWORD = "password123"

def test_image_upload():
    print("="*60)
    print("TEST IMAGE UPLOAD")
    print("="*60)

    # 1. Register
    print(f"\n[1] Registering user: {EMAIL}")
    reg_resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": EMAIL,
            "password": PASSWORD,
            "full_name": "Test Image User",
            "phone_number": "0123456789"
        }
    )
    if reg_resp.status_code not in [201, 400]: # 400 if exists
        print(f"❌ Register failed: {reg_resp.json()}")
        return

    # 2. Login
    print("\n[2] Logging in...")
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": EMAIL,
            "password": PASSWORD
        }
    )
    
    if login_resp.status_code != 200:
        print(f"❌ Login failed: {login_resp.json()}")
        return
    
    token = login_resp.json()['token']
    print(f"✅ Login successful. Token obtained.")

    # 3. Chat with Image
    print("\n[3] Sending image to chat...")
    # 1x1 Red Pixel
    image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    
    chat_resp = requests.post(
        f"{BASE_URL}/medical-chatbot/chat-secure",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "Hình ảnh này là gì?",
            "image_base64": image_base64
        }
    )
    
    print(f"Status: {chat_resp.status_code}")
    if chat_resp.status_code == 200:
        data = chat_resp.json()
        print(f"✅ PASS: Chat with image successful!")
        print(f"Answer: {data['answer']}")
    else:
        print(f"❌ FAIL: {chat_resp.json()}")

if __name__ == "__main__":
    test_image_upload()
