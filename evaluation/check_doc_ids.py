"""
Script để kiểm tra doc IDs thật trong ChromaDB
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.medical_chatbot_service import get_or_create_collection

# Get collection
collection = get_or_create_collection()

# Get first 20 documents
results = collection.get(
    limit=20,
    include=["metadatas", "documents"]
)

print("=" * 60)
print("📋 SAMPLE DOC IDs IN CHROMADB")
print("=" * 60)

for i, doc_id in enumerate(results['ids'][:20], 1):
    metadata = results['metadatas'][i-1]
    disease_name = metadata.get('disease_name', metadata.get('original_question', 'N/A'))
    
    print(f"\n{i}. ID: {doc_id}")
    print(f"   Disease/Topic: {disease_name[:60]}...")

print("\n" + "=" * 60)
print(f"Total documents: {collection.count()}")
print("=" * 60)

# Search for specific diseases to find correct IDs
print("\n🔍 SEARCHING FOR SPECIFIC DISEASES:")
test_queries = [
    "Sốt xuất huyết",
    "Viêm gan B", 
    "Paracetamol",
    "COVID-19"
]

for query in test_queries:
    results = collection.query(
        query_texts=[query],
        n_results=3,
        include=["metadatas"]
    )
    
    print(f"\n📌 Query: '{query}'")
    print(f"   Top 3 matching doc IDs:")
    for i, doc_id in enumerate(results['ids'][0], 1):
        metadata = results['metadatas'][0][i-1]
        disease = metadata.get('disease_name', metadata.get('original_question', 'N/A'))
        print(f"   {i}. {doc_id} - {disease[:50]}...")
