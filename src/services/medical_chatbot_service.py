import os
import json
from openai import OpenAI
from typing import Dict, List, Optional, Any, Tuple
import chromadb
import numpy as np
import sys
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path to import phobert_embedding
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(src_dir)

from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize ChromaDB client
workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
chroma_client = chromadb.PersistentClient(path=os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'chroma_db'))

# Initialize PhoBERT embedding function
phobert_ef = PhoBERTEmbeddingFunction()

# Medical keywords for enhanced relevance scoring
MEDICAL_KEYWORDS = {
    'symptoms': ['triệu chứng', 'dấu hiệu', 'biểu hiện', 'sốt', 'ho', 'đau', 'ngứa', 'mệt', 'buồn nôn'],
    'treatment': ['điều trị', 'chữa', 'thuốc', 'uống', 'dùng', 'khám', 'bác sĩ'],
    'prevention': ['phòng ngừa', 'tránh', 'vệ sinh', 'vắc-xin', 'tiêm chủng'],
    'diagnosis': ['chẩn đoán', 'xét nghiệm', 'kiểm tra', 'khám']
}

# Confidence threshold for search results
# Lowered to 0.15 to allow more results (was 0.3)
CONFIDENCE_THRESHOLD = 0.15

def get_or_create_collection():
    """Get existing collection or create new one if not exists"""
    try:
        collection = chroma_client.get_collection(
            name="medical_collection",
            embedding_function=phobert_ef
        )
        return collection
    except Exception as e:
        print(f"Collection not found, creating new one: {str(e)}")
        collection = chroma_client.create_collection(
            name="medical_collection",
            embedding_function=phobert_ef
        )
        return collection

def normalize_similarity(distance: float) -> float:
    """
    Convert L2 distance to a normalized similarity score.
    PhoBERT embeddings have large vector norms, so L2 distance is large.
    Scale distance to get a meaningful similarity score.
    """
    if distance <= 0:
        return 1.0
    sim = 1 / (1 + (distance / 10))  # scale factor 10 tuned for PhoBERT
    return float(sim)


def extract_keywords(text: str) -> List[str]:
    """
    Extract important keywords from text.
    """
    # Remove punctuation and convert to lowercase
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()
    
    # Filter out common stop words (basic Vietnamese stop words)
    stop_words = {'là', 'của', 'và', 'có', 'được', 'này', 'đó', 'các', 'cho', 'từ', 'với', 'một', 'những'}
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords

def calculate_keyword_match_score(question: str, document: str, metadata: Dict) -> float:
    """
    Calculate keyword matching score between question and document.
    """
    question_keywords = set(extract_keywords(question))
    
    # Combine all searchable fields
    searchable_text = ' '.join([
        str(metadata.get('disease_name', '')),
        str(metadata.get('symptoms', '')),
        str(metadata.get('treatment', '')),
        str(metadata.get('prevention', '')),
        str(metadata.get('description', ''))
    ]).lower()
    
    doc_keywords = set(extract_keywords(searchable_text))
    
    if not question_keywords or not doc_keywords:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(question_keywords & doc_keywords)
    union = len(question_keywords | doc_keywords)
    
    return intersection / union if union > 0 else 0.0

def calculate_medical_relevance_score(question: str, metadata: Dict) -> float:
    """
    Calculate relevance score based on medical domain knowledge.
    Boosts score if medical keywords match.
    """
    question_lower = question.lower()
    score = 0.0
    
    # Check for medical keyword categories
    for category, keywords in MEDICAL_KEYWORDS.items():
        if any(kw in question_lower for kw in keywords):
            # Check if the metadata has relevant information for this category
            field_value = str(metadata.get(category, '')).lower()
            if field_value and len(field_value) > 5:
                score += 0.15
    
    return min(score, 0.6)  # Cap at 0.6

def calculate_combined_score(
    distance: float,
    question: str,
    document: str,
    metadata: Dict
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate combined relevance score using multiple signals.
    
    Returns:
        Tuple of (final_score, score_breakdown)
    """
    # Semantic similarity from PhoBERT embeddings
    semantic_score = normalize_similarity(distance)
    
    # Keyword matching score
    keyword_score = calculate_keyword_match_score(question, document, metadata)
    
    # Medical domain relevance
    medical_score = calculate_medical_relevance_score(question, metadata)
    
    # Weighted combination
    final_score = (
        0.5 * semantic_score +      # PhoBERT semantic similarity (most important)
        0.3 * keyword_score +        # Keyword matching
        0.2 * medical_score          # Medical domain relevance
    )
    
    score_breakdown = {
        'semantic': round(semantic_score, 3),
        'keyword': round(keyword_score, 3),
        'medical': round(medical_score, 3),
        'final': round(final_score, 3)
    }
    
    return final_score, score_breakdown

def extract_user_intent_and_features(question: str) -> Dict[str, Any]:
    """
    Extract user intent and medical features using OpenAI
    """
    
    tools_schema = [
        {
            "type": "function",
            "function": {
                "name": "tim_kiem_thong_tin_y_te",
                "description": "Trích xuất thông tin y tế từ câu hỏi người dùng (triệu chứng, tên bệnh, thuốc, v.v.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "trieu_chung": {
                            "type": "string",
                            "description": "Các triệu chứng bệnh (sốt, ho, đau đầu, v.v.)"
                        },
                        "ten_benh": {
                            "type": "string", 
                            "description": "Tên bệnh nghi ngờ hoặc được nhắc đến"
                        },
                        "thuoc": {
                            "type": "string",
                            "description": "Tên thuốc hoặc loại thuốc"
                        },
                        "muc_dich": {
                            "type": "string",
                            "description": "Mục đích hỏi (tìm cách chữa, phòng ngừa, hỏi triệu chứng)"
                        }
                    },
                    "required": []
                }
            }
        }
    ]
    
    system_prompt = """Bạn là trợ lý y tế AI. Hãy phân tích câu hỏi của người dùng và trích xuất thông tin y tế quan trọng.
    Hãy trích xuất chính xác các thông tin từ câu hỏi và trả về dưới dạng JSON."""

    try:
        response = client.chat.completions.create(
    model="gpt-4o-mini",   # Có thể đổi gpt-3.5 nếu muốn, nhưng 4o-mini mạnh hơn
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ],
    tools=tools_schema,
    tool_choice={"type": "function", "function": {"name": "tim_kiem_thong_tin_y_te"}}
)
        
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            function_call = tool_calls[0]
            function_args = json.loads(function_call.function.arguments)
            
            return {
                "original_question": question,
                "intent": "tim_kiem_thong_tin_y_te",
                "confidence": 0.9,
                "extracted_features": function_args
            }
        else:
            return {
                "original_question": question,
                "intent": "general_question",
                "confidence": 0.5,
                "extracted_features": {}
            }
            
    except Exception as e:
        print(f"Error in extract_user_intent_and_features: {str(e)}")
        return {
            "original_question": question,
            "intent": "error",
            "confidence": 0.0,
            "extracted_features": {}
        }

def combined_search_with_filters(
    question: str,
    extracted_features: Dict[str, Any],
    n_results: int = 10
) -> Dict[str, Any]:
    """
    Perform hybrid semantic search with reranking for medical information.
    
    Args:
        question: User's medical question
        extracted_features: Extracted medical features from the question
        n_results: Number of initial results to retrieve (will be reranked)
        
    Returns:
        Dictionary with search results and metadata
    """
    try:
        logger.info(f"Searching for: {question}")
        
        collection = get_or_create_collection()
        count = collection.count()
        
        if count == 0:
            logger.warning("No data in database")
            return {"success": False, "message": "No data in database", "results": []}
        
        # Retrieve more results initially for reranking
        initial_n = min(n_results * 2, count)
        
        # Semantic search using PhoBERT embeddings
        logger.info(f"Performing semantic search (retrieving top {initial_n})")

        # 1) Embed query bằng PhoBERT
        query_vec = phobert_ef([question])[0]

        # 2) Query bằng vector
        results = collection.query(
            query_embeddings=[query_vec],
            n_results=initial_n,
            include=["metadatas", "documents", "distances"]
        )
        
        # Calculate combined scores and rerank
        scored_results = []
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            document = results['documents'][0][i]
            distance = results['distances'][0][i]
            
            # Calculate combined relevance score
            final_score, score_breakdown = calculate_combined_score(
                distance, question, document, metadata
            )
            
            scored_results.append({
                'id': results['ids'][0][i],
                'metadata': metadata,
                'document': document,
                'distance': distance,
                'relevance_score': final_score,
                'score_breakdown': score_breakdown,
                'confidence': 'high' if final_score > 0.7 else 'medium' if final_score > 0.5 else 'low'
            })
            
            # Debug log for each result
            logger.info(f"Candidate: {metadata.get('disease_name')} | Score: {final_score:.3f} | Breakdown: {score_breakdown}")
        
        # Sort by relevance score (descending)
        scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Filter by confidence threshold and take top n_results
        filtered_results = [
            r for r in scored_results
            if r['relevance_score'] >= CONFIDENCE_THRESHOLD
        ][:n_results]
        
        logger.info(f"Found {len(filtered_results)} relevant results (after filtering and reranking)")
        
        if filtered_results:
            logger.info(f"Top result: {filtered_results[0]['metadata'].get('disease_name')} "
                       f"(score: {filtered_results[0]['relevance_score']:.3f})")
        
        return {
            "success": True,
            "results": filtered_results,
            "total_found": len(filtered_results),
            "total_searched": initial_n
        }
        
    except Exception as e:
        logger.error(f"Error in search: {str(e)}", exc_info=True)
        return {"success": False, "message": str(e), "results": []}

def generate_natural_response(
    question: str,
    search_results: List[Dict],
    extracted_features: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate natural language response for medical queries using GPT.
    Includes safety checks and proper citations.
    
    Args:
        question: User's medical question
        search_results: Relevant search results from RAG
        extracted_features: Extracted medical features
        
    Returns:
        Dictionary with answer and metadata
    """
    try:
        logger.info("Generating response with GPT")
        
        # Check if we have good quality results
        if not search_results:
            return {
                "answer": """Xin lỗi, tôi không tìm thấy thông tin phù hợp trong cơ sở dữ liệu y tế để trả lời câu hỏi của bạn. Bạn hãy đề cập đến vấn đề y tế cụ thể hơn nhé.
                
⚠️ Khuyến cáo: Vui lòng tham khảo ý kiến bác sĩ chuyên khoa để được tư vấn chính xác và an toàn.""",
                "sources": [],
                "confidence": "none"
            }
        
        # Prepare context from search results
        context_parts = []
        for idx, result in enumerate(search_results[:3], 1):  # Use top 3 results
            metadata = result['metadata']
            context_parts.append(f"""
[Nguồn {idx}] Bệnh: {metadata.get('disease_name', 'N/A')}
- Triệu chứng: {metadata.get('symptoms', 'N/A')}
- Điều trị: {metadata.get('treatment', 'N/A')}
- Phòng ngừa: {metadata.get('prevention', 'N/A')}
- Độ liên quan: {result.get('relevance_score', 0):.2f}
""")
        
        context = "\n".join(context_parts)
        
        # Enhanced system prompt with safety guidelines
        system_prompt = """
Bạn là trợ lý y tế AI trả lời ngắn gọn, rõ ràng, tự nhiên như bác sĩ thật.
Quy tắc quan trọng:
1. Chỉ sử dụng thông tin từ [Nguồn] đã cung cấp.
2. Không chia Phần 1 / Phần 2 / Phần 3.
3. Trả lời mạch lạc như một đoạn tư vấn liên tục.
4. Luôn thêm khuyến cáo an toàn cuối câu: đây chỉ là thông tin tham khảo, vui lòng hỏi bác sĩ.
5. Không phóng đại, không chẩn đoán chắc chắn.
6. Nếu câu hỏi liên quan đến triệu chứng nguy hiểm → nhắc đi khám ngay.

Trả lời tự nhiên như một bác sĩ nói chuyện với bệnh nhân.
Luôn bắt đầu bằng một câu chào ngắn gọn, ví dụ: “Chào bạn,”.
"""
        
        user_prompt = f"""Câu hỏi của người dùng:
{question}

Thông tin y tế liên quan:
{context}

Thông tin trích xuất từ câu hỏi:
{json.dumps(extracted_features, ensure_ascii=False, indent=2)}

Hãy trả lời câu hỏi một cách chuyên nghiệp và an toàn."""
        
        # Call GPT API
        response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.7,
    max_tokens=800
)
        
        answer = response.choices[0].message.content
        
        # Add safety disclaimer if not already present
        if "bác sĩ" not in answer.lower() and "khám" not in answer.lower():
            answer += "\n\n⚠️ Lưu ý: Thông tin trên chỉ mang tính chất tham khảo. Vui lòng tham khảo ý kiến bác sĩ chuyên khoa để được tư vấn chính xác."
        
        # Determine overall confidence
        avg_score = np.mean([r.get('relevance_score', 0) for r in search_results[:3]])
        confidence = 'high' if avg_score > 0.7 else 'medium' if avg_score > 0.5 else 'low'
        
        logger.info(f"Response generated successfully (confidence: {confidence})")
        
        return {
            "answer": answer,
            "sources": search_results[:3],  # Return top 3 sources
            "confidence": confidence,
            "avg_relevance_score": round(avg_score, 3)
        }
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        return {
            "answer": """Xin lỗi, tôi đang gặp sự cố kỹ thuật khi tạo câu trả lời. Vui lòng thử lại sau.
            
⚠️ Nếu bạn đang gặp vấn đề sức khỏe cấp bách, vui lòng liên hệ bác sĩ hoặc cơ sở y tế ngay lập tức.""",
            "error": str(e),
            "sources": [],
            "confidence": "error"
        }
