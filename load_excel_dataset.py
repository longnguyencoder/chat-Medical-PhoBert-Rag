"""
Load Excel medical Q&A dataset into ChromaDB

This script loads test.xlsx and indexes into the medical chatbot database
"""

import pandas as pd
from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction
from src.services.medical_chatbot_service import get_or_create_collection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_excel_to_chromadb(excel_path: str = "src/scape/test.xlsx"):
    """
    Load Excel file and index into ChromaDB
    
    Args:
        excel_path: Path to Excel file
    """
    
    print("="*80)
    print("LOADING EXCEL DATASET INTO CHROMADB")
    print("="*80)
    
    # Step 1: Load Excel
    logger.info(f"Loading Excel: {excel_path}")
    df = pd.read_excel(excel_path)
    logger.info(f"✓ Loaded {len(df)} Q&A pairs")
    
    # Step 2: Get current collection size
    collection = get_or_create_collection()
    current_count = collection.count()
    logger.info(f"Current collection size: {current_count}")
    
    # Step 3: Prepare data for indexing
    logger.info("Preparing documents for indexing...")
    
    documents = []
    metadatas = []
    ids = []
    
    for idx, row in df.iterrows():
        question = str(row.get('question', ''))
        answer = str(row.get('answer', ''))
        link = str(row.get('link', ''))
        
        if not question or not answer or question == 'nan' or answer == 'nan':
            continue
        
        # Create document text (combine question + answer for better search)
        doc_text = f"Câu hỏi: {question} Trả lời: {answer}"
        documents.append(doc_text)
        
        # Extract disease name from question
        disease_name = question.replace('?', '').strip()
        if len(disease_name) > 150:
            disease_name = disease_name[:150] + '...'
        
        # Create metadata
        metadata = {
            'disease_name': disease_name[:500],
            'description': answer[:1000],
            'symptoms': '',
            'causes': '',
            'treatment': answer[:1000] if any(kw in answer.lower() for kw in ['điều trị', 'chữa', 'thuốc']) else '',
            'prevention': answer[:1000] if any(kw in answer.lower() for kw in ['phòng', 'tránh']) else '',
            'source': link[:200] if link and link != 'nan' else 'Medical Q&A Dataset',
            'original_question': question[:500],
            'original_answer': answer[:2000]
        }
        metadatas.append(metadata)
        
        # Create ID
        ids.append(f"excel_qa_{current_count + idx + 1}")
    
    logger.info(f"Prepared {len(documents)} documents")
    
    # Step 4: Index in batches
    batch_size = 100
    total_batches = (len(documents) - 1) // batch_size + 1
    
    logger.info(f"Indexing {len(documents)} documents in {total_batches} batches...")
    
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_meta = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        collection.add(
            documents=batch_docs,
            metadatas=batch_meta,
            ids=batch_ids
        )
        
        batch_num = i // batch_size + 1
        logger.info(f"✓ Indexed batch {batch_num}/{total_batches}")
    
    # Step 5: Verify
    new_count = collection.count()
    added = new_count - current_count
    
    logger.info(f"✓ Successfully indexed {added} new documents")
    logger.info(f"Total collection size: {new_count}")
    
    # Step 6: Rebuild BM25 index
    logger.info("Rebuilding BM25 index...")
    from src.services.medical_chatbot_service import initialize_bm25_index
    
    success = initialize_bm25_index()
    if success:
        logger.info("✓ BM25 index rebuilt successfully")
    else:
        logger.warning("⚠ BM25 index rebuild failed")
    
    # Summary
    print("\n" + "="*80)
    print("✅ SUCCESS!")
    print("="*80)
    print(f"Excel file: {excel_path}")
    print(f"Loaded: {len(df)} Q&A pairs")
    print(f"Indexed: {added} new documents")
    print(f"Total in ChromaDB: {new_count} documents")
    print(f"BM25 index: {'✓ Rebuilt' if success else '✗ Failed'}")
    print("="*80)
    print("\n💡 Next steps:")
    print("1. Restart server: python main.py")
    print("2. Test at: http://127.0.0.1:5000/api/docs")
    print("3. Try asking medical questions!")
    print("="*80)
    
    return new_count, added


if __name__ == "__main__":
    try:
        new_count, added = load_excel_to_chromadb()
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        exit(1)
