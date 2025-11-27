import chromadb
import os
import json
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(src_dir)

from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction

def read_medical_chroma():
    """Read and display medical data from ChromaDB"""
    try:
        # Initialize ChromaDB client
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        chroma_db_path = os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'chroma_db')
        
        logger.info(f"Connecting to ChromaDB at: {chroma_db_path}")
        chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        
        # Initialize PhoBERT embedding function
        phobert_ef = PhoBERTEmbeddingFunction()
        
        # Get collection
        logger.info("Getting medical_collection...")
        collection = chroma_client.get_collection(
            name="medical_collection",
            embedding_function=phobert_ef
        )
        
        # Get all data
        results = collection.get()
        
        # Print summary
        print("\n" + "="*70)
        print("MEDICAL KNOWLEDGE BASE SUMMARY")
        print("="*70)
        print(f"Total medical records: {len(results['ids'])}")
        print(f"Collection name: medical_collection")
        print(f"Embedding model: PhoBERT (vinai/phobert-base)")
        print("="*70 + "\n")
        
        # Print details for each record
        print("MEDICAL RECORDS:")
        print("-"*70)
        
        for i, (id, metadata, document) in enumerate(zip(results['ids'], results['metadatas'], results['documents']), 1):
            print(f"\n[{i}] ID: {id}")
            print(f"Bệnh: {metadata.get('disease_name', 'N/A')}")
            print(f"Triệu chứng: {metadata.get('symptoms', 'N/A')[:100]}...")
            print(f"Điều trị: {metadata.get('treatment', 'N/A')[:100]}...")
            print("-"*70)
        
        # Test embedding dimension
        if results['ids']:
            test_embedding = phobert_ef(["Test"])
            print(f"\n✓ Embedding dimension: {len(test_embedding[0])}")
            print(f"✓ Expected dimension for PhoBERT-base: 768")
        
        # Save to JSON for inspection
        output_data = []
        for id, metadata, document in zip(results['ids'], results['metadatas'], results['documents']):
            output_data.append({
                'id': id,
                'disease_name': metadata.get('disease_name'),
                'symptoms': metadata.get('symptoms'),
                'treatment': metadata.get('treatment'),
                'prevention': metadata.get('prevention'),
                'description': metadata.get('description'),
                'document': document
            })
        
        output_file = os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'medical_chroma_data.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Detailed data exported to: {output_file}")
        print("\n" + "="*70 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Error reading ChromaDB: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    read_medical_chroma()
