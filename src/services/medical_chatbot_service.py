import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
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

# Import Cross-Encoder for reranking
try:
    from sentence_transformers import CrossEncoder
    RERANKER = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    RERANKING_ENABLED = True
    logger.info("✓ Cross-Encoder loaded for reranking")
except ImportError:
    RERANKING_ENABLED = False
    logger.warning("⚠ sentence-transformers not installed. Reranking disabled.")

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
CONFIDENCE_THRESHOLD = 0.15

# ═══════════════════════════════════════════════════════════════
# RAG OPTIMIZATION: Query Expansion & Reranking
# ═══════════════════════════════════════════════════════════════

def expand_query(question: str) -> List[str]:
    """
    Expand user query into multiple similar queries using GPT.
    This helps find more relevant results.
    
    Args:
        question: Original user question
        
    Returns:
        List of expanded queries (including original)
    """
    try:
        prompt = f"""Bạn là chuyên gia y tế. Hãy tạo 2 câu hỏi TƯƠNG TỰ (không giống hệt) với câu hỏi gốc.

Câu hỏi gốc: "{question}"

Yêu cầu:
- Giữ nguyên ý nghĩa y tế
- Dùng từ đồng nghĩa hoặc cách diễn đạt khác
- Mỗi câu trên 1 dòng
- KHÔNG giải thích, CHỈ trả về 2 câu hỏi

Ví dụ:
Câu gốc: "Sốt cao là bao nhiêu độ?"
Câu 1: Nhiệt độ cơ thể bao nhiêu được coi là sốt cao?
Câu 2: Sốt trên bao nhiêu độ C là nguy hiểm?
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )
        
        expanded_text = response.choices[0].message.content.strip()
        expanded_queries = [q.strip() for q in expanded_text.split('\n') if q.strip()]
        
        # Always include original question first
        all_queries = [question] + expanded_queries[:2]
        logger.info(f"Query expansion: {question} → {len(all_queries)} queries")
        return all_queries
        
    except Exception as e:
        logger.warning(f"Query expansion failed: {e}. Using original query only.")
        return [question]

def rerank_results(question: str, results: List[Dict]) -> List[Dict]:
    """
    Rerank search results using Cross-Encoder for better accuracy.
    
    Args:
        question: User's question
        results: List of search results from PhoBERT
        
    Returns:
        Reranked results sorted by Cross-Encoder scores
    """
    if not RERANKING_ENABLED or not results:
        return results
    
    try:
        # Prepare pairs for Cross-Encoder
        pairs = []
        for result in results:
            # Combine all relevant text from metadata
            doc_text = f"{result['metadata'].get('disease_name', '')} "
            doc_text += f"{result['metadata'].get('symptoms', '')} "
            doc_text += f"{result['metadata'].get('treatment', '')}"
            pairs.append([question, doc_text])
        
        # Get Cross-Encoder scores
        ce_scores = RERANKER.predict(pairs)
        
        # Add Cross-Encoder scores to results
        for i, result in enumerate(results):
            result['ce_score'] = float(ce_scores[i])
            # Combine with original relevance score (70% CE, 30% original)
            result['final_score'] = 0.7 * ce_scores[i] + 0.3 * result.get('relevance_score', 0)
        
        # Sort by final score
        reranked = sorted(results, key=lambda x: x['final_score'], reverse=True)
        
        logger.info(f"Reranked {len(results)} results. Top score: {reranked[0]['final_score']:.3f}")
        return reranked
        
    except Exception as e:
        logger.error(f"Reranking failed: {e}. Using original order.")
        return results

# ═══════════════════════════════════════════════════════════════
# CONVERSATION SUMMARY
# ═══════════════════════════════════════════════════════════════

def generate_conversation_summary(conversation_id: int) -> Optional[str]:
    """
    Generate a concise summary of the conversation using GPT.
    
    Args:
        conversation_id: ID of the conversation to summarize
        
    Returns:
        Concise summary string or None if failed
    """
    try:
        from src.models.message import Message
        
        # Get all messages in conversation
        messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.sent_at).all()
        
        if not messages or len(messages) < 3:
            return None  # Too few messages to summarize
        
        # Format conversation history
        conversation_text = []
        for msg in messages:
            sender = "Người dùng" if msg.sender == 'user' else "Bác sĩ AI"
            conversation_text.append(f"{sender}: {msg.message_text}")
        
        full_conversation = "\n".join(conversation_text)
        
        # Generate summary with GPT
        prompt = f"""Bạn là trợ lý y tế. Hãy tóm tắt cuộc hội thoại sau thành 3-5 dòng NGẮN GỌN.

Cuộc hội thoại:
{full_conversation}

YÊU CẦU TÓM TẮT:
- Chỉ ghi các thông tin Y TẾ quan trọng
- Format: Bullet points (•)
- Bao gồm: Triệu chứng, thuốc đã dùng, tình trạng hiện tại
- KHÔNG giải thích, CHỈ liệt kê thông tin

VÍ DỤ TÓM TẮT TỐT:
• Triệu chứng: Sốt 38°C, đau đầu, ho khan
• Đã dùng: Paracetamol 3 ngày
• Tình trạng: Chưa đỡ
• Khuyến cáo: Cần đi khám nếu không cải thiện

Hãy tóm tắt:"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Low temperature for consistent summaries
            max_tokens=200
        )
        
        summary = response.choices[0].message.content.strip()
        logger.info(f"✓ Generated summary for conversation {conversation_id}")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        return None


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
    """Convert L2 distance to a normalized similarity score"""
    if distance <= 0:
        return 1.0
    sim = 1 / (1 + (distance / 10))
    return float(sim)

def extract_keywords(text: str) -> List[str]:
    """Extract important keywords from text"""
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()
    stop_words = {'là', 'của', 'và', 'có', 'được', 'này', 'đó', 'các', 'cho', 'từ', 'với', 'một', 'những'}
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords

def calculate_keyword_match_score(question: str, document: str, metadata: Dict) -> float:
    """Calculate keyword matching score between question and document"""
    question_keywords = set(extract_keywords(question))
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
    intersection = len(question_keywords & doc_keywords)
    union = len(question_keywords | doc_keywords)
    return intersection / union if union > 0 else 0.0

def calculate_medical_relevance_score(question: str, metadata: Dict) -> float:
    """Calculate relevance score based on medical domain knowledge"""
    question_lower = question.lower()
    score = 0.0
    for category, keywords in MEDICAL_KEYWORDS.items():
        if any(kw in question_lower for kw in keywords):
            field_value = str(metadata.get(category, '')).lower()
            if field_value and len(field_value) > 5:
                score += 0.15
    return min(score, 0.6)

def calculate_combined_score(
    distance: float,
    question: str,
    document: str,
    metadata: Dict
) -> Tuple[float, Dict[str, float]]:
    """Calculate combined relevance score using multiple signals"""
    semantic_score = normalize_similarity(distance)
    keyword_score = calculate_keyword_match_score(question, document, metadata)
    medical_score = calculate_medical_relevance_score(question, metadata)
    final_score = (
        0.5 * semantic_score +
        0.3 * keyword_score +
        0.2 * medical_score
    )
    score_breakdown = {
        'semantic': round(semantic_score, 3),
        'keyword': round(keyword_score, 3),
        'medical': round(medical_score, 3),
        'final': round(final_score, 3)
    }
    return final_score, score_breakdown

def extract_user_intent_and_features(question: str) -> Dict[str, Any]:
    """Extract user intent and medical features using OpenAI"""
    tools_schema = [
        {
            "type": "function",
            "function": {
                "name": "tim_kiem_thong_tin_y_te",
                "description": "Trích xuất thông tin y tế từ câu hỏi người dùng",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "trieu_chung": {"type": "string", "description": "Các triệu chứng bệnh"},
                        "ten_benh": {"type": "string", "description": "Tên bệnh nghi ngờ"},
                        "thuoc": {"type": "string", "description": "Tên thuốc hoặc loại thuốc"},
                        "muc_dich": {"type": "string", "description": "Mục đích hỏi"}
                    },
                    "required": []
                }
            }
        }
    ]
    system_prompt = "Bạn là trợ lý y tế AI. Hãy phân tích câu hỏi và trích xuất thông tin y tế quan trọng."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            tools=tools_schema,
            tool_choice={"type": "function", "function": {"name": "tim_kiem_thong_tin_y_te"}}
        )
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            function_args = json.loads(tool_calls[0].function.arguments)
            return {
                "original_question": question,
                "intent": "tim_kiem_thong_tin_y_te",
                "confidence": 0.9,
                "extracted_features": function_args
            }
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
    Perform hybrid semantic search with query expansion and reranking.
    
    NEW FEATURES:
    - Query Expansion: Generate similar queries to find more results
    - Reranking: Use Cross-Encoder to re-score results for better accuracy
    """
    try:
        logger.info(f"Searching for: {question}")
        collection = get_or_create_collection()
        count = collection.count()
        if count == 0:
            logger.warning("No data in database")
            return {"success": False, "message": "No data in database", "results": []}
        
        # === QUERY EXPANSION ===
        expanded_queries = expand_query(question)
        logger.info(f"Expanded to {len(expanded_queries)} queries")
        
        # Search with all expanded queries
        all_results = {}  # Use dict to deduplicate by ID
        for query in expanded_queries:
            initial_n = min(n_results * 2, count)
            query_vec = phobert_ef([query])[0]
            results = collection.query(
                query_embeddings=[query_vec],
                n_results=initial_n,
                include=["metadatas", "documents", "distances"]
            )
            
            # Process results
            for i in range(len(results['ids'][0])):
                result_id = results['ids'][0][i]
                if result_id not in all_results:  # Avoid duplicates
                    metadata = results['metadatas'][0][i]
                    document = results['documents'][0][i]
                    distance = results['distances'][0][i]
                    final_score, score_breakdown = calculate_combined_score(
                        distance, question, document, metadata  # Use original question
                    )
                    all_results[result_id] = {
                        'id': result_id,
                        'metadata': metadata,
                        'document': document,
                        'distance': distance,
                        'relevance_score': final_score,
                        'score_breakdown': score_breakdown,
                        'confidence': 'high' if final_score > 0.7 else 'medium' if final_score > 0.5 else 'low'
                    }
        
        # Convert to list and sort
        scored_results = list(all_results.values())
        scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Take top candidates for reranking
        top_candidates = scored_results[:n_results * 2]
        
        # === RERANKING ===
        reranked_results = rerank_results(question, top_candidates)
        
        # Filter and limit
        filtered_results = [
            r for r in reranked_results
            if r.get('relevance_score', 0) >= CONFIDENCE_THRESHOLD
        ][:n_results]
        
        logger.info(f"Found {len(filtered_results)} relevant results (from {len(scored_results)} total)")
        if filtered_results:
            top = filtered_results[0]
            logger.info(f"Top result: {top['metadata'].get('disease_name')} "
                       f"(score: {top.get('final_score', top.get('relevance_score')):.3f})")
        
        return {
            "success": True,
            "results": filtered_results,
            "total_found": len(filtered_results),
            "total_searched": len(scored_results),
            "query_expansion_used": len(expanded_queries) > 1,
            "reranking_used": RERANKING_ENABLED
        }
    except Exception as e:
        logger.error(f"Error in search: {str(e)}", exc_info=True)
        return {"success": False, "message": str(e), "results": []}

def generate_natural_response(
    question: str,
    search_results: List[Dict],
    extracted_features: Dict[str, Any],
    conversation_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate natural language response using enhanced prompts.
    
    NEW: Includes conversation context from recent messages for better understanding.
    """
    try:
        logger.info("Generating response with GPT")
        
        # === CONVERSATION CONTEXT ===
        conversation_context = ""
        conversation_summary = ""
        
        if conversation_id:
            try:
                from src.models.message import Message
                from src.models.conversation import Conversation
                
                # Get conversation summary (if exists)
                conversation = Conversation.query.get(conversation_id)
                if conversation and conversation.summary:
                    conversation_summary = conversation.summary
                    logger.info("✓ Loaded conversation summary")
                
                # Get last 5 messages (excluding current question)
                recent_messages = Message.query.filter_by(
                    conversation_id=conversation_id
                ).order_by(Message.sent_at.desc()).limit(5).all()
                
                if recent_messages:
                    # Reverse to chronological order
                    recent_messages.reverse()
                    context_parts = []
                    for msg in recent_messages:
                        sender_label = "Người dùng" if msg.sender == 'user' else "Bác sĩ AI"
                        context_parts.append(f"{sender_label}: {msg.message_text}")
                    
                    conversation_context = "\n".join(context_parts)
                    logger.info(f"✓ Loaded {len(recent_messages)} recent messages for context")
            except Exception as e:
                logger.warning(f"Could not load conversation context: {e}")
        if not search_results:
            return {
                "answer": """Xin lỗi, tôi không tìm thấy thông tin phù hợp trong cơ sở dữ liệu y tế để trả lời câu hỏi của bạn.

⚠️ Khuyến cáo: Vui lòng tham khảo ý kiến bác sĩ chuyên khoa để được tư vấn chính xác và an toàn.""",
                "sources": [],
                "confidence": "none"
            }
        
        # Prepare context
        context_parts = []
        for idx, result in enumerate(search_results[:3], 1):
            metadata = result['metadata']
            context_parts.append(f"""
[Nguồn {idx}] Bệnh: {metadata.get('disease_name', 'N/A')}
- Triệu chứng: {metadata.get('symptoms', 'N/A')}
- Điều trị: {metadata.get('treatment', 'N/A')}
- Phòng ngừa: {metadata.get('prevention', 'N/A')}
- Độ liên quan: {result.get('relevance_score', 0):.2f}
""")
        context = "\n".join(context_parts)
        
        # Enhanced system prompt
        system_prompt = """
Bạn là Bác sĩ AI với 10 năm kinh nghiệm lâm sàng, chuyên tư vấn sức khỏe cho người Việt Nam.

QUY TẮC BẮT BUỘC:
1. CHỈ sử dụng thông tin từ [Nguồn] được cung cấp
2. KHÔNG chẩn đoán chắc chắn (dùng "có thể", "khả năng")
3. KHÔNG kê đơn thuốc cụ thể
4. LUÔN khuyến cáo đi khám bác sĩ nếu:
   • Triệu chứng kéo dài > 3 ngày
   • Sốt cao > 39°C
   • Có dấu hiệu nguy hiểm: khó thở, đau ngực, co giật

PHONG CÁCH:
- Bắt đầu bằng "Chào bạn,"
- Chia thành 2-3 đoạn ngắn
- Dùng bullet points (•) khi liệt kê
- Giọng điệu thân thiện, không gây hoảng loạn

VÍ DỤ TRẢ LỜI TỐT:
"Chào bạn, cảm cúm thường có các triệu chứng sau:

• Sốt nhẹ (37.5-38.5°C)
• Chảy nước mũi, nghẹt mũi
• Đau họng, ho khan

Bạn nên nghỉ ngơi đầy đủ, uống nhiều nước. Nếu sốt cao hoặc kéo dài quá 3 ngày, hãy đến gặp bác sĩ nhé."
"""
        
        
        # Build user prompt with conversation context
        user_prompt_parts = [f"Câu hỏi hiện tại: {question}"]
        
        # Add conversation summary if available
        if conversation_summary:
            user_prompt_parts.append(f"""
【Tóm tắt cuộc trò chuyện trước đó】
{conversation_summary}""")

        # Add conversation history if available
        if conversation_context:
            user_prompt_parts.append(f"""
【Lịch sử hội thoại gần đây】
{conversation_context}

⚠️ LƯU Ý: Hãy tham khảo lịch sử để hiểu ngữ cảnh. 
Ví dụ: Nếu user hỏi "còn cách nào khác?" thì "cách" đó đã được đề cập trước đó.""")
        
        user_prompt_parts.append(f"""
【Thông tin y tế từ cơ sở dữ liệu】
{context}

【Thông tin trích xuất】
{json.dumps(extracted_features, ensure_ascii=False)}

Hãy trả lời theo đúng quy tắc.""")
        
        user_prompt = "\n\n".join(user_prompt_parts)
        
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
        
        # Add safety disclaimer if needed
        if "bác sĩ" not in answer.lower() and "khám" not in answer.lower():
            answer += "\n\n⚠️ Lưu ý: Thông tin trên chỉ mang tính chất tham khảo. Vui lòng tham khảo ý kiến bác sĩ chuyên khoa."
        
        avg_score = np.mean([r.get('relevance_score', 0) for r in search_results[:3]])
        confidence = 'high' if avg_score > 0.7 else 'medium' if avg_score > 0.5 else 'low'
        
        logger.info(f"Response generated successfully (confidence: {confidence})")
        
        return {
            "answer": answer,
            "sources": search_results[:3],
            "confidence": confidence,
            "avg_relevance_score": round(avg_score, 3)
        }
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        return {
            "answer": """Xin lỗi, tôi đang gặp sự cố kỹ thuật. Vui lòng thử lại sau.

⚠️ Nếu bạn đang gặp vấn đề sức khỏe cấp bách, vui lòng liên hệ bác sĩ ngay lập tức.""",
            "error": str(e),
            "sources": [],
            "confidence": "error"
        }
