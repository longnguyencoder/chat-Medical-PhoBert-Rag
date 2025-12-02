import requests
import json
import sys

BASE_URL = "http://localhost:5000/api/medical-chatbot"

def test_create_conversation():
    print("\n--- Testing Create Conversation ---")
    url = f"{BASE_URL}/conversations"
    payload = {
        "user_id": 1,
        "title": "Test Conversation"
    }
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 201:
            return response.json()['conversation_id']
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_list_conversations():
    print("\n--- Testing List Conversations ---")
    url = f"{BASE_URL}/conversations?user_id=1"
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Conversations found: {len(data.get('conversations', []))}")
        # print(f"Response: {data}")
    except Exception as e:
        print(f"Error: {e}")

def test_get_history(conversation_id):
    print(f"\n--- Testing Get History for ID {conversation_id} ---")
    url = f"{BASE_URL}/history/{conversation_id}?user_id=1"
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # 1. Create
    conv_id = test_create_conversation()
    
    if conv_id:
        # 2. List
        test_list_conversations()
        
        # 3. Get History (should be empty initially)
        test_get_history(conv_id)
    else:
        print("Failed to create conversation, skipping other tests.")
