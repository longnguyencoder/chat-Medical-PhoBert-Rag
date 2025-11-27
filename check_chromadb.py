import chromadb
import os
import sys

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction

# Initialize ChromaDB client
chroma_db_path = os.path.join(current_dir, 'src', 'nlp_model', 'data', 'chroma_db')
print(f"ChromaDB path: {chroma_db_path}")

client = chromadb.PersistentClient(path=chroma_db_path)

# Initialize PhoBERT embedding function
phobert_ef = PhoBERTEmbeddingFunction()

try:
    # Get collection
    collection = client.get_collection(
        name="medical_collection",
        embedding_function=phobert_ef
    )
    
    # Check count
    count = collection.count()
    print(f"\n✓ Collection found!")
    print(f"Total documents: {count}")
    
    if count > 0:
        # Peek at some data
        print("\n" + "="*60)
        print("Sample data:")
        print("="*60)
        results = collection.peek(limit=2)
        
        for i, (doc_id, doc, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            print(f"\n[{i+1}] ID: {doc_id}")
            print(f"Disease: {metadata.get('disease_name')}")
            print(f"Document preview: {doc[:200]}...")
        
        # Test search with "cảm cúm"
        print("\n" + "="*60)
        print("Testing search: 'cảm cúm'")
        print("="*60)
        
        search_results = collection.query(
            query_texts=["cảm cúm"],
            n_results=3,
            include=["metadatas", "documents", "distances"]
        )
        
        print(f"\nFound {len(search_results['ids'][0])} results")
        
        for i in range(len(search_results['ids'][0])):
            print(f"\n[Result {i+1}]")
            print(f"  ID: {search_results['ids'][0][i]}")
            print(f"  Disease: {search_results['metadatas'][0][i].get('disease_name')}")
            print(f"  Distance: {search_results['distances'][0][i]:.4f}")
            print(f"  Document preview: {search_results['documents'][0][i][:150]}...")
    else:
        print("\n⚠️ Collection is empty! Need to run process_medical_data.py")
        
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    print("\nCollection might not exist. Run process_medical_data.py first.")
