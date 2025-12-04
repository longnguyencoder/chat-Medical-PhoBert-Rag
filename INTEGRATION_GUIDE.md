# Hướng dẫn tích hợp Next-Question Suggestions
## Integration Guide

### Bước 1: Thêm import vào đầu file medical_chatbot_controller.py

Mở file `src/controllers/medical_chatbot_controller.py`

Tìm phần import ở đầu file (khoảng dòng 1-20) và thêm dòng này:

```python
from src.services.suggestion_agent_service import generate_next_questions
```

**Ví dụ:**
```python
from flask import request
from flask_restx import Namespace, Resource, fields
import logging
from datetime import datetime
from src.services.medical_chatbot_service import (
    extract_user_intent_and_features,
    combined_search_with_filters,
    # ... các imports khác
)
from src.services.suggestion_agent_service import generate_next_questions  # ← THÊM DÒNG NÀY
```

---

### Bước 2: Cập nhật response model

Tìm `chat_response` model (khoảng dòng 29-54) và thêm field `suggestions`:

**Trước:**
```python
chat_response = medical_chatbot_ns.model('MedicalChatResponse', {
    'question': fields.String(description='Original question'),
    'answer': fields.String(description='Generated answer'),
    'conversation_id': fields.Integer(description='Conversation ID'),
    'user_info': fields.Raw(description='User information'),
    'cache_info': fields.Raw(description='Cache information')
})
```

**Sau:**
```python
chat_response = medical_chatbot_ns.model('MedicalChatResponse', {
    'question': fields.String(description='Original question'),
    'answer': fields.String(description='Generated answer'),
    'suggestions': fields.List(fields.String, description='Next question suggestions'),  # ← THÊM DÒNG NÀY
    'conversation_id': fields.Integer(description='Conversation ID'),
    'user_info': fields.Raw(description='User information'),
    'cache_info': fields.Raw(description='Cache information')
})
```

---

### Bước 3: Cập nhật SecureMedicalChat.post method

Tìm class `SecureMedicalChat` và method `post` (khoảng dòng 56-162)

Tìm phần lưu bot message và return response (khoảng dòng 145-162):

**Trước:**
```python
        # Lưu câu trả lời bot
        bot_msg = Message(
            conversation_id=conversation.conversation_id,
            sender='bot',
            message_text=answer,
            message_type='text',
            sent_at=datetime.utcnow()
        )
        db.session.add(bot_msg)
        db.session.commit()
        
        return {
            'question': question,
            'answer': answer,
            'conversation_id': conversation.conversation_id,
            'user_info': {'user_id': user_id, 'name': user_name},
            'cache_info': {
                'search_cached': search_from_cache,
                'response_cached': response_from_cache
            }
        }, 200
```

**Sau:**
```python
        # Lưu câu trả lời bot
        bot_msg = Message(
            conversation_id=conversation.conversation_id,
            sender='bot',
            message_text=answer,
            message_type='text',
            sent_at=datetime.utcnow()
        )
        db.session.add(bot_msg)
        db.session.commit()
        
        # ========== THÊM PHẦN NÀY ==========
        # Generate next-question suggestions
        suggestions = []
        try:
            suggestions = generate_next_questions(
                user_question=question,
                bot_answer=answer
            )
        except Exception as e:
            logger.warning(f"Failed to generate suggestions: {e}")
            # Không block response nếu suggestion fail
        # ===================================
        
        return {
            'question': question,
            'answer': answer,
            'suggestions': suggestions,  # ← THÊM DÒNG NÀY
            'conversation_id': conversation.conversation_id,
            'user_info': {'user_id': user_id, 'name': user_name},
            'cache_info': {
                'search_cached': search_from_cache,
                'response_cached': response_from_cache
            }
        }, 200
```

---

### Bước 4: Test

1. **Restart server:**
   ```bash
   python main.py
   ```

2. **Test API:**
   ```bash
   POST /api/medical-chatbot/chat
   Authorization: Bearer <your_token>
   
   {
     "question": "Triệu chứng tiểu đường là gì?"
   }
   ```

3. **Kiểm tra response có suggestions:**
   ```json
   {
     "answer": "...",
     "suggestions": [
       "Làm thế nào để phòng ngừa tiểu đường?",
       "Chế độ ăn cho người tiểu đường?",
       "Biến chứng của tiểu đường là gì?"
     ]
   }
   ```

---

## Troubleshooting

### Lỗi: "OPENAI_API_KEY not configured"

**Giải pháp:** Thêm API key vào `.env`:
```env
OPENAI_API_KEY=sk-your-key-here
```

### Suggestions trống []

**Nguyên nhân:**
- API key không hợp lệ
- `ENABLE_SUGGESTIONS=False` trong .env
- OpenAI API lỗi

**Giải pháp:**
- Check logs để xem error
- Verify API key
- Set `ENABLE_SUGGESTIONS=True`

### Response chậm

**Giải pháp:**
- Dùng `gpt-4o-mini` thay vì `gpt-4`
- Suggestions được generate sau khi lưu message, không block response chính

---

## Summary

**3 thay đổi chính:**
1. ✅ Import `generate_next_questions`
2. ✅ Thêm field `suggestions` vào response model
3. ✅ Gọi `generate_next_questions()` và thêm vào response

**Thời gian:** ~5-10 phút để tích hợp
