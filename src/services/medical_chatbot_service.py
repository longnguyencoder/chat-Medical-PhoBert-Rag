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
from collections import defaultdict

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
from src.services.bm25_search import BM25SearchEngine, create_searchable_text

# Import Cross-Encoder for reranking
try:
    from sentence_transformers import CrossEncoder
    RERANKER = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    RERANKING_ENABLED = True
    logger.info("✓ Cross-Encoder loaded for reranking")
except ImportError:
    RERANKING_ENABLED = False
    logger.warning("⚠ sentence-transformers not installed. Reranking disabled.")

# Initialize BM25 search engine
BM25_ENGINE = BM25SearchEngine()
BM25_ENABLED = False  # Will be set to True after indexing

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

# Hybrid search weights (BM25 + Vector)
HYBRID_BM25_WEIGHT = 0.3  # 30% BM25 keyword matching
HYBRID_VECTOR_WEIGHT = 0.7  # 70% semantic vector search

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

def initialize_bm25_index():
    """
    Initialize BM25 index with all documents from ChromaDB.
    This should be called once at startup.
    """
    global BM25_ENABLED
    
    try:
        logger.info("Initializing BM25 index...")
        collection = get_or_create_collection()
        
        # Get all documents from ChromaDB
        all_docs = collection.get(
            include=["documents", "metadatas"]
        )
        
        if not all_docs['ids']:
            logger.warning("No documents found in ChromaDB. BM25 index not created.")
            return False
        
        # Create searchable texts from metadata
        searchable_texts = [
            create_searchable_text(metadata) 
            for metadata in all_docs['metadatas']
        ]
        
        # Index documents
        BM25_ENGINE.index_documents(
            documents=searchable_texts,
            document_ids=all_docs['ids'],
            metadatas=all_docs['metadatas']
        )
        
        BM25_ENABLED = True
        logger.info(f"✓ BM25 index initialized with {len(all_docs['ids'])} documents")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize BM25 index: {e}")
        BM25_ENABLED = False
        return False

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

def hybrid_search(
    question: str,
    n_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search combining BM25 (keyword) and Vector (semantic) search.
    
    Args:
        question: User's search query
        n_results: Number of results to return
        
    Returns:
        Combined and scored results from both search methods
    """
    results_dict = defaultdict(lambda: {'bm25_score': 0.0, 'vector_score': 0.0})
    
    # === BM25 KEYWORD SEARCH ===
    if BM25_ENABLED:
        try:
            bm25_results = BM25_ENGINE.search(question, top_k=n_results * 2)
            
            # Normalize BM25 scores to 0-1 range
            if bm25_results:
                max_bm25 = max(r['bm25_score'] for r in bm25_results)
                if max_bm25 > 0:
                    for result in bm25_results:
                        doc_id = result['id']
                        normalized_score = result['bm25_score'] / max_bm25
                        results_dict[doc_id]['bm25_score'] = normalized_score
                        results_dict[doc_id]['metadata'] = result['metadata']
                        results_dict[doc_id]['document'] = result['document']
                        results_dict[doc_id]['id'] = doc_id
            
            logger.info(f"BM25 found {len(bm25_results)} results")
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
    
    # === VECTOR SEMANTIC SEARCH ===
    try:
        collection = get_or_create_collection()
        query_vec = phobert_ef([question])[0]
        vector_results = collection.query(
            query_embeddings=[query_vec],
            n_results=n_results * 2,
            include=["metadatas", "documents", "distances"]
        )
        
        # Process vector results
        for i in range(len(vector_results['ids'][0])):
            doc_id = vector_results['ids'][0][i]
            distance = vector_results['distances'][0][i]
            
            # Normalize distance to similarity score (0-1)
            vector_score = normalize_similarity(distance)
            
            results_dict[doc_id]['vector_score'] = vector_score
            results_dict[doc_id]['metadata'] = vector_results['metadatas'][0][i]
            results_dict[doc_id]['document'] = vector_results['documents'][0][i]
            results_dict[doc_id]['id'] = doc_id
            results_dict[doc_id]['distance'] = distance
        
        logger.info(f"Vector search found {len(vector_results['ids'][0])} results")
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []
    
    # === COMBINE SCORES ===
    combined_results = []
    for doc_id, scores in results_dict.items():
        # Hybrid score: weighted combination
        hybrid_score = (
            HYBRID_BM25_WEIGHT * scores['bm25_score'] + 
            HYBRID_VECTOR_WEIGHT * scores['vector_score']
        )
        
        combined_results.append({
            'id': scores['id'],
            'metadata': scores['metadata'],
            'document': scores['document'],
            'bm25_score': scores['bm25_score'],
            'vector_score': scores['vector_score'],
            'hybrid_score': hybrid_score,
            'relevance_score': hybrid_score,  # For compatibility
            'distance': scores.get('distance', 0),
            'score_breakdown': {
                'bm25': round(scores['bm25_score'], 3),
                'vector': round(scores['vector_score'], 3),
                'hybrid': round(hybrid_score, 3)
            }
        })
    
    # Sort by hybrid score
    combined_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
    
    logger.info(f"Hybrid search combined {len(combined_results)} unique results")
    if combined_results:
        top = combined_results[0]
        logger.info(f"Top result: BM25={top['bm25_score']:.3f}, Vector={top['vector_score']:.3f}, Hybrid={top['hybrid_score']:.3f}")
    
    return combined_results[:n_results]

def combined_search_with_filters(
    question: str,
    extracted_features: Dict[str, Any],
    n_results: int = 10
) -> Dict[str, Any]:
    """
    Perform hybrid search with query expansion and reranking.
    
    FEATURES:
    - Hybrid Search: BM25 (keyword) + Vector (semantic)
    - Query Expansion: Generate similar queries to find more results
    - Reranking: Use Cross-Encoder to re-score results for better accuracy
    """
    try:
        logger.info(f"🔍 Hybrid search for: {question}")
        collection = get_or_create_collection()
        count = collection.count()
        if count == 0:
            logger.warning("No data in database")
            return {"success": False, "message": "No data in database", "results": []}
        
        # === QUERY EXPANSION ===
        expanded_queries = expand_query(question)
        logger.info(f"Expanded to {len(expanded_queries)} queries")
        
        # === HYBRID SEARCH (BM25 + Vector) ===
        all_results = {}  # Use dict to deduplicate by ID
        
        for query in expanded_queries:
            # Perform hybrid search for each expanded query
            hybrid_results = hybrid_search(query, n_results=n_results * 2)
            
            # Merge results (keep best score for each document)
            for result in hybrid_results:
                result_id = result['id']
                if result_id not in all_results or result['hybrid_score'] > all_results[result_id]['relevance_score']:
                    all_results[result_id] = {
                        'id': result_id,
                        'metadata': result['metadata'],
                        'document': result['document'],
                        'distance': result.get('distance', 0),
                        'relevance_score': result['hybrid_score'],
                        'score_breakdown': result['score_breakdown'],
                        'bm25_score': result['bm25_score'],
                        'vector_score': result['vector_score'],
                        'confidence': 'high' if result['hybrid_score'] > 0.7 else 'medium' if result['hybrid_score'] > 0.5 else 'low'
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
            "reranking_used": RERANKING_ENABLED,
            "hybrid_search_used": BM25_ENABLED,
            "search_method": "Hybrid (BM25 + Vector)" if BM25_ENABLED else "Vector Only"
        }
    except Exception as e:
        logger.error(f"Error in search: {str(e)}", exc_info=True)
        return {"success": False, "message": str(e), "results": []}

def generate_natural_response(
    question: str,
    search_results: List[Dict],
    extracted_features: Dict[str, Any],
    conversation_id: Optional[int] = None,
    user_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate natural language response using enhanced prompts.
    
    NEW: Includes conversation context and user personalization.
    """
    try:
        logger.info(f"Generating response with GPT (User: {user_name})")
        
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
        
        # Personalize greeting
        greeting_instruction = '- Bắt đầu bằng "Chào bạn,"'
        if user_name:
            greeting_instruction = f'- Bắt đầu bằng "Chào bạn {user_name},"'
        
        # Enhanced system prompt
        system_prompt = f"""
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
{greeting_instruction}
- Chia thành 2-3 đoạn ngắn
- Dùng bullet points (•) khi liệt kê
- Giọng điệu thân thiện, không gây hoảng loạn

VÍ DỤ TRẢ LỜI TỐT:
"Chào bạn {user_name if user_name else ''}, cảm cúm thường có các triệu chứng sau:

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
