import chromadb
import os
import sys

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(src_dir)

from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction

def check_disease_data():
    """Check disease data from medical_data.csv in ChromaDB"""
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
        
        # Get all records
        results = collection.get()
        
        # Filter disease records
        disease_records = []
        for i, (id, metadata) in enumerate(zip(results['ids'], results['metadatas'])):
            if metadata.get('doc_type') == 'disease':
                disease_records.append({
                    'id': id,
                    'disease_name': metadata.get('disease_name'),
                    'symptoms': metadata.get('symptoms')
                })
        
        # Print summary
        print("\n" + "="*70)
        print("DISEASE DATA FROM medical_data.csv IN CHROMADB")
        print("="*70)
        print(f"Total disease records: {len(disease_records)}")
        print("="*70 + "\n")
        
        # Show first 10 diseases
        print("First 10 disease records:")
        print("-"*70)
        for i, record in enumerate(disease_records[:10], 1):
            print(f"\n[{i}] ID: {record['id']}")
            print(f"Tên bệnh: {record['disease_name']}")
            print(f"Triệu chứng: {record['symptoms'][:100]}...")
        
        # Check for specific disease (Thủy đậu)
        print("\n" + "="*70)
        print("Checking for 'Thủy đậu' (Chickenpox):")
        print("-"*70)
        
        found = False
        for record in disease_records:
            if 'Thủy đậu' in record['disease_name']:
                print(f"✓ FOUND: {record['disease_name']}")
                print(f"  ID: {record['id']}")
                print(f"  Triệu chứng: {record['symptoms']}")
                found = True
                break
        
        if not found:
            print("✗ NOT FOUND: Thủy đậu")
        
        print("\n" + "="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_disease_data()
