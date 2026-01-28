
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_mock_vision_analysis():
    print("="*60)
    print("VERIFYING IMAGE ANALYSIS FLOW (MOCKED)")
    print("="*60)

    # Mock OpenAI client
    with patch('src.services.medical_chatbot_service.client') as mock_client:
        # 1. Mock keywords extraction (GPT-4o)
        mock_keywords_response = MagicMock()
        mock_keywords_response.choices[0].message.content = "Glucose 10.5, HbA1c 8.2, tiểu đường type 2"
        
        # 2. Mock natural response generation (GPT-4o with image)
        mock_natural_response = MagicMock()
        mock_natural_response.choices[0].message.content = """
📋 **Thông tin chung**: Kết quả xét nghiệm máu ngày 26/01/2026.
🔍 **Các chỉ số chính**:
- Glucose: 10.5 mmol/L (Cao)
- HbA1c: 8.2% (Cao)
💡 **Giải thích sơ bộ**: Các chỉ số này cho thấy tình trạng đường huyết đang kiểm soát chưa tốt.
🛠️ **Khuyến nghị**: Bạn cần trao đổi với bác sĩ về việc điều chỉnh liều thuốc tiểu đường.
"""
        mock_natural_response.choices[0].message.tool_calls = None

        # Setup side effects
        mock_client.chat.completions.create.side_effects = [
            mock_keywords_response,
            mock_natural_response
        ]
        
        from src.services.medical_chatbot_service import generate_search_query_from_image, generate_natural_response
        
        # Test keyword extraction
        print("\n[Step 1] Testing keyword extraction...")
        keywords = generate_search_query_from_image("mock_base64")
        print(f"Extracted: {keywords}")
        assert "Glucose" in keywords
        
        # Test natural response
        print("\n[Step 2] Testing natural response generation...")
        response = generate_natural_response(
            question="Phân tích ảnh này cho tôi",
            search_results=[],
            extracted_features={"intent": "medical_report"},
            image_base64="mock_base64"
        )
        
        print("\nFinal Answer:")
        print(response['answer'])
        assert "Glucose" in response['answer']
        assert "📋 **Thông tin chung**" in response['answer']

    print("\n" + "="*60)
    print("✓ MOCK VISION TEST COMPLETED")
    print("="*60)

if __name__ == "__main__":
    try:
        test_mock_vision_analysis()
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
