import os
import json
from dotenv import load_dotenv  # Import để load biến môi trường từ file .env (VD: API Key)

# Load biến môi trường
load_dotenv()
from openai import OpenAI  # Import thư viện OpenAI để gọi GPT
from typing import Dict, List, Optional, Any, Tuple  # Import Type Hinting để code rõ ràng hơn
import chromadb  # Import ChromaDB - Database Vector để lưu trữ kiến thức y tế
import numpy as np  # Import numpy để tính toán vector
import sys
import logging
import re
from collections import defaultdict  # Import defaultdict để dễ dàng gom nhóm kết quả tìm kiếm

# Cấu hình logging để theo dõi hoạt động hệ thống
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Thêm đường dẫn src vào system path để import các module khác
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(src_dir)

from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction  # Import model PhoBERT để chuyển văn bản thành Vector
from src.services.bm25_search import BM25SearchEngine, create_searchable_text  # Import công cụ tìm kiếm từ khóa BM25
from src.services.hospital_finder_service import hospital_finder_service  # Service tìm bệnh viện
from src.services.tool_calling_functions import AVAILABLE_TOOLS, execute_tool_call  # Các hàm hỗ trợ Agent gọi tool

# Import Cross-Encoder để sắp xếp lại kết quả (Reranking) - Giúp tăng độ chính xác
try:
    from sentence_transformers import CrossEncoder
    # Sử dụng model MS-MARCO MiniLM vì nó nhẹ và hiệu quả cho việc rerank
    RERANKER = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    RERANKING_ENABLED = True
    logger.info("✓ Cross-Encoder loaded for reranking")
except ImportError:
    RERANKING_ENABLED = False
    logger.warning("⚠ sentence-transformers not installed. Reranking disabled.")

# Khởi tạo bộ tìm kiếm BM25 (tìm kiếm theo từ khóa)
BM25_ENGINE = BM25SearchEngine()
BM25_ENABLED = False  # Sẽ được set thành True sau khi load dữ liệu xong

# Khởi tạo OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Khởi tạo ChromaDB Client (Lưu trữ Vector)
workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
chroma_client = chromadb.PersistentClient(path=os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'chroma_db'))

# Khởi tạo hàm Embedding PhoBERT (Dùng cho tiếng Việt)
phobert_ef = PhoBERTEmbeddingFunction()

# Danh sách từ khóa y tế quan trọng để tính điểm liên quan
MEDICAL_KEYWORDS = {
    'symptoms': ['triệu chứng', 'dấu hiệu', 'biểu hiện', 'sốt', 'ho', 'đau', 'ngứa', 'mệt', 'buồn nôn'],
    'treatment': ['điều trị', 'chữa', 'thuốc', 'uống', 'dùng', 'khám', 'bác sĩ'],
    'prevention': ['phòng ngừa', 'tránh', 'vệ sinh', 'vắc-xin', 'tiêm chủng'],
    'diagnosis': ['chẩn đoán', 'xét nghiệm', 'kiểm tra', 'khám']
}

# Ngưỡng tin cậy (Confidence Threshold)
# Nếu điểm số thấp hơn ngưỡng này thì coi như không liên quan
CONFIDENCE_THRESHOLD = 0.10  # Đã hạ thấp xuống 0.10 để lấy được nhiều kết quả hơn

# Trọng số cho Hybrid Search (Kết hợp BM25 và Vector)
# 70% điểm số dựa trên từ khóa (BM25) - Quan trọng vì thuật ngữ y tế cần chính xác
# 30% điểm số dựa trên ngữ nghĩa (Vector) - Giúp tìm các từ đồng nghĩa
HYBRID_BM25_WEIGHT = 0.7
HYBRID_VECTOR_WEIGHT = 0.3

# ═══════════════════════════════════════════════════════════════
# PHẦN 1: TỐI ƯU HÓA RAG (Query Expansion & Reranking)
# ═══════════════════════════════════════════════════════════════

def expand_query(question: str) -> List[str]:
    """
    Kỹ thuật Query Expansion: Mở rộng câu hỏi của user thành nhiều câu tương tự.
    Giúp tìm kiếm được nhiều kết quả hơn nếu user dùng từ không chuẩn.
    
    VD: "đau đầu" -> ["đau đầu là gì", "nguyên nhân gây nhức đầu", "đau đầu"]
    """
    try:
        # Prompt nhờ GPT tạo ra 2 câu hỏi tương tự
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
            model="gpt-4o-mini",  # Dùng model nhỏ cho nhanh và rẻ
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )
        
        expanded_text = response.choices[0].message.content.strip()
        expanded_queries = [q.strip() for q in expanded_text.split('\n') if q.strip()]
        
        # Luôn đưa câu hỏi gốc lên đầu tiên
        all_queries = [question] + expanded_queries[:2]
        logger.info(f"Query expansion: {question} → {len(all_queries)} queries")
        return all_queries
        
    except Exception as e:
        logger.warning(f"Query expansion failed: {e}. Using original query only.")
        return [question]

def generate_search_query_from_image(image_base64: str) -> str:
    """
    Dùng GPT-4o Vision để nhìn ảnh và sinh ra từ khóa tìm kiếm.
    VD: Ảnh chụp vết thương -> GPT trả về "vết thương hở, sưng tấy"
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Hãy nhìn bức ảnh này và liệt kê 3-5 từ khóa y tế quan trọng nhất bằng tiếng Việt để tìm kiếm trong cơ sở dữ liệu. VÍ DỤ: 'mẩn đỏ ngứa', 'vết thương hở', 'sưng tấy'. CHỈ TRẢ VỀ TỪ KHÓA, KHÔNG GIẢI THÍCH."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_base64 if image_base64.startswith("data:image") else f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=50
        )
        keywords = response.choices[0].message.content.strip()
        logger.info(f"🖼️ Image keywords extracted: {keywords}")
        return keywords
    except Exception as e:
        logger.error(f"Failed to extract keywords from image: {e}")
        return ""

def rewrite_query_with_context(question: str, conversation_id: int) -> str:
    """
    Viết lại câu hỏi dựa trên lịch sử chat (Contextual Rewriting).
    VD: 
       User: "Bệnh tiểu đường là gì?"
       Bot: "..."
       User: "Nó có nguy hiểm không?" -> Viết lại thành "Bệnh tiểu đường có nguy hiểm không?"
    """
    try:
        from src.models.message import Message
        
        # Lấy 2 tin nhắn gần nhất để hiểu ngữ cảnh
        recent_messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.sent_at.desc()).limit(2).all()
        
        if not recent_messages:
            return question
            
        recent_messages.reverse()
        history_text = "\n".join([f"{'User' if m.sender=='user' else 'Bot'}: {m.message_text}" for m in recent_messages])
        
        prompt = f"""Hãy viết lại câu hỏi cuối cùng của User để nó ĐẦY ĐỦ Ý NGHĨA, dựa vào ngữ cảnh trước đó.

Lịch sử:
{history_text}

Câu hỏi hiện tại: "{question}"

Yêu cầu:
- Nếu câu hỏi đã rõ ràng, giữ nguyên.
- Nếu câu hỏi thiếu chủ ngữ/ngữ cảnh (ví dụ: "Nó là gì?", "Uống thuốc gì?"), hãy thêm tên bệnh/vấn đề từ lịch sử vào.
- CHỈ trả về câu hỏi đã viết lại (hoặc câu gốc). KHÔNG giải thích.

Câu hỏi viết lại:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3, # Nhiệt độ thấp để chính xác
            max_tokens=100
        )
        
        rewritten = response.choices[0].message.content.strip()
        logger.info(f"🔄 Rewrote query: '{question}' -> '{rewritten}'")
        return rewritten
        
    except Exception as e:
        logger.warning(f"Query rewrite failed: {e}")
        return question

def rerank_results(question: str, results: List[Dict]) -> List[Dict]:
    """
    Sắp xếp lại kết quả tìm kiếm (Reranking) bằng Cross-Encoder.
    Cross-Encoder so sánh trực tiếp câu hỏi và văn bản để chấm điểm chính xác hơn Vector Search.
    """
    if not RERANKING_ENABLED or not results:
        return results
    
    try:
        # Chuẩn bị dữ liệu để đưa vào model: List các cặp [Câu hỏi, Văn bản]
        pairs = []
        for result in results:
            # Gom tất cả thông tin trong metadata thành 1 đoạn văn
            doc_text = f"{result['metadata'].get('disease_name', '')} "
            doc_text += f"{result['metadata'].get('symptoms', '')} "
            doc_text += f"{result['metadata'].get('treatment', '')}"
            pairs.append([question, doc_text])
        
        # Chấm điểm
        ce_scores = RERANKER.predict(pairs)
        
        # Gán điểm mới và tính điểm tổng hợp cuối cùng
        for i, result in enumerate(results):
            result['ce_score'] = float(ce_scores[i])
            # Điểm cuối cùng = 70% Rerank Score + 30% Original Score
            result['final_score'] = 0.7 * ce_scores[i] + 0.3 * result.get('relevance_score', 0)
        
        # Sắp xếp lại danh sách theo điểm final_score giảm dần
        reranked = sorted(results, key=lambda x: x['final_score'], reverse=True)
        
        logger.info(f"Reranked {len(results)} results. Top score: {reranked[0]['final_score']:.3f}")
        return reranked
        
    except Exception as e:
        logger.error(f"Reranking failed: {e}. Using original order.")
        return results

# ═══════════════════════════════════════════════════════════════
# TÓM TẮT HỘI THOẠI
# ═══════════════════════════════════════════════════════════════

def generate_conversation_summary(conversation_id: int) -> Optional[str]:
    """Hàm tóm tắt nội dung cuộc trò chuyện để lưu vào DB (hiển thị ở màn hình danh sách)"""
    try:
        from src.models.message import Message
        
        messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.sent_at).all()
        
        if not messages or len(messages) < 3:
            return None
        
        conversation_text = []
        for msg in messages:
            sender = "Người dùng" if msg.sender == 'user' else "Bác sĩ AI"
            conversation_text.append(f"{sender}: {msg.message_text}")
        
        full_conversation = "\n".join(conversation_text)
        
        prompt = f"""Bạn là trợ lý y tế. Hãy tóm tắt cuộc hội thoại sau thành 3-5 dòng NGẮN GỌN.

Cuộc hội thoại:
{full_conversation}

YÊU CẦU TÓM TẮT:
- Chỉ ghi các thông tin Y TẾ quan trọng
- Format: Bullet points (•)
- Bao gồm: Triệu chứng, thuốc đã dùng, tình trạng hiện tại
- KHÔNG giải thích, CHỈ liệt kê thông tin

Hãy tóm tắt:"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        summary = response.choices[0].message.content.strip()
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        return None

# ═══════════════════════════════════════════════════════════════
# CÁC HÀM HỖ TRỢ VECTOR DB & TÍNH TOÁN ĐIỂM SỐ
# ═══════════════════════════════════════════════════════════════

def get_or_create_collection():
    """Lấy hoặc tạo Collection trong ChromaDB"""
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
    Khởi tạo chỉ mục BM25 từ toàn bộ dữ liệu trong ChromaDB.
    Hàm này cần chạy 1 lần khi server khởi động.
    """
    global BM25_ENABLED
    
    try:
        logger.info("Initializing BM25 index...")
        collection = get_or_create_collection()
        
        # Lấy toàn bộ dữ liệu (documents và metadata)
        all_docs = collection.get(
            include=["documents", "metadatas"]
        )
        
        if not all_docs['ids']:
            logger.warning("No documents found in ChromaDB. BM25 index not created.")
            return False
        
        # Tạo văn bản searchable từ metadata (kết hợp tên bệnh, triệu chứng...)
        searchable_texts = [
            create_searchable_text(metadata) 
            for metadata in all_docs['metadatas']
        ]
        
        # Index dữ liệu vào BM25 Engine
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
    """Chuyển đổi khoảng cách L2 (Distance) thành điểm tương đồng (Similarity Score 0-1)"""
    if distance <= 0:
        return 1.0
    # Công thức: 1 / (1 + distance)
    sim = 1 / (1 + (distance / 10))
    return float(sim)

def extract_keywords(text: str) -> List[str]:
    """Tách từ khóa từ một đoạn văn (bỏ các từ nối stop_words)"""
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()
    stop_words = {'là', 'của', 'và', 'có', 'được', 'này', 'đó', 'các', 'cho', 'từ', 'với', 'một', 'những'}
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords

def calculate_keyword_match_score(question: str, document: str, metadata: Dict) -> float:
    """Tính điểm khớp từ khóa (Keyword Match) giữa câu hỏi và văn bản"""
    question_keywords = set(extract_keywords(question))
    
    # Tạo văn bản tổng hợp của document
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
    
    # Tính giao thoa (Jaccard Similarity)
    intersection = len(question_keywords & doc_keywords)
    union = len(question_keywords | doc_keywords)
    return intersection / union if union > 0 else 0.0

def calculate_medical_relevance_score(question: str, metadata: Dict) -> float:
    """Tính điểm cộng thêm nếu khớp đúng ngữ cảnh y tế (triệu chứng, điều trị...)"""
    question_lower = question.lower()
    score = 0.0
    for category, keywords in MEDICAL_KEYWORDS.items():
        if any(kw in question_lower for kw in keywords):
            # Nếu câu hỏi chứa từ khóa loại nào (VD: "điều trị"), kiểm tra xem document có trường đó không
            field_value = str(metadata.get(category, '')).lower()
            if field_value and len(field_value) > 5:
                score += 0.15 # Cộng điểm thưởng
    return min(score, 0.6)

def calculate_combined_score(
    distance: float,
    question: str,
    document: str,
    metadata: Dict
) -> Tuple[float, Dict[str, float]]:
    """Tính điểm tổng hợp từ các thành phần (Semantic + Keyword + Medical Context)"""
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
    """
    Dùng GPT để phân tích ý định người dùng (User Intent).
    Trích xuất các thực thể như: Tên bệnh, Triệu chứng, Thuốc...
    """
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

# ═══════════════════════════════════════════════════════════════
# CƠ CHẾ TÌM KIẾM CHÍNH (HYBRID SEARCH)
# ═══════════════════════════════════════════════════════════════

def hybrid_search(
    question: str,
    n_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Tìm kiếm kết hợp (Hybrid Search): BM25 + Vector.
    Output: Danh sách kết quả đã được chấm điểm tổng hợp.
    """
    results_dict = defaultdict(lambda: {'bm25_score': 0.0, 'vector_score': 0.0})
    
    # 1. TÌM KIẾM KEYWORD (BM25)
    if BM25_ENABLED:
        try:
            bm25_results = BM25_ENGINE.search(question, top_k=n_results * 2)
            
            # Chuẩn hóa điểm BM25 về khoảng 0-1 để cộng với điểm Vector
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
    
    # 2. TÌM KIẾM NGỮ NGHĨA (VECTOR SEARCH)
    try:
        collection = get_or_create_collection()
        query_vec = phobert_ef([question])[0] # Mã hóa câu hỏi thành Vector
        vector_results = collection.query(
            query_embeddings=[query_vec],
            n_results=n_results * 2,
            include=["metadatas", "documents", "distances"]
        )
        
        # Xử lý kết quả Vector
        for i in range(len(vector_results['ids'][0])):
            doc_id = vector_results['ids'][0][i]
            distance = vector_results['distances'][0][i]
            
            # Chuẩn hóa khoảng cách thành điểm Similarity (0-1)
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
    
    # 3. KẾT HỢP ĐIỂM SỐ (COMBINE)
    combined_results = []
    for doc_id, scores in results_dict.items():
        # Tính điểm Hybrid theo trọng số
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
            'relevance_score': hybrid_score,  # Giữ tên này để tương thích
            'distance': scores.get('distance', 0),
            'score_breakdown': {
                'bm25': round(scores['bm25_score'], 3),
                'vector': round(scores['vector_score'], 3),
                'hybrid': round(hybrid_score, 3)
            }
        })
    
    # Sắp xếp theo điểm Hybrid giảm dần
    combined_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
    
    return combined_results[:n_results]

def combined_search_with_filters(
    question: str,
    extracted_features: Dict[str, Any],
    n_results: int = 10
) -> Dict[str, Any]:
    """
    Hàm tìm kiếm CAO CẤP: Kết hợp tất cả kỹ thuật.
    1. Query Expansion (Mở rộng câu hỏi)
    2. Hybrid Search (BM25 + Vector) cho mỗi câu hỏi
    3. Merge & Deduplicate (Gộp kết quả)
    4. Reranking (Sắp xếp lại bằng Cross-Encoder)
    """
    try:
        logger.info(f"🔍 Hybrid search for: {question}")
        collection = get_or_create_collection()
        count = collection.count()
        if count == 0:
            logger.warning("No data in database")
            return {"success": False, "message": "No data in database", "results": []}
        
        # === BƯỚC 1: QUERY EXPANSION ===
        expanded_queries = expand_query(question)
        logger.info(f"Expanded to {len(expanded_queries)} queries")
        
        # === BƯỚC 2: HYBRID SEARCH CHO TỪNG QUERY ===
        all_results = {}  # Dict để loại bỏ trùng lặp (Key = ID)
        
        for query in expanded_queries:
            hybrid_results = hybrid_search(query, n_results=n_results * 2)
            
            # Gộp kết quả (giữ lại điểm cao nhất nếu trùng ID)
            for result in hybrid_results:
                result_id = result['id']
                if result_id not in all_results or result['hybrid_score'] > all_results[result_id]['relevance_score']:
                    all_results[result_id] = {
                        'id': result_id,
                        'metadata': result['metadata'],
                        'document': result['document'],
                        'distance': result.get('distance', 0),
                        'relevance_score': result['hybrid_score'], # Base hybrid score
                        'score_breakdown': result['score_breakdown'],
                        'bm25_score': result['bm25_score'],
                        'vector_score': result['vector_score'],
                        'confidence': 'high' if result['hybrid_score'] > 0.7 else 'medium' if result['hybrid_score'] > 0.5 else 'low'
                    }
        
        # Chuyển thành list và sắp xếp sơ bộ
        scored_results = list(all_results.values())
        scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Lấy top ứng viên để Rerank (Rerank tốn tài nguyên nên chỉ làm trên top đầu)
        top_candidates = scored_results[:n_results * 2]
        
        # === BƯỚC 3: RERANKING ===
        reranked_results = rerank_results(question, top_candidates)
        
        # Lọc kết quả và giới hạn số lượng
        filtered_results = [
            r for r in reranked_results
            if r.get('relevance_score', 0) >= CONFIDENCE_THRESHOLD  # Lọc bỏ kết quả điểm quá thấp
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
            "search_method": "Hybrid (BM25 + Vector)" if BM25_ENABLED else "Vector Only"
        }
    except Exception as e:
        logger.error(f"Error in search: {str(e)}", exc_info=True)
        return {"success": False, "message": str(e), "results": []}

# ═══════════════════════════════════════════════════════════════
# SINH CÂU TRẢ LỜI TỰ NHIÊN (GENERATION)
# ═══════════════════════════════════════════════════════════════

def generate_natural_response(
    question: str,
    search_results: List[Dict],
    extracted_features: Dict[str, Any],
    conversation_id: Optional[int] = None,
    user_name: Optional[str] = None,
    image_base64: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sinh câu trả lời tự nhiên bằng GPT-4o, kết hợp:
    1. Thông tin tìm kiếm được (Context)
    2. Lịch sử trò chuyện
    3. Hồ sơ sức khỏe người dùng
    4. Khả năng gọi Tool tự động (Agentic)
    """
    try:
        logger.info(f"Generating response with GPT (User: {user_name})")
        
        # 1. TẠO CONTEXT TỪ LỊCH SỬ CHAT
        conversation_context = ""
        conversation_summary = ""
        
        if conversation_id:
            try:
                from src.models.message import Message
                from src.models.conversation import Conversation
                
                # Lấy tóm tắt nếu có
                conversation = Conversation.query.get(conversation_id)
                if conversation and conversation.summary:
                    conversation_summary = conversation.summary
                
                # Lấy 5 tin nhắn gần nhất
                recent_messages = Message.query.filter_by(
                    conversation_id=conversation_id
                ).order_by(Message.sent_at.desc()).limit(5).all()
                
                if recent_messages:
                    recent_messages.reverse()
                    context_parts = []
                    for msg in recent_messages:
                        sender_label = "Người dùng" if msg.sender == 'user' else "Bác sĩ AI"
                        context_parts.append(f"{sender_label}: {msg.message_text}")
                    
                    conversation_context = "\n".join(context_parts)
            except Exception as e:
                logger.warning(f"Could not load conversation context: {e}")
        
        # 2. TẠO CONTEXT TỪ HỒ SƠ SỨC KHỎE
        health_profile_context = ""
        # (Lấy thông tin từ DB nhưng code logic hơi phức tạp nên bỏ qua việc query trực tiếp ở đây để tránh lỗi circular import)
        if conversation_id:
             try:
                from src.models.conversation import Conversation
                from src.services.health_profile_service import health_profile_service
                
                conversation = Conversation.query.get(conversation_id)
                if conversation:
                    profile_text = health_profile_service.format_profile_for_chatbot(conversation.user_id)
                    if profile_text:
                        health_profile_context = f"""
【HỒ SƠ SỨC KHỎE CÁ NHÂN】
{profile_text}

⚠️ QUAN TRỌNG: Hãy tham khảo hồ sơ này khi tư vấn. 
- Nếu user DỊ ỨNG với thuốc/thực phẩm nào → TUYỆT ĐỐI KHÔNG đề xuất
- Nếu có bệnh mãn tính → Lưu ý tương tác thuốc và chế độ ăn
"""
             except Exception as e:
                pass


        if not search_results:
            return {
                "answer": """Xin lỗi, tôi không tìm thấy thông tin phù hợp trong cơ sở dữ liệu y tế để trả lời câu hỏi của bạn.

⚠️ Khuyến cáo: Vui lòng tham khảo ý kiến bác sĩ chuyên khoa để được tư vấn chính xác và an toàn.""",
                "sources": [],
                "confidence": "none"
            }
        
        # 3. CHUẨN BỊ CONTEXT TỪ KẾT QUẢ TÌM KIẾM
        context_parts = []
        for idx, result in enumerate(search_results[:3], 1): # Lấy top 3 kết quả tốt nhất
            metadata = result['metadata']
            
            # Ưu tiên dùng câu trả lời gốc nếu có (High Quality Data)
            original_answer = metadata.get('original_answer', '')
            original_question = metadata.get('original_question', '')
            
            if original_answer and len(original_answer) > 50:
                context_parts.append(f"""
[Nguồn {idx}] {metadata.get('source', 'Medical Database')}
Câu hỏi gốc: {original_question if original_question else metadata.get('disease_name', 'N/A')}
Câu trả lời: {original_answer}
Độ liên quan: {result.get('relevance_score', 0):.2f}
""")
            else:
                # Nếu không, dùng thông tin cấu trúc
                context_parts.append(f"""
[Nguồn {idx}] Bệnh: {metadata.get('disease_name', 'N/A')}
- Triệu chứng: {metadata.get('symptoms', 'N/A')}
- Điều trị: {metadata.get('treatment', 'N/A')}
- Phòng ngừa: {metadata.get('prevention', 'N/A')}
- Độ liên quan: {result.get('relevance_score', 0):.2f}
""")
        context = "\n".join(context_parts)
        
        greeting_instruction = f'- Bắt đầu bằng "Chào bạn {user_name},"' if user_name else '- Bắt đầu bằng "Chào bạn,"'
        
        # 4. SYSTEM PROMPT (KỊCH BẢN CHÍNH CHO GPT)
        system_prompt = f"""
Bạn là Bác sĩ AI với 10 năm kinh nghiệm lâm sàng, chuyên tư vấn sức khỏe cho người Việt Nam.

QUY TẮC BẮT BUỘC (QUAN TRỌNG NHẤT):
1. ✅ SỬ DỤNG CHÍNH XÁC thông tin từ [Nguồn] được cung cấp nếu có
2. ✅ NẾU CÓ NGUỒN: Ưu tiên trích dẫn và bám sát nội dung
3. ⚠️ NẾU KHÔNG CÓ NGUỒN: Được phép sử dụng kiến thức y khoa chuẩn xác để tư vấn, NHƯNG phải bắt đầu bằng: "Dựa trên kiến thức y khoa tổng quát (không có trong dữ liệu cụ thể)..."
4. ❌ KHÔNG kê đơn thuốc cụ thể, chỉ đưa ra lời khuyên về nhóm thuốc hoặc hoạt chất
5. ❌ KHÔNG chẩn đoán khẳng định, luôn khuyên người dùng đi khám bác sĩ
6. ✅ Luôn giữ thái độ khách quan, khoa học và cảm thông

🤖 AUTONOMOUS DECISION MAKING (QUAN TRỌNG NHẤT):
Bạn có quyền truy cập vào các công cụ (tools) để CHỦ ĐỘNG hỗ trợ user:

**Tool 1: lay_thong_tin_nguoi_dung**
- Lấy hồ sơ sức khỏe, lịch uống thuốc, thuốc sắp uống
- ✅ TỰ ĐỘNG GỌI khi user nói về triệu chứng (đau đầu, sốt, ho...)
- ✅ TỰ ĐỘNG GỌI khi user hỏi về thuốc
- ✅ TỰ ĐỘNG GỌI để check dị ứng trước khi đề xuất

**Tool 2: tim_benh_vien_gan_nhat**
- Tìm bệnh viện gần user (cần vị trí GPS)
- Gọi khi user cần đi khám hoặc hỏi về bệnh viện

{health_profile_context if health_profile_context else ""}

CÁCH TRẢ LỜI:
{greeting_instruction}
- Trả lời DỰA TRÊN nội dung từ [Nguồn]
- Nếu nguồn có "Câu trả lời" gốc → Dùng nội dung đó
- Chia thành 2-3 đoạn ngắn, dùng bullet points (•)
- Giọng điệu thân thiện, không gây hoảng loạn

LUÔN KHUYẾN CÁO ĐI KHÁM BÁC SĨ NẾU:
• Triệu chứng kéo dài > 3 ngày
• Sốt cao > 39°C
• Có dấu hiệu nguy hiểm: khó thở, đau ngực, co giật
"""
        if image_base64:
             logger.info(f"Image attached. Using Vision capabilities.")
             system_prompt += "\n7. 🖼️ CÓ HÌNH ẢNH: Hãy phân tích hình ảnh được gửi kèm và đưa ra nhận xét y tế sơ bộ. Luôn cảnh báo đây chỉ là đánh giá dựa trên hình ảnh."
        
        
        # 5. USER PROMPT (CÂU HỎI VÀ NỘI DUNG)
        user_prompt_parts = []
        
        if conversation_id:
             try:
                from src.models.conversation import Conversation
                c = Conversation.query.get(conversation_id)
                if c:
                    user_prompt_parts.append(f"User ID: {c.user_id}")
                    user_prompt_parts.append(f"⚠️ Sử dụng user_id này khi gọi tool lay_thong_tin_nguoi_dung")
             except: pass
        
        user_prompt_parts.append(f"Câu hỏi hiện tại: {question}")
        
        if conversation_summary:
            user_prompt_parts.append(f"【Tóm tắt cuộc trò chuyện trước đó】\n{conversation_summary}")

        if conversation_context:
            user_prompt_parts.append(f"【Lịch sử hội thoại gần đây】\n{conversation_context}\n\n⚠️ LƯU Ý: Hãy tham khảo lịch sử để hiểu ngữ cảnh.")
        
        user_prompt_parts.append(f"【Thông tin y tế từ cơ sở dữ liệu】\n{context}")
        user_prompt_parts.append(f"【Thông tin trích xuất】\n{json.dumps(extracted_features, ensure_ascii=False)}")
        user_prompt_parts.append("Hãy trả lời theo đúng quy tắc.")
        
        user_prompt = "\n\n".join(user_prompt_parts)
        
        # 6. GỌI GPT (TOOL CALLING FLOW)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if image_base64:
             # Gửi cả Text và Ảnh
             user_content = []
             user_content.append({"type": "text", "text": user_prompt})
             user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_base64 if image_base64.startswith("data:image") else f"data:image/jpeg;base64,{image_base64}"
                }
             })
             messages.append({"role": "user", "content": user_content})
        else:
             messages.append({"role": "user", "content": user_prompt})

        # Gọi GPT Lần 1
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=AVAILABLE_TOOLS,  # Cung cấp danh sách công cụ
            tool_choice="auto",
            temperature=0.3,
            max_tokens=800
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        # 7. XỬ LÝ TOOL CALLING
        if tool_calls:
            logger.info(f"🔧 GPT triggered {len(tool_calls)} tool call(s)")
            messages.append(response_message)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                logger.info(f"Executing tool: {function_name}")
                
                # Thực thi tool
                function_response = execute_tool_call(tool_call)
                
                # Thêm kết quả vào hội thoại
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response
                })
            
            # Gọi GPT Lần 2 (có thông tin từ tool)
            second_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.3,
                max_tokens=800
            )
            
            answer = second_response.choices[0].message.content
            logger.info("✓ Tool calling completed, final answer generated")
        else:
            # Không gọi tool -> Lấy luôn câu trả lời
            answer = response_message.content
        
        # Thêm cảnh báo an toàn nếu GPT quên
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
