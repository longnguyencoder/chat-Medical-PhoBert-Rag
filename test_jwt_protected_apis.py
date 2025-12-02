"""
Test JWT Protected APIs
========================
Test all 6 critical APIs that now require JWT token.
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"

def get_token():
    """Login and get JWT token"""
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "test_user_9348@example.com",
            "password": "password123"
        }
    )
    if resp.status_code == 200:
        return resp.json()['token']
    else:
        print(f"❌ Login failed: {resp.json()}")
        return None

def test_protected_apis():
    print("\n" + "="*60)
    print("TEST JWT PROTECTED APIs")
    print("="*60)
    
    # Get token
    print("\n[1] Getting JWT token...")
    token = get_token()
    if not token:
        return
    
    print(f"✅ Token: {token[:30]}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a test conversation first
    print("\n[2] Creating test conversation...")
    conv_resp = requests.post(
        f"{BASE_URL}/medical-chatbot/conversations",
        json={"user_id": 1, "title": "Test Conversation"}
    )
    conv_id = conv_resp.json().get('conversation_id')
    print(f"✅ Created conversation ID: {conv_id}")
    
    # Test 1: Update conversation (JWT Required)
    print("\n[3] Testing PUT /conversations/{id} (JWT Required)...")
    resp = requests.put(
        f"{BASE_URL}/medical-chatbot/conversations/{conv_id}",
        headers=headers,
        json={"title": "Updated Title"}
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("✅ PASS: Update conversation with JWT")
    else:
        print(f"❌ FAIL: {resp.json()}")
    
    # Test 2: Archive conversation (JWT Required)
    print("\n[4] Testing POST /conversations/{id}/archive (JWT Required)...")
    resp = requests.post(
        f"{BASE_URL}/medical-chatbot/conversations/{conv_id}/archive",
        headers=headers
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("✅ PASS: Archive conversation with JWT")
    else:
        print(f"❌ FAIL: {resp.json()}")
    
    # Test 3: Pin conversation (JWT Required)
    print("\n[5] Testing POST /conversations/{id}/pin (JWT Required)...")
    resp = requests.post(
        f"{BASE_URL}/medical-chatbot/conversations/{conv_id}/pin",
        headers=headers
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("✅ PASS: Pin conversation with JWT")
    else:
        print(f"❌ FAIL: {resp.json()}")
    
    # Test 4: Delete conversation (JWT Required)
    print("\n[6] Testing DELETE /conversations/{id} (JWT Required)...")
    resp = requests.delete(
        f"{BASE_URL}/medical-chatbot/conversations/{conv_id}",
        headers=headers
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("✅ PASS: Delete conversation with JWT")
    else:
        print(f"❌ FAIL: {resp.json()}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED")
    print("="*60)

if __name__ == "__main__":
    try:
        test_protected_apis()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
