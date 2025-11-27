import pandas as pd
import chromadb
import os
import sys
import logging
from typing import Dict, List


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the src directory to the python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(src_dir)


from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction

def validate_medical_data(df: pd.DataFrame) -> bool:
    """Validate medical data structure and content"""
    required_columns = ['id', 'disease_name', 'symptoms', 'treatment', 'prevention', 'description']
    
    # Check required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    # Check for empty values
    for col in required_columns:
        empty_count = df[col].isna().sum()
        if empty_count > 0:
            logger.warning(f"Column '{col}' has {empty_count} empty values")
    
    # Check for duplicates
    duplicate_count = df['id'].duplicated().sum()
    if duplicate_count > 0:
        logger.warning(f"Found {duplicate_count} duplicate IDs")
    
    logger.info(f"Data validation completed. Total records: {len(df)}")
    return True

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if pd.isna(text):
        return ""
    
    # Convert to string and strip whitespace
    text = str(text).strip()
    
    # Remove multiple spaces
    text = ' '.join(text.split())
    
    return text

def create_optimized_document(row: pd.Series) -> str:
    """Create document text optimized for PhoBERT embedding"""
    # Clean all fields
    disease_name = clean_text(row['disease_name'])
    symptoms = clean_text(row['symptoms'])
    treatment = clean_text(row['treatment'])
    prevention = clean_text(row['prevention'])
    description = clean_text(row['description'])
    
    # Create structured document with clear sections
    # PhoBERT works better with natural Vietnamese text structure
    document = f"""Tên bệnh: {disease_name}

Triệu chứng: {symptoms}

Cách điều trị: {treatment}

Phòng ngừa: {prevention}

Mô tả chi tiết: {description}"""
    
    return document

def process_medical_data():
    """Process medical data and Q&A, store in ChromaDB with PhoBERT embeddings"""
    try:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Path to medical_data.csv
        disease_csv_path = os.path.join(workspace_root, 'src', 'scape', 'medical_data.csv')
        qa_csv_path = os.path.join(workspace_root, 'src', 'scape', 'medical_qa.csv')
        
        # Read disease data
        logger.info(f"Loading disease data from: {disease_csv_path}")
        if not os.path.exists(disease_csv_path):
            raise FileNotFoundError(f"Medical data file not found at: {disease_csv_path}")
        
        df_disease = pd.read_csv(disease_csv_path, encoding='utf-8')
        logger.info(f"Loaded {len(df_disease)} disease records")
        
        # Validate disease data
        if not validate_medical_data(df_disease):
            raise ValueError("Disease data validation failed")
        
        # Clean disease data
        logger.info("Cleaning disease data...")
        for col in ['disease_name', 'symptoms', 'treatment', 'prevention', 'description']:
            df_disease[col] = df_disease[col].apply(clean_text)
        
        # Create documents for diseases
        logger.info("Creating disease documents...")
        df_disease['document'] = df_disease.apply(create_optimized_document, axis=1)
        df_disease['doc_type'] = 'disease'
        
        # Read Q&A data (if exists)
        all_documents = []
        all_ids = []
        all_metadatas = []
        
        # Add disease documents
        for _, row in df_disease.iterrows():
            all_documents.append(row['document'])
            all_ids.append(f"disease_{row['id']}")
            all_metadatas.append({
                'id': str(row['id']),
                'disease_name': str(row['disease_name']),
                'symptoms': str(row['symptoms']),
                'treatment': str(row['treatment']),
                'prevention': str(row['prevention']),
                'description': str(row['description']),
                'doc_type': 'disease'
            })
        
        # Add Q&A documents if file exists
        if os.path.exists(qa_csv_path):
            logger.info(f"Loading Q&A data from: {qa_csv_path}")
            df_qa = pd.read_csv(qa_csv_path, encoding='utf-8')
            logger.info(f"Loaded {len(df_qa)} Q&A records")
            
            for _, row in df_qa.iterrows():
                question = clean_text(row['question'])
                answer = clean_text(row['answer'])
                disease_name = clean_text(row.get('disease_name', ''))
                
                # Create Q&A document
                qa_doc = f"Câu hỏi: {question}\n\nTrả lời: {answer}"
                
                all_documents.append(qa_doc)
                all_ids.append(f"qa_{row['id']}")
                all_metadatas.append({
                    'id': str(row['id']),
                    'question': question,
                    'answer': answer,
                    'disease_name': disease_name,
                    'category': str(row.get('category', '')),
                    'doc_type': 'qa'
                })
        else:
            logger.info("No Q&A file found, skipping Q&A data")
        
        # Initialize ChromaDB
        chroma_db_path = os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'chroma_db')
        logger.info(f"Initializing ChromaDB at: {chroma_db_path}")
        chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        
        # Initialize PhoBERT
        logger.info("Initializing PhoBERT embedding function...")
        phobert_ef = PhoBERTEmbeddingFunction()
        
        # Delete old collection
        try:
            chroma_client.delete_collection("medical_collection")
            logger.info("Deleted old medical_collection")
        except:
            logger.info("medical_collection does not exist, creating new one")
        
        # Create new collection
        logger.info("Creating new medical_collection...")
        collection = chroma_client.create_collection(
            name="medical_collection",
            embedding_function=phobert_ef,
            metadata={"description": "Medical knowledge base with diseases and Q&A"}
        )
        
        # Add all documents to collection
        logger.info(f"Adding {len(all_documents)} documents to ChromaDB...")
        collection.add(
            ids=all_ids,
            documents=all_documents,
            metadatas=all_metadatas
        )
        
        # Verify
        count = collection.count()
        logger.info(f"✓ Successfully saved {count} records to ChromaDB")
        
        # Print summary
        disease_count = len(df_disease)
        qa_count = len(all_documents) - disease_count
        
        print("\n" + "="*60)
        print("MEDICAL DATA PROCESSING SUMMARY")
        print("="*60)
        print(f"Disease records: {disease_count}")
        print(f"Q&A records: {qa_count}")
        print(f"Total in ChromaDB: {count}")
        print(f"Collection: medical_collection")
        print(f"Embedding: PhoBERT (vinai/phobert-base)")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing medical data: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    process_medical_data()
