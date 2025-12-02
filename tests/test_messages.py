import requests
import json

BASE_URL = "http://localhost:5000/api/medical-chatbot"

def test_full_flow():
    """Test đầy đủ: Tạo conversation -> Gửi tin nhắn -> Lấy danh sách tin nhắn"""
    
    print("=" * 60)
    print("BƯỚC 1: Tạo conversation mới")
    print("=" * 60)
    
    # 1. Tạo conversation
    create_response = requests.post(
        f"{BASE_URL}/conversations",
        json={"user_id": 1, "title": "Test Messages"}
    )
    print(f"Status: {create_response.status_code}")
    conv_data = create_response.json()
    print(f"Response: {json.dumps(conv_data, indent=2, ensure_ascii=False)}")
    
    conversation_id = conv_data.get('conversation_id')
    if not conversation_id:
        print("❌ Không tạo được conversation!")
        return
    
    print(f"\n✅ Đã tạo conversation ID: {conversation_id}")
    
    print("\n" + "=" * 60)
    print("BƯỚC 2: Gửi tin nhắn vào conversation")
    print("=" * 60)
    
    # 2. Gửi tin nhắn (sử dụng API chat)
    chat_response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "user_id": 1,
            "conversation_id": conversation_id,
            "question": "Triệu chứng của cảm cúm là gì?"
        }
    )
    print(f"Status: {chat_response.status_code}")
    chat_data = chat_response.json()
    print(f"Question: {chat_data.get('question')}")
    print(f"Answer: {chat_data.get('answer')[:100]}...")  # Chỉ hiện 100 ký tự đầu
    
    print("\n✅ Đã gửi tin nhắn thành công!")
    
    print("\n" + "=" * 60)
    print("BƯỚC 3: Lấy danh sách tin nhắn")
    print("=" * 60)
    
    # 3. Lấy danh sách tin nhắn
    history_response = requests.get(
        f"{BASE_URL}/history/{conversation_id}",
        params={"user_id": 1}
    )
    print(f"Status: {history_response.status_code}")
    history_data = history_response.json()
    
    messages = history_data.get('messages', [])
    print(f"\n📨 Tổng số tin nhắn: {len(messages)}")
    print("\nChi tiết tin nhắn:")
    print("-" * 60)
    
    for i, msg in enumerate(messages, 1):
        sender = "👤 User" if msg['sender'] == 'user' else "🤖 Bot"
        text = msg['message_text']
        # Giới hạn độ dài hiển thị
        display_text = text if len(text) <= 100 else text[:100] + "..."
        print(f"\n{i}. {sender}")
        print(f"   Nội dung: {display_text}")
        print(f"   Thời gian: {msg['sent_at']}")
    
    print("\n" + "=" * 60)
    print("✅ HOÀN THÀNH TEST!")
    print("=" * 60)

if __name__ == "__main__":
    test_full_flow()
