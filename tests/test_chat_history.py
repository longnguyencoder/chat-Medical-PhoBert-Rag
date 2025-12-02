import requests
import json
import time

BASE_URL = "http://localhost:5000/api/medical-chatbot"

def test_chat_history():
    print("🚀 Testing Chat History Feature")
    print("=" * 50)
    
    # 1. Start a new conversation
    print("\n1. Sending first message (New Conversation)...")
    payload = {
        "question": "Triệu chứng của bệnh sốt xuất huyết là gì?",
        "user_id": 123  # Test user ID
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        if response.status_code == 200:
            data = response.json()
            conversation_id = data.get('conversation_id')
            print(f"✅ Success! Conversation ID: {conversation_id}")
            print(f"   Answer: {data.get('answer')[:50]}...")
        else:
            print(f"❌ Failed: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    if not conversation_id:
        print("❌ No conversation ID returned")
        return

    # 2. Continue conversation
    print("\n2. Sending second message (Continue Conversation)...")
    payload = {
        "question": "Cách phòng ngừa bệnh này?",
        "user_id": 123,
        "conversation_id": conversation_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Conversation ID: {data.get('conversation_id')}")
            print(f"   Answer: {data.get('answer')[:50]}...")
        else:
            print(f"❌ Failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # 3. Get History
    print(f"\n3. Retrieving History for Conversation {conversation_id}...")
    try:
        response = requests.get(f"{BASE_URL}/history/{conversation_id}")
        if response.status_code == 200:
            history = response.json()
            messages = history.get('messages', [])
            print(f"✅ Success! Found {len(messages)} messages")
            
            for msg in messages:
                sender = msg.get('sender')
                text = msg.get('message_text')[:30]
                print(f"   - [{sender}]: {text}...")
                
            if len(messages) >= 4: # 2 user questions + 2 bot answers
                print("\n🎉 Chat History Verification PASSED!")
            else:
                print("\n⚠️ Warning: Expected at least 4 messages")
        else:
            print(f"❌ Failed to get history: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Wait for server to be ready (if running locally)
    # In this environment, we assume server is running or we need to start it
    test_chat_history()
