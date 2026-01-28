import chromadb
import os
import sys

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(src_dir)

from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction

def count_chroma_records():
    """Count records in ChromaDB"""
    try:
        # Get ChromaDB path
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        chroma_db_path = os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'chroma_db')
        
        print(f"Connecting to ChromaDB at: {chroma_db_path}")
        
        # Connect to ChromaDB
        chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        
        # Initialize PhoBERT
        phobert_ef = PhoBERTEmbeddingFunction()
        
        # Get collection
        collection = chroma_client.get_collection(
            name="medical_collection",
            embedding_function=phobert_ef
        )
        
        # Count total records
        total_count = collection.count()
        
        # Get all records to count by type
        results = collection.get()
        
        disease_count = 0
        qa_count = 0
        
        for metadata in results['metadatas']:
            doc_type = metadata.get('doc_type', '')
            if doc_type == 'disease':
                disease_count += 1
            elif doc_type == 'qa':
                qa_count += 1
        
        # Print summary
        print("\n" + "="*60)
        print("CHROMADB MEDICAL COLLECTION SUMMARY")
        print("="*60)
        print(f"Total records: {total_count}")
        print(f"  - Disease records: {disease_count}")
        print(f"  - Q&A records: {qa_count}")
        print("="*60 + "\n")
        
        # Show sample Q&A records
        print("Sample Q&A records:")
        print("-"*60)
        qa_shown = 0
        for i, (id, metadata) in enumerate(zip(results['ids'], results['metadatas'])):
            if metadata.get('doc_type') == 'qa' and qa_shown < 5:
                question = metadata.get('question', 'N/A')
                answer = metadata.get('answer', 'N/A')
                source = metadata.get('source_link', 'N/A')
                
                print(f"\n[{qa_shown + 1}] ID: {id}")
                print(f"Q: {question[:100]}...")
                print(f"A: {answer[:100]}...")
                print(f"Source: {source}")
                qa_shown += 1
        
        print("\n" + "="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    count_chroma_records()
