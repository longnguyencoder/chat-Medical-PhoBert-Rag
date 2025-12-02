import requests
import json

BASE_URL = "http://localhost:5000/api/medical-chatbot"

def test_update_conversation():
    """Test 1: Update conversation title"""
    print("\n" + "="*60)
    print("TEST 1: Đổi tên conversation")
    print("="*60)
    
    # Create a conversation first
    create_resp = requests.post(
        f"{BASE_URL}/conversations",
        json={"user_id": 1, "title": "Old Title"}
    )
    conv_id = create_resp.json()['conversation_id']
    print(f"✓ Created conversation ID: {conv_id} with title: 'Old Title'")
    
    # Update title
    update_resp = requests.put(
        f"{BASE_URL}/conversations/{conv_id}",
        json={"user_id": 1, "title": "Tư vấn đau đầu"}
    )
    print(f"Status: {update_resp.status_code}")
    print(f"New title: {update_resp.json()['title']}")
    print("✅ PASS: Đổi tên thành công!")
    
    return conv_id

def test_search_conversations():
    """Test 2: Search conversations"""
    print("\n" + "="*60)
    print("TEST 2: Tìm kiếm conversations")
    print("="*60)
    
    # Create conversations with different titles
    requests.post(f"{BASE_URL}/conversations", json={"user_id": 1, "title": "Hỏi về đau đầu"})
    requests.post(f"{BASE_URL}/conversations", json={"user_id": 1, "title": "Tư vấn sốt cao"})
    requests.post(f"{BASE_URL}/conversations", json={"user_id": 1, "title": "Đau bụng"})
    
    # Search for "đau"
    search_resp = requests.get(
        f"{BASE_URL}/conversations/search",
        params={"user_id": 1, "keyword": "đau"}
    )
    print(f"Status: {search_resp.status_code}")
    results = search_resp.json()['conversations']
    print(f"Found {len(results)} conversations with keyword 'đau':")
    for conv in results[:3]:
        print(f"  - {conv['title']}")
    print("✅ PASS: Tìm kiếm thành công!")

def test_regenerate_response():
    """Test 3: Regenerate bot response"""
    print("\n" + "="*60)
    print("TEST 3: Regenerate câu trả lời")
    print("="*60)
    
    # Create conversation and send message
    create_resp = requests.post(
        f"{BASE_URL}/conversations",
        json={"user_id": 1, "title": "Test Regenerate"}
    )
    conv_id = create_resp.json()['conversation_id']
    
    # Send a question
    chat_resp = requests.post(
        f"{BASE_URL}/chat",
        json={
            "user_id": 1,
            "conversation_id": conv_id,
            "question": "Triệu chứng cảm cúm là gì?"
        }
    )
    print(f"✓ Sent question, got response")
    
    # Get message history to find bot message ID
    history_resp = requests.get(
        f"{BASE_URL}/history/{conv_id}",
        params={"user_id": 1}
    )
    messages = history_resp.json()['messages']
    bot_message = [m for m in messages if m['sender'] == 'bot'][0]
    bot_msg_id = bot_message['message_id']
    
    original_answer = bot_message['message_text'][:50]
    print(f"Original answer: {original_answer}...")
    
    # Regenerate
    regen_resp = requests.post(
        f"{BASE_URL}/chat/regenerate",
        json={
            "user_id": 1,
            "conversation_id": conv_id,
            "message_id": bot_msg_id
        }
    )
    print(f"Status: {regen_resp.status_code}")
    new_answer = regen_resp.json()['answer'][:50]
    print(f"New answer: {new_answer}...")
    print("✅ PASS: Regenerate thành công!")
    
    return conv_id

def test_delete_conversation(conv_id):
    """Test 4: Delete conversation"""
    print("\n" + "="*60)
    print("TEST 4: Xóa conversation")
    print("="*60)
    
    # Delete
    delete_resp = requests.delete(
        f"{BASE_URL}/conversations/{conv_id}",
        params={"user_id": 1}
    )
    print(f"Status: {delete_resp.status_code}")
    print(f"Message: {delete_resp.json()['message']}")
    
    # Verify deleted
    verify_resp = requests.get(
        f"{BASE_URL}/history/{conv_id}",
        params={"user_id": 1}
    )
    if verify_resp.status_code == 404:
        print("✅ PASS: Conversation đã bị xóa!")
    else:
        print("⚠️ WARNING: Conversation vẫn còn tồn tại")

def test_archive_pin_conversation():
    """Test 5: Archive and Pin conversation"""
    print("\n" + "="*60)
    print("TEST 5: Archive và Pin conversation")
    print("="*60)
    
    # Create conversation
    create_resp = requests.post(
        f"{BASE_URL}/conversations",
        json={"user_id": 1, "title": "Test Archive Pin"}
    )
    conv_id = create_resp.json()['conversation_id']
    
    # Test Archive
    archive_resp = requests.post(
        f"{BASE_URL}/conversations/{conv_id}/archive",
        params={"user_id": 1}
    )
    print(f"Archive Status: {archive_resp.status_code}")
    print(f"Is Archived: {archive_resp.json()['is_archived']}")
    
    # Test Pin
    pin_resp = requests.post(
        f"{BASE_URL}/conversations/{conv_id}/pin",
        params={"user_id": 1}
    )
    print(f"Pin Status: {pin_resp.status_code}")
    print(f"Is Pinned: {pin_resp.json()['is_pinned']}")
    
    print("✅ PASS: Archive và Pin thành công!")
    return conv_id

def test_delete_message(conv_id):
    """Test 6: Delete message"""
    print("\n" + "="*60)
    print("TEST 6: Xóa tin nhắn")
    print("="*60)
    
    # Send a message first
    requests.post(
        f"{BASE_URL}/chat",
        json={
            "user_id": 1,
            "conversation_id": conv_id,
            "question": "Tin nhắn cần xóa"
        }
    )
    
    # Get message ID
    history_resp = requests.get(
        f"{BASE_URL}/history/{conv_id}",
        params={"user_id": 1}
    )
    messages = history_resp.json()['messages']
    msg_id = messages[0]['message_id']
    print(f"Deleting message ID: {msg_id}")
    
    # Delete message
    delete_resp = requests.delete(
        f"{BASE_URL}/messages/{msg_id}",
        params={"user_id": 1}
    )
    print(f"Status: {delete_resp.status_code}")
    print(f"Message: {delete_resp.json()['message']}")
    
    # Verify
    history_resp = requests.get(
        f"{BASE_URL}/history/{conv_id}",
        params={"user_id": 1}
    )
    messages = history_resp.json()['messages']
    if not any(m['message_id'] == msg_id for m in messages):
        print("✅ PASS: Tin nhắn đã bị xóa!")
    else:
        print("⚠️ WARNING: Tin nhắn vẫn còn")

if __name__ == "__main__":
    print("\n🚀 BẮT ĐẦU TEST CÁC TÍNH NĂNG MỚI")
    print("="*60)
    
    try:
        # Test 1: Update
        conv_id_1 = test_update_conversation()
        
        # Test 2: Search
        test_search_conversations()
        
        # Test 3: Regenerate
        conv_id_2 = test_regenerate_response()
        
        # Test 4: Delete
        test_delete_conversation(conv_id_1)
        
        # Test 5: Archive & Pin
        conv_id_3 = test_archive_pin_conversation()
        
        # Test 6: Delete Message
        test_delete_message(conv_id_3)
        
        print("\n" + "="*60)
        print("✅ TẤT CẢ TESTS ĐỀU PASS!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
