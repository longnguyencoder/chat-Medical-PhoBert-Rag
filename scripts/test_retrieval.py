import chromadb
import os
import sys

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.append(src_dir)

from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction

def test_retrieval():
    try:
        workspace_root = os.path.dirname(current_dir)
        chroma_db_path = os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'chroma_db')
        
        print(f"Connecting to ChromaDB at: {chroma_db_path}")
        client = chromadb.PersistentClient(path=chroma_db_path)
        phobert_ef = PhoBERTEmbeddingFunction()
        
        try:
            collection = client.get_collection("medical_collection", embedding_function=phobert_ef)
            print(f"Collection count: {collection.count()}")
            
            # Test queries
            queries = ["mụn nước khắp cơ thể", "thủy đậu", "nốt mụn nhỏ màu đỏ"]
            
            for q in queries:
                print(f"\nSearching for: '{q}'")
                results = collection.query(
                    query_texts=[q],
                    n_results=3,
                    include=["metadatas", "distances"]
                )
                
                for i in range(len(results['ids'][0])):
                    meta = results['metadatas'][0][i]
                    print(f"  - [{results['ids'][0][i]}] {meta.get('disease_name')} (Dist: {results['distances'][0][i]:.4f})")
                    
        except Exception as e:
            print(f"Error querying collection: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_retrieval()
