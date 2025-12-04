"""
Load and index medical Q&A dataset from HuggingFace

Usage:
    python load_huggingface_dataset.py --dataset "username/dataset-name"
"""

import argparse
from datasets import load_dataset
import pandas as pd
from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction
from src.services.medical_chatbot_service import get_or_create_collection
from src.services.bm25_search import BM25SearchEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_hf_dataset(dataset_name: str, split: str = 'train'):
    """
    Load dataset from HuggingFace
    
    Args:
        dataset_name: HuggingFace dataset name (e.g., 'username/medical-qa')
        split: Dataset split ('train', 'test', 'validation')
    
    Returns:
        pandas DataFrame
    """
    logger.info(f"Loading dataset: {dataset_name}")
    
    try:
        # Load from HuggingFace
        dataset = load_dataset(dataset_name, split=split)
        
        # Convert to pandas
        df = pd.DataFrame(dataset)
        
        logger.info(f"✓ Loaded {len(df)} rows")
        logger.info(f"Columns: {df.columns.tolist()}")
        
        return df
    
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise


def convert_qa_to_medical_format(df: pd.DataFrame, 
                                  question_col: str = 'question',
                                  answer_col: str = 'answer',
                                  context_col: str = None):
    """
    Convert Q&A dataset to medical document format
    
    Args:
        df: Input DataFrame
        question_col: Column name for questions
        answer_col: Column name for answers
        context_col: Optional context column
    
    Returns:
        DataFrame in medical format
    """
    logger.info("Converting to medical format...")
    
    medical_data = []
    
    for idx, row in df.iterrows():
        question = str(row.get(question_col, ''))
        answer = str(row.get(answer_col, ''))
        context = str(row.get(context_col, '')) if context_col else ''
        
        # Extract disease name from question (simple heuristic)
        disease_name = question.replace('?', '').strip()
        if len(disease_name) > 100:
            disease_name = disease_name[:100] + '...'
        
        # Create medical document
        medical_doc = {
            'disease_name': disease_name,
            'description': answer,
            'symptoms': '',  # Extract if available
            'causes': '',
            'treatment': answer if 'điều trị' in answer.lower() or 'chữa' in answer.lower() else '',
            'prevention': answer if 'phòng' in answer.lower() or 'tránh' in answer.lower() else '',
            'source': 'HuggingFace Q&A',
            'original_question': question,
            'original_answer': answer,
            'context': context
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
        doc_text = f"{row['disease_name']}. {row['description']}"
        documents.append(doc_text)
        
        # Create metadata
        metadata = {
            'disease_name': str(row['disease_name']),
            'description': str(row['description'])[:1000],  # Limit length
            'symptoms': str(row.get('symptoms', '')),
            'causes': str(row.get('causes', '')),
            'treatment': str(row.get('treatment', ''))[:1000],
            'prevention': str(row.get('prevention', ''))[:1000],
            'source': str(row.get('source', 'Unknown')),
            'original_question': str(row.get('original_question', ''))[:500],
            'original_answer': str(row.get('original_answer', ''))[:1000]
        }
        metadatas.append(metadata)
        
        # Create ID
        ids.append(f"hf_qa_{current_count + idx + 1}")
    
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
    logger.info(f"✓ Indexed {new_count - current_count} new documents")
    logger.info(f"Total collection size: {new_count}")
    
    return new_count


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
    parser = argparse.ArgumentParser(description='Load HuggingFace medical Q&A dataset')
    parser.add_argument('--dataset', type=str, required=True, 
                       help='HuggingFace dataset name (e.g., username/medical-qa)')
    parser.add_argument('--split', type=str, default='train',
                       help='Dataset split (train/test/validation)')
    parser.add_argument('--question-col', type=str, default='question',
                       help='Question column name')
    parser.add_argument('--answer-col', type=str, default='answer',
                       help='Answer column name')
    parser.add_argument('--context-col', type=str, default=None,
                       help='Optional context column name')
    parser.add_argument('--save-csv', type=str, default='data/hf_medical_data.csv',
                       help='Save processed data to CSV')
    
    args = parser.parse_args()
    
    try:
        # Step 1: Load dataset
        df = load_hf_dataset(args.dataset, args.split)
        
        # Step 2: Convert to medical format
        medical_df = convert_qa_to_medical_format(
            df,
            question_col=args.question_col,
            answer_col=args.answer_col,
            context_col=args.context_col
        )
        
        # Step 3: Save to CSV (optional)
        if args.save_csv:
            medical_df.to_csv(args.save_csv, index=False, encoding='utf-8-sig')
            logger.info(f"✓ Saved to {args.save_csv}")
        
        # Step 4: Index to ChromaDB
        new_count = index_to_chromadb(medical_df)
        
        # Step 5: Rebuild BM25 index
        rebuild_bm25_index()
        
        # Summary
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print(f"Dataset: {args.dataset}")
        print(f"Loaded: {len(df)} Q&A pairs")
        print(f"Indexed: {new_count} total documents in ChromaDB")
        print(f"BM25 index: Rebuilt")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
