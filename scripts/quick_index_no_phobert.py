"""
Quick Indexing without PhoBERT
==============================
Sử dụng Default Embedding của ChromaDB để index nhanh.
Dùng khi PhoBERT loading bị lỗi hoặc quá chậm.
"""

import json
import os
import sys
import chromadb
from chromadb.utils import embedding_functions

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("=" * 60)
    print("⚡ QUICK INDEXING (NO PHOBERT)")
    print("=" * 60)
    
    # 1. Setup paths
    workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'chroma_db')
    data_path = os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'hospital_specialties.json')
    
    print(f"📂 DB Path: {db_path}")
    print(f"📂 Data Path: {data_path}")
    
    # 2. Initialize ChromaDB
    print("\nInitializing ChromaDB...")
    client = chromadb.PersistentClient(path=db_path)
    
    # Use Default Embedding (Sentence Transformers all-MiniLM-L6-v2)
    # Lightweight and fast
    ef = embedding_functions.DefaultEmbeddingFunction()
    
    COLLECTION_NAME = "hospital_specialty_collection"
    
    # 3. Reset collection
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"✓ Deleted existing collection '{COLLECTION_NAME}'")
    except:
        pass
        
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"model": "default-miniLM"}
    )
    print(f"✓ Created new collection '{COLLECTION_NAME}'")
    
    # 4. Load Data
    print("\nLoading data...")
    with open(data_path, 'r', encoding='utf-8') as f:
        specialties = json.load(f)
    print(f"✓ Loaded {len(specialties)} specialties")
    
    # 5. Index
    print("\nIndexing...")
    
    documents = []
    metadatas = []
    ids = []
    
    for s in specialties:
        # Create rich text for embedding
        text = f"{s['specialty_name']}. {s['description']}. "
        text += f"Synonyms: {', '.join(s['synonyms'])}. "
        if s.get('symptoms'):
            text += f"Symptoms: {', '.join(s['symptoms'])}."
            
        documents.append(text)
        
        metadatas.append({
            'specialty_id': s['specialty_id'],
            'specialty_name': s['specialty_name'],
            'description': s['description'],
            'synonyms': json.dumps(s['synonyms'], ensure_ascii=False),
            'hospital_keywords': json.dumps(s['hospital_keywords'], ensure_ascii=False),
            'symptoms': json.dumps(s.get('symptoms', []), ensure_ascii=False)
        })
        
        ids.append(s['specialty_id'])
        print(f"   + Prepared: {s['specialty_name']}")
        
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"\n✅ Successfully indexed {len(ids)} items!")
    
    # 6. Verify
    print("\nVerifying search...")
    results = collection.query(
        query_texts=["bệnh viện chữa ung thư"],
        n_results=1
    )
    print(f"Query: 'bệnh viện chữa ung thư'")
    print(f"Result: {results['metadatas'][0][0]['specialty_name']}")
    
    print("\nDONE.")

if __name__ == "__main__":
    main()
