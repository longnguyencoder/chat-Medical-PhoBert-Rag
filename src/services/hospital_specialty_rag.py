"""
Hospital Specialty RAG Service
================================
Service sử dụng RAG (Retrieval-Augmented Generation) để tìm kiếm chuyên khoa bệnh viện
thông minh hơn bằng Semantic Search.

Chức năng:
- Semantic search cho hospital specialties
- Query expansion với GPT
- Hybrid matching (semantic + keyword)
- Fallback mechanism
"""

import os
import json
import logging
from typing import List, Dict, Optional
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Import embedding function
from chromadb.utils import embedding_functions

# Initialize clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Use Default Embedding (Sentence Transformers) for stability/speed
# This avoids PhoBERT loading issues and matches quick_index_no_phobert.py
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

# ChromaDB setup
workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
chroma_client = chromadb.PersistentClient(
    path=os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'chroma_db')
)

# Collection name
COLLECTION_NAME = "hospital_specialty_collection"

# ═══════════════════════════════════════════════════════════════
# COLLECTION MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def initialize_hospital_specialty_collection() -> bool:
    """
    Khởi tạo ChromaDB collection cho hospital specialties.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Try to get existing collection
        try:
            collection = chroma_client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=embedding_fn
            )
            logger.info(f"✓ Collection '{COLLECTION_NAME}' already exists with {collection.count()} items")
            return True
        except Exception:
            # Collection doesn't exist, create new one
            try:
                collection = chroma_client.create_collection(
                    name=COLLECTION_NAME,
                    embedding_function=embedding_fn,
                    metadata={"description": "Hospital specialties for semantic search"}
                )
                logger.info(f"✓ Created new collection '{COLLECTION_NAME}'")
                
                # AUTO-INDEXING: Load data immediately if collection is new
                try:
                    data_path = os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'hospital_specialties.json')
                    logger.info(f"⏳ Auto-indexing data from {data_path}...")
                    
                    with open(data_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    index_hospital_specialties(data)
                    return True
                except Exception as index_err:
                    logger.error(f"✗ Auto-indexing failed: {index_err}")
                    return False
                    
            except Exception as create_err:
                 logger.error(f"✗ Failed to create collection: {create_err}")
                 return False
            
    except Exception as e:
        logger.error(f"✗ Failed to initialize collection: {e}")
        return False


def index_hospital_specialties(specialties_data: List[Dict]) -> bool:
    """
    Index hospital specialties vào ChromaDB.
    
    Args:
        specialties_data: List of specialty dictionaries
        
    Returns:
        bool: True nếu thành công
    """
    try:
        collection = chroma_client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn
        )
        
        # Clear existing data (optional - comment out if you want to append)
        # collection.delete()
        
        documents = []
        metadatas = []
        ids = []
        
        for specialty in specialties_data:
            # Create searchable document text
            doc_text = f"{specialty['specialty_name']}. "
            doc_text += f"{specialty['description']}. "
            doc_text += f"Từ đồng nghĩa: {', '.join(specialty['synonyms'])}. "
            
            if specialty.get('symptoms'):
                doc_text += f"Triệu chứng: {', '.join(specialty['symptoms'])}."
            
            documents.append(doc_text)
            
            # Metadata
            metadatas.append({
                'specialty_id': specialty['specialty_id'],
                'specialty_name': specialty['specialty_name'],
                'description': specialty['description'],
                'synonyms': json.dumps(specialty['synonyms'], ensure_ascii=False),
                'hospital_keywords': json.dumps(specialty['hospital_keywords'], ensure_ascii=False),
                'symptoms': json.dumps(specialty.get('symptoms', []), ensure_ascii=False),
                'osm_tags': json.dumps(specialty.get('osm_tags', []), ensure_ascii=False)
            })
            
            ids.append(specialty['specialty_id'])
        
        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"✓ Indexed {len(specialties_data)} specialties into ChromaDB")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to index specialties: {e}", exc_info=True)
        return False


# ═══════════════════════════════════════════════════════════════
# SEMANTIC SEARCH
# ═══════════════════════════════════════════════════════════════

def semantic_search_specialty(query: str, top_k: int = 5) -> List[Dict]:
    """
    Tìm kiếm chuyên khoa bằng semantic search.
    
    Args:
        query: Câu hỏi của user (VD: "bệnh viện chữa ung thư")
        top_k: Số lượng kết quả trả về
        
    Returns:
        List of specialty dictionaries với similarity scores
    """
    try:
        # Tự động init collection nếu chưa có
        try:
             collection = chroma_client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=embedding_fn
            )
        except:
             logger.info("Collection missing during search, attempting to initialize...")
             initialize_hospital_specialty_collection()
             collection = chroma_client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=embedding_fn
            )
        
        # Encode query và search
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["metadatas", "documents", "distances"]
        )
        
        # Parse results
        specialties = []
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]
            
            # Convert distance to similarity score (0-1)
            similarity = 1 / (1 + distance)
            
            specialties.append({
                'specialty_id': metadata['specialty_id'],
                'specialty_name': metadata['specialty_name'],
                'description': metadata['description'],
                'synonyms': json.loads(metadata['synonyms']),
                'hospital_keywords': json.loads(metadata['hospital_keywords']),
                'symptoms': json.loads(metadata['symptoms']),
                'similarity_score': round(similarity, 3),
                'distance': round(distance, 3)
            })
        
        logger.info(f"🔍 Semantic search for '{query}': found {len(specialties)} specialties")
        if specialties:
            logger.info(f"   Top match: {specialties[0]['specialty_name']} (score: {specialties[0]['similarity_score']})")
        
        return specialties
        
    except Exception as e:
        logger.error(f"✗ Semantic search failed: {e}", exc_info=True)
        return []


# ═══════════════════════════════════════════════════════════════
# QUERY EXPANSION
# ═══════════════════════════════════════════════════════════════

def expand_specialty_query_with_gpt(query: str) -> str:
    """
    Mở rộng query bằng GPT để hiểu rõ hơn ý định user.
    
    VD: "ung thư" → "ung thư, ung bướu, khối u"
    
    Args:
        query: Query gốc
        
    Returns:
        Expanded query string
    """
    try:
        prompt = f"""Bạn là chuyên gia y tế. Hãy mở rộng từ khóa tìm kiếm bệnh viện sau thành các từ đồng nghĩa hoặc liên quan.

Từ khóa gốc: "{query}"

Yêu cầu:
- Liệt kê 3-5 từ đồng nghĩa hoặc liên quan (tiếng Việt)
- Ngăn cách bằng dấu phẩy
- CHỈ trả về danh sách từ, KHÔNG giải thích

Ví dụ:
Input: "ung thư"
Output: ung thư, ung bướu, khối u, hóa trị, xạ trị

Hãy mở rộng:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )
        
        expanded = response.choices[0].message.content.strip()
        logger.info(f"🔄 Query expansion: '{query}' → '{expanded}'")
        return expanded
        
    except Exception as e:
        logger.warning(f"⚠ Query expansion failed: {e}. Using original query.")
        return query


# ═══════════════════════════════════════════════════════════════
# HYBRID MATCHING
# ═══════════════════════════════════════════════════════════════

def hybrid_specialty_matching(query: str, top_k: int = 5) -> List[str]:
    """
    Kết hợp semantic search và query expansion để tìm hospital keywords.
    
    Args:
        query: User query (VD: "bệnh viện chữa ung thư")
        top_k: Số lượng specialties để xem xét
        
    Returns:
        List of hospital keywords để filter OSM results
    """
    try:
        # Step 1: Semantic search
        specialties = semantic_search_specialty(query, top_k=top_k)
        
        if not specialties:
            logger.warning("⚠ No specialties found via semantic search")
            return []
        
        # Step 2: Extract hospital keywords from top matches
        all_keywords = []
        for specialty in specialties:
            # Only use high-confidence matches (similarity > 0.6)
            if specialty['similarity_score'] > 0.6:
                keywords = specialty['hospital_keywords']
                all_keywords.extend(keywords)
                logger.info(f"   ✓ {specialty['specialty_name']}: {len(keywords)} keywords (score: {specialty['similarity_score']})")
        
        # Deduplicate
        unique_keywords = list(set(all_keywords))
        
        logger.info(f"✓ Hybrid matching found {len(unique_keywords)} unique hospital keywords")
        return unique_keywords
        
    except Exception as e:
        logger.error(f"✗ Hybrid matching failed: {e}", exc_info=True)
        return []


# ═══════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_specialty_by_name(specialty_name: str) -> Optional[Dict]:
    """
    Lấy thông tin chi tiết của một chuyên khoa theo tên.
    
    Args:
        specialty_name: Tên chuyên khoa
        
    Returns:
        Specialty dictionary hoặc None
    """
    try:
        collection = chroma_client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn
        )
        
        results = collection.get(
            where={"specialty_name": specialty_name},
            include=["metadatas"]
        )
        
        if results['ids']:
            metadata = results['metadatas'][0]
            return {
                'specialty_id': metadata['specialty_id'],
                'specialty_name': metadata['specialty_name'],
                'description': metadata['description'],
                'synonyms': json.loads(metadata['synonyms']),
                'hospital_keywords': json.loads(metadata['hospital_keywords']),
                'symptoms': json.loads(metadata['symptoms'])
            }
        return None
        
    except Exception as e:
        logger.error(f"✗ Failed to get specialty: {e}")
        return None


def list_all_specialties() -> List[str]:
    """
    Liệt kê tất cả các chuyên khoa đã được index.
    
    Returns:
        List of specialty names
    """
    try:
        collection = chroma_client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn
        )
        
        results = collection.get(include=["metadatas"])
        specialty_names = [m['specialty_name'] for m in results['metadatas']]
        
        return sorted(specialty_names)
        
    except Exception as e:
        logger.error(f"✗ Failed to list specialties: {e}")
        return []


# ═══════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test the service
    print("🧪 Testing Hospital Specialty RAG Service\n")
    
    # Test 1: Initialize collection
    print("1. Initializing collection...")
    success = initialize_hospital_specialty_collection()
    print(f"   Result: {'✓ Success' if success else '✗ Failed'}\n")
    
    # Test 2: Semantic search
    print("2. Testing semantic search...")
    test_queries = [
        "bệnh viện chữa ung thư",
        "bệnh viện tim",
        "đau ngực khó thở",
        "bệnh viện sản",
        "bệnh viện trẻ em"
    ]
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        results = semantic_search_specialty(query, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"      {i}. {r['specialty_name']} (score: {r['similarity_score']})")
    
    # Test 3: Hybrid matching
    print("\n3. Testing hybrid matching...")
    query = "bệnh viện chữa ung thư"
    keywords = hybrid_specialty_matching(query, top_k=3)
    print(f"   Query: '{query}'")
    print(f"   Keywords: {keywords}")
    
    # Test 4: Query expansion
    print("\n4. Testing query expansion...")
    query = "ung thư"
    expanded = expand_specialty_query_with_gpt(query)
    print(f"   Original: '{query}'")
    print(f"   Expanded: '{expanded}'")
    
    print("\n✓ All tests completed!")
