import requests
import json
import base64
import time
import os

BASE_URL = "http://localhost:5000/api"
EMAIL = f"test_image_{int(time.time())}@example.com"
PASSWORD = "password123"
IMAGE_PATH = r"C:/Users/PC/.gemini/antigravity/brain/93e53696-1ca1-49d3-90c6-1df063bef3ff/uploaded_media_1769566255222.png"

def test_real_image_analysis():
    print("="*60)
    print("TEST REAL MEDICAL IMAGE ANALYSIS")
    print("="*60)

    # 1. Read Image
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Image not found at: {IMAGE_PATH}")
        return

    print(f"\n[1] Reading image from: {IMAGE_PATH}")
    with open(IMAGE_PATH, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    print("✅ Image encoded successfully")

    # 2. Register/Login
    print(f"\n[2] Authenticating...")
    # Register (ignore error if exists)
    requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": EMAIL,
            "password": PASSWORD,
            "full_name": "Test Real Image User",
            "phone_number": "0123456789"
        }
    )
    
    # Login
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
    print(f"✅ Login successful")

    # 3. Chat with Image
    print("\n[3] Sending medical image to chat...")
    question = "Bạn xem thử chỉ số này có ảnh hưởng gì không?"
    print(f"Question: {question}")
    
    chat_resp = requests.post(
        f"{BASE_URL}/medical-chatbot/chat-secure",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": question,
            "image_base64": encoded_string
        }
    )
    
    print(f"\nStatus: {chat_resp.status_code}")
    if chat_resp.status_code == 200:
        data = chat_resp.json()
        print("✅ PASS: API returned success")
        print("-" * 60)
        print("ANSWER FROM AI:")
        print(data['answer'])
        print("-" * 60)
        
        # Check for refusal keywords
        refusal_keywords = ["i'm sorry", "i can't assist", "không thể hỗ trợ", "xin lỗi"]
        answer_lower = data['answer'].lower()
        if any(k in answer_lower for k in refusal_keywords) and "để giúp bạn hiểu" not in answer_lower:
             print("⚠️ WARNING: It seems GPT still refused or gave a generic refusal.")
        else:
             print("🎉 SUCCESS: AI analyzed the image!")
             
    else:
        print(f"❌ FAIL: {chat_resp.json()}")

if __name__ == "__main__":
    test_real_image_analysis()
