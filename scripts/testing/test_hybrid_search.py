"""
Test script to compare Hybrid Search vs Vector-only Search

This script demonstrates the improvements from hybrid search by testing
with various medical queries.
"""

import requests
import json
from typing import Dict, Any

# API endpoint
BASE_URL = "http://127.0.0.1:5000"
CHAT_ENDPOINT = f"{BASE_URL}/api/medical-chatbot/chat"

def test_query(question: str, conversation_id: int = None) -> Dict[str, Any]:
    """
    Send a query to the medical chatbot API
    
    Args:
        question: Medical question to ask
        conversation_id: Optional conversation ID
        
    Returns:
        API response with answer and metadata
    """
    payload = {
        "message": question,
        "conversation_id": conversation_id
    }
    
    try:
        response = requests.post(CHAT_ENDPOINT, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return None

def print_result(question: str, result: Dict[str, Any]):
    """Pretty print the test result"""
    print("\n" + "="*80)
    print(f"📝 Câu hỏi: {question}")
    print("="*80)
    
    if not result:
        print("❌ Không nhận được kết quả")
        return
    
    # Print search metadata
    print(f"\n🔍 Phương pháp tìm kiếm: {result.get('search_method', 'N/A')}")
    print(f"   - Query Expansion: {'✅' if result.get('query_expansion_used') else '❌'}")
    print(f"   - Hybrid Search: {'✅' if result.get('hybrid_search_used') else '❌'}")
    print(f"   - Reranking: {'✅' if result.get('reranking_used') else '❌'}")
    print(f"   - Tổng kết quả: {result.get('total_found', 0)}")
    print(f"   - Độ tin cậy: {result.get('confidence', 'N/A')}")
    
    # Print answer
    print(f"\n💬 Câu trả lời:")
    print(result.get('answer', 'Không có câu trả lời'))
    
    # Print sources
    sources = result.get('sources', [])
    if sources:
        print(f"\n📚 Nguồn tham khảo ({len(sources)} nguồn):")
        for i, source in enumerate(sources[:3], 1):
            metadata = source.get('metadata', {})
            score_breakdown = source.get('score_breakdown', {})
            
            print(f"\n   [{i}] {metadata.get('disease_name', 'N/A')}")
            
            # Show hybrid scores if available
            if 'bm25' in score_breakdown and 'vector' in score_breakdown:
                print(f"       • BM25 Score: {score_breakdown['bm25']:.3f}")
                print(f"       • Vector Score: {score_breakdown['vector']:.3f}")
                print(f"       • Hybrid Score: {score_breakdown['hybrid']:.3f}")
            else:
                print(f"       • Relevance Score: {source.get('relevance_score', 0):.3f}")
            
            if source.get('final_score'):
                print(f"       • Final Score (after reranking): {source['final_score']:.3f}")

def main():
    """Run test cases"""
    print("\n" + "🧪 TESTING HYBRID SEARCH (BM25 + Vector)".center(80, "="))
    
    # Test cases designed to show hybrid search benefits
    test_cases = [
        # Test 1: Exact medical term (BM25 should help)
        "Paracetamol liều lượng cho trẻ em bao nhiêu?",
        
        # Test 2: Disease name (keyword matching important)
        "Triệu chứng của sốt xuất huyết là gì?",
        
        # Test 3: Symptom-based query (semantic search important)
        "Tôi bị sốt cao và đau đầu, có thể bị bệnh gì?",
        
        # Test 4: Treatment query (hybrid should work well)
        "Cách điều trị viêm họng tại nhà?",
        
        # Test 5: Prevention query
        "Làm thế nào để phòng ngừa cảm cúm?",
    ]
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n\n{'TEST CASE ' + str(i):.^80}")
        result = test_query(question)
        print_result(question, result)
        
        # Small delay between requests
        import time
        time.sleep(1)
    
    print("\n\n" + "="*80)
    print("✅ Testing completed!".center(80))
    print("="*80)
    
    print("\n📊 Để xem chi tiết hơn, truy cập Swagger UI:")
    print(f"   {BASE_URL}/api/docs")
    print("\n💡 Lưu ý:")
    print("   - BM25 Score cao = Khớp từ khóa tốt")
    print("   - Vector Score cao = Khớp ngữ nghĩa tốt")
    print("   - Hybrid Score = 0.3 × BM25 + 0.7 × Vector")
    print("   - Final Score = Sau khi reranking với Cross-Encoder")

if __name__ == "__main__":
    main()
