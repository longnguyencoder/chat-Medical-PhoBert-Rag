"""
Load medical Q&A dataset from CSV file

Usage:
    python load_csv_dataset.py --csv "path/to/your/dataset.csv"
"""

import argparse
import pandas as pd
from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction
from src.services.medical_chatbot_service import get_or_create_collection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_csv_dataset(csv_path: str):
    """
    Load Q&A dataset from CSV
    
    Args:
        csv_path: Path to CSV file
    
    Returns:
        pandas DataFrame
    """
    logger.info(f"Loading CSV: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        logger.info(f"✓ Loaded {len(df)} rows")
        logger.info(f"Columns: {df.columns.tolist()}")
        
        return df
    
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        raise


def convert_qa_to_medical_format(df: pd.DataFrame):
    """
    Convert Q&A dataset to medical document format
    
    Expected columns: id, question, answer, link (optional)
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame in medical format
    """
    logger.info("Converting to medical format...")
    
    medical_data = []
    
    for idx, row in df.iterrows():
        question = str(row.get('question', ''))
        answer = str(row.get('answer', ''))
        link = str(row.get('link', ''))
        
        if not question or not answer:
            continue
        
        # Use question as disease_name (truncate if too long)
        disease_name = question.replace('?', '').strip()
        if len(disease_name) > 150:
            disease_name = disease_name[:150] + '...'
        
        # Analyze answer to extract structured info
        answer_lower = answer.lower()
        
        # Extract symptoms
        symptoms = ''
        if any(kw in answer_lower for kw in ['triệu chứng', 'dấu hiệu', 'biểu hiện']):
            # Try to extract symptoms section
            symptoms = answer[:500]  # First 500 chars as symptoms
        
        # Extract treatment
        treatment = ''
        if any(kw in answer_lower for kw in ['điều trị', 'chữa', 'uống thuốc', 'dùng thuốc']):
            treatment = answer
        
        # Extract prevention
        prevention = ''
        if any(kw in answer_lower for kw in ['phòng ngừa', 'tránh', 'dự phòng']):
            prevention = answer
        
        # Create medical document
        medical_doc = {
            'disease_name': disease_name,
            'description': answer[:1000],  # Limit to 1000 chars
            'symptoms': symptoms,
            'causes': '',  # Not available in Q&A format
            'treatment': treatment[:1000] if treatment else '',
            'prevention': prevention[:1000] if prevention else '',
            'source': link if link and link != 'nan' else 'Medical Q&A Dataset',
            'original_question': question,
            'original_answer': answer
        }
        
        medical_data.append(medical_doc)
    
    result_df = pd.DataFrame(medical_data)
    logger.info(f"✓ Converted {len(result_df)} documents")
    
    return result_df


def index_to_chromadb(df: pd.DataFrame, batch_size: int = 100):
    """
    Index documents into ChromaDB
    
    Args:
        df: DataFrame with medical documents
        batch_size: Batch size for indexing
    """
    logger.info("Indexing to ChromaDB...")
    
    # Get collection
    collection = get_or_create_collection()
    current_count = collection.count()
    logger.info(f"Current collection size: {current_count}")
    
    # Prepare data
    documents = []
    metadatas = []
    ids = []
    
    for idx, row in df.iterrows():
        # Create document text (for embedding)
        # Combine question and answer for better semantic search
        doc_text = f"Câu hỏi: {row['original_question']} Trả lời: {row['description']}"
        documents.append(doc_text)
        
        # Create metadata
        metadata = {
            'disease_name': str(row['disease_name'])[:500],
            'description': str(row['description'])[:1000],
            'symptoms': str(row.get('symptoms', ''))[:1000],
            'causes': str(row.get('causes', ''))[:1000],
            'treatment': str(row.get('treatment', ''))[:1000],
            'prevention': str(row.get('prevention', ''))[:1000],
            'source': str(row.get('source', 'Unknown'))[:200],
            'original_question': str(row.get('original_question', ''))[:500],
            'original_answer': str(row.get('original_answer', ''))[:2000]
        }
        metadatas.append(metadata)
        
        # Create ID
        ids.append(f"csv_qa_{current_count + idx + 1}")
    
    # Add to collection in batches
    total_batches = (len(documents) - 1) // batch_size + 1
    
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
        logger.info(f"Indexed batch {batch_num}/{total_batches}")
    
    new_count = collection.count()
    added = new_count - current_count
    logger.info(f"✓ Indexed {added} new documents")
    logger.info(f"Total collection size: {new_count}")
    
    return new_count, added


def rebuild_bm25_index():
    """Rebuild BM25 index with new documents"""
    logger.info("Rebuilding BM25 index...")
    
    from src.services.medical_chatbot_service import initialize_bm25_index
    
    success = initialize_bm25_index()
    
    if success:
        logger.info("✓ BM25 index rebuilt successfully")
    else:
        logger.warning("⚠ BM25 index rebuild failed")
    
    return success


def main():
    parser = argparse.ArgumentParser(description='Load CSV medical Q&A dataset')
    parser.add_argument('--csv', type=str, required=True,
                       help='Path to CSV file')
    parser.add_argument('--preview', action='store_true',
                       help='Preview data without indexing')
    
    args = parser.parse_args()
    
    try:
        # Step 1: Load CSV
        df = load_csv_dataset(args.csv)
        
        # Step 2: Convert to medical format
        medical_df = convert_qa_to_medical_format(df)
        
        # Preview mode
        if args.preview:
            print("\n" + "="*60)
            print("PREVIEW MODE - First 5 documents:")
            print("="*60)
            print(medical_df.head().to_string())
            print("\n" + "="*60)
            print(f"Total documents: {len(medical_df)}")
            print("Run without --preview to index into ChromaDB")
            return 0
        
        # Step 3: Index to ChromaDB
        new_count, added = index_to_chromadb(medical_df)
        
        # Step 4: Rebuild BM25 index
        rebuild_bm25_index()
        
        # Summary
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print(f"CSV file: {args.csv}")
        print(f"Loaded: {len(df)} Q&A pairs")
        print(f"Added: {added} new documents")
        print(f"Total in ChromaDB: {new_count} documents")
        print(f"BM25 index: Rebuilt")
        print("="*60)
        print("\n💡 Next steps:")
        print("1. Restart server: python main.py")
        print("2. Test at: http://127.0.0.1:5000/api/docs")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
