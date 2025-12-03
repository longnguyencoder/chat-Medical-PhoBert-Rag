"""
Verify ChromaDB data and search for specific question
"""

from src.services.medical_chatbot_service import get_or_create_collection
from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction

# Get collection
collection = get_or_create_collection()

print("="*80)
print("CHROMADB VERIFICATION")
print("="*80)

# Check total count
total = collection.count()
print(f"\nTotal documents in ChromaDB: {total}")

# Search for the specific question
question = "Trẻ sốt, ăn kém, chướng bụng phình to cảnh báo điều gì?"

print(f"\nSearching for: {question}")
print("-"*80)

# Initialize embedding function
phobert_ef = PhoBERTEmbeddingFunction()

# Create embedding
query_vec = phobert_ef([question])[0]

# Search
results = collection.query(
    query_embeddings=[query_vec],
    n_results=5,
    include=["metadatas", "documents", "distances"]
)

# Display results
if results and results['ids'] and results['ids'][0]:
    print(f"\nFound {len(results['ids'][0])} results:\n")
    
    for i in range(len(results['ids'][0])):
        print(f"\n{'='*80}")
        print(f"Result {i+1}:")
        print(f"{'='*80}")
        print(f"ID: {results['ids'][0][i]}")
        print(f"Distance: {results['distances'][0][i]:.4f}")
        
        metadata = results['metadatas'][0][i]
        print(f"\nOriginal Question: {metadata.get('original_question', 'N/A')[:200]}")
        print(f"\nOriginal Answer: {metadata.get('original_answer', 'N/A')[:300]}...")
        print(f"\nSource: {metadata.get('source', 'N/A')[:100]}")
else:
    print("\n❌ No results found!")

print("\n" + "="*80)
