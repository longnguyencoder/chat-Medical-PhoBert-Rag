# Hướng dẫn tích hợp Next-Question Suggestions
# ============================================

# Bước 1: Thêm import vào đầu file medical_chatbot_controller.py
# Tìm dòng import và thêm:

from src.services.suggestion_agent_service import generate_next_questions

# Bước 2: Cập nhật response model
# Tìm chat_response model (khoảng dòng 29-54) và thêm field suggestions:

chat_response = medical_chatbot_ns.model('MedicalChatResponse', {
    'question': fields.String(description='Original question'),
    'answer': fields.String(description='Generated answer'),
    'suggestions': fields.List(fields.String, description='Next question suggestions'),  # ← THÊM DÒNG NÀY
    'conversation_id': fields.Integer(description='Conversation ID'),
    # ... các fields khác giữ nguyên
})

# Bước 3: Cập nhật SecureMedicalChat.post method
# Tìm phần return (khoảng dòng 153-162) và sửa thành:

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
