"""
Next-Question Suggestion Agent Service
========================================

Sử dụng GPT-4 để tạo câu hỏi gợi ý tiếp theo cho người dùng.

Tính năng:
- Tự động tạo 3 câu hỏi liên quan
- Dựa trên context của cuộc hội thoại
- Tối ưu chi phí với gpt-4o-mini
- Xử lý lỗi gracefully
"""

import json
import os
from openai import OpenAI
from src.config.config import Config

# Initialize OpenAI client
client = OpenAI(api_key=Config.OPENAI_API_KEY)

SUGGESTION_PROMPT_TEMPLATE = """
Bạn là trợ lý y tế chuyên nghiệp tại Việt Nam. Dựa trên cuộc hội thoại sau, 
hãy tạo 3 câu hỏi tiếp theo mà người dùng có thể quan tâm.

Câu hỏi của người dùng: {user_question}
Câu trả lời của chatbot: {bot_answer}

Yêu cầu:
1. 3 câu hỏi phải liên quan trực tiếp đến chủ đề y tế đang thảo luận
2. Sắp xếp từ cơ bản đến nâng cao (hoặc từ phòng ngừa → điều trị → biến chứng)
3. Ngắn gọn, dễ hiểu (tối đa 15 từ mỗi câu)
4. Phù hợp với ngữ cảnh y tế Việt Nam
5. Dùng tiếng Việt tự nhiên, thân thiện

Ví dụ tốt:
- "Làm thế nào để phòng ngừa bệnh tiểu đường?"
- "Chế độ ăn uống cho người bị cao huyết áp như thế nào?"
- "Triệu chứng nào cần đi khám ngay?"

Trả lời CHÍNH XÁC theo format JSON sau (không thêm text nào khác):
{{
  "suggestions": [
    "Câu hỏi 1",
    "Câu hỏi 2",
    "Câu hỏi 3"
  ]
}}
"""


def generate_next_questions(user_question: str, bot_answer: str, topic: str = None) -> list:
    """
    Tạo 3 câu hỏi gợi ý tiếp theo sử dụng GPT-4
    
    Args:
        user_question (str): Câu hỏi của người dùng
        bot_answer (str): Câu trả lời của chatbot
        topic (str, optional): Chủ đề y tế (nếu có)
    
    Returns:
        list: Danh sách 3 câu hỏi gợi ý, hoặc [] nếu có lỗi
    
    Example:
        >>> generate_next_questions(
        ...     "Triệu chứng tiểu đường là gì?",
        ...     "Triệu chứng tiểu đường gồm: khát nước nhiều, tiểu nhiều..."
        ... )
        [
            "Làm thế nào để phòng ngừa tiểu đường?",
            "Chế độ ăn cho người tiểu đường?",
            "Biến chứng của tiểu đường là gì?"
        ]
    """
    
    # Kiểm tra config
    if not Config.ENABLE_SUGGESTIONS:
        return []
    
    if not Config.OPENAI_API_KEY:
        print("⚠️  Warning: OPENAI_API_KEY not configured. Suggestions disabled.")
        return []
    
    try:
        # Tạo prompt
        prompt = SUGGESTION_PROMPT_TEMPLATE.format(
            user_question=user_question,
            bot_answer=bot_answer[:500]  # Giới hạn độ dài để tiết kiệm token
        )
        
        # Gọi OpenAI API
        response = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là trợ lý y tế chuyên nghiệp. Luôn trả lời bằng JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,  # Tăng creativity một chút
            max_tokens=200,   # Đủ cho 3 câu hỏi
            response_format={"type": "json_object"}  # Force JSON response
        )
        
        # Parse response
        content = response.choices[0].message.content
        suggestions_data = json.loads(content)
        suggestions = suggestions_data.get('suggestions', [])
        
        # Validate
        if not isinstance(suggestions, list) or len(suggestions) != 3:
            print(f"⚠️  Invalid suggestions format: {suggestions}")
            return []
        
        print(f"✅ Generated {len(suggestions)} suggestions")
        return suggestions
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return []
    
    except Exception as e:
        print(f"❌ Error generating suggestions: {e}")
        return []


def generate_next_questions_async(user_question: str, bot_answer: str, topic: str = None):
    """
    Async version - để tránh block main response
    Có thể implement sau nếu cần
    """
    # TODO: Implement async version with asyncio
    pass


# Fallback suggestions khi API fail
FALLBACK_SUGGESTIONS = {
    "default": [
        "Làm thế nào để phòng ngừa bệnh này?",
        "Cần lưu ý gì trong chế độ ăn uống?",
        "Khi nào cần đi khám bác sĩ?"
    ],
    "diabetes": [
        "Làm thế nào để phòng ngừa tiểu đường?",
        "Chế độ ăn cho người tiểu đường như thế nào?",
        "Biến chứng của tiểu đường là gì?"
    ],
    "hypertension": [
        "Cách hạ huyết áp tự nhiên?",
        "Thực phẩm nên tránh khi bị cao huyết áp?",
        "Thuốc điều trị cao huyết áp nào tốt?"
    ]
}


def get_fallback_suggestions(topic: str = None) -> list:
    """
    Trả về câu hỏi gợi ý mặc định khi API fail
    
    Args:
        topic (str): Chủ đề y tế
    
    Returns:
        list: 3 câu hỏi gợi ý mặc định
    """
    if topic and topic.lower() in FALLBACK_SUGGESTIONS:
        return FALLBACK_SUGGESTIONS[topic.lower()]
    return FALLBACK_SUGGESTIONS["default"]
