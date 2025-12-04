"""
Deduplication tool for medical documents

This script:
1. Detects duplicate/similar documents in ChromaDB
2. Removes or merges duplicates
3. Keeps the best version of each document
"""

import numpy as np
from typing import List, Dict, Tuple
from src.services.medical_chatbot_service import get_or_create_collection
from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_similarity(text1: str, text2: str, phobert_ef) -> float:
    """
    Calculate cosine similarity between two texts
    
    Returns:
        Similarity score (0-1, higher = more similar)
    """
    emb1 = phobert_ef([text1])[0]
    emb2 = phobert_ef([text2])[0]
    
    # Cosine similarity
    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    
    return float(similarity)


def find_duplicates(
    similarity_threshold: float = 0.95,
    batch_size: int = 100
) -> List[Tuple[str, str, float]]:
    """
    Find duplicate documents in ChromaDB
    
    Args:
        similarity_threshold: Documents with similarity > this are considered duplicates
        batch_size: Process in batches to avoid memory issues
    
    Returns:
        List of (id1, id2, similarity) tuples
    """
    logger.info("Finding duplicates...")
    
    collection = get_or_create_collection()
    phobert_ef = PhoBERTEmbeddingFunction()
    
    # Get all documents
    all_docs = collection.get(include=["documents", "metadatas"])
    total_docs = len(all_docs['ids'])
    
    logger.info(f"Checking {total_docs} documents for duplicates...")
    
    duplicates = []
    
    # Compare each document with others
    for i in range(total_docs):
        if i % 100 == 0:
            logger.info(f"Progress: {i}/{total_docs}")
        
        doc1_id = all_docs['ids'][i]
        doc1_text = all_docs['documents'][i]
        
        # Only compare with documents after this one (avoid double-checking)
        for j in range(i + 1, total_docs):
            doc2_id = all_docs['ids'][j]
            doc2_text = all_docs['documents'][j]
            
            # Quick check: if texts are identical
            if doc1_text == doc2_text:
                duplicates.append((doc1_id, doc2_id, 1.0))
                continue
            
            # Calculate similarity
            similarity = calculate_similarity(doc1_text, doc2_text, phobert_ef)
            
            if similarity >= similarity_threshold:
                duplicates.append((doc1_id, doc2_id, similarity))
    
    logger.info(f"Found {len(duplicates)} duplicate pairs")
    
    return duplicates


def choose_best_document(doc1: Dict, doc2: Dict) -> str:
    """
    Choose which document to keep when there are duplicates
    
    Criteria:
    1. Longer original_answer is better
    2. Has source link is better
    3. More complete metadata is better
    
    Returns:
        ID of the document to keep
    """
    meta1 = doc1['metadata']
    meta2 = doc2['metadata']
    
    # Score each document
    score1 = 0
    score2 = 0
    
    # Criterion 1: Length of original_answer
    answer1_len = len(meta1.get('original_answer', ''))
    answer2_len = len(meta2.get('original_answer', ''))
    
    if answer1_len > answer2_len:
        score1 += 3
    elif answer2_len > answer1_len:
        score2 += 3
    
    # Criterion 2: Has source link
    source1 = meta1.get('source', '')
    source2 = meta2.get('source', '')
    
    if source1 and source1.startswith('http'):
        score1 += 2
    if source2 and source2.startswith('http'):
        score2 += 2
    
    # Criterion 3: Completeness of metadata
    fields = ['symptoms', 'treatment', 'prevention', 'causes']
    for field in fields:
        if meta1.get(field) and len(meta1.get(field, '')) > 50:
            score1 += 1
        if meta2.get(field) and len(meta2.get(field, '')) > 50:
            score2 += 1
    
    # Return ID of document with higher score
    if score1 >= score2:
        return doc1['id']
    else:
        return doc2['id']


def remove_duplicates(
    duplicates: List[Tuple[str, str, float]],
    dry_run: bool = True
) -> int:
    """
    Remove duplicate documents from ChromaDB
    
    Args:
        duplicates: List of (id1, id2, similarity) tuples
        dry_run: If True, only show what would be deleted (don't actually delete)
    
    Returns:
        Number of documents removed
    """
    if not duplicates:
        logger.info("No duplicates to remove")
        return 0
    
    collection = get_or_create_collection()
    
    # Build set of IDs to delete
    to_delete = set()
    
    for id1, id2, similarity in duplicates:
        # Get both documents
        doc1_data = collection.get(ids=[id1], include=["metadatas"])
        doc2_data = collection.get(ids=[id2], include=["metadatas"])
        
        if not doc1_data['ids'] or not doc2_data['ids']:
            continue
        
        doc1 = {'id': id1, 'metadata': doc1_data['metadatas'][0]}
        doc2 = {'id': id2, 'metadata': doc2_data['metadatas'][0]}
        
        # Choose which to keep
        keep_id = choose_best_document(doc1, doc2)
        delete_id = id2 if keep_id == id1 else id1
        
        to_delete.add(delete_id)
        
        logger.info(f"Duplicate pair (similarity: {similarity:.3f}):")
        logger.info(f"  Keep: {keep_id}")
        logger.info(f"  Delete: {delete_id}")
    
    if dry_run:
        logger.info(f"\n[DRY RUN] Would delete {len(to_delete)} documents")
        logger.info("Run with dry_run=False to actually delete")
        return 0
    
    # Actually delete
    if to_delete:
        collection.delete(ids=list(to_delete))
        logger.info(f"✓ Deleted {len(to_delete)} duplicate documents")
    
    return len(to_delete)


def deduplicate_database(
    similarity_threshold: float = 0.95,
    dry_run: bool = True
):
    """
    Main function to deduplicate the entire database
    
    Args:
        similarity_threshold: Documents with similarity > this are considered duplicates
        dry_run: If True, only show what would be deleted
    """
    print("="*80)
    print("DEDUPLICATION TOOL")
    print("="*80)
    
    # Step 1: Find duplicates
    duplicates = find_duplicates(similarity_threshold)
    
    if not duplicates:
        print("\n✓ No duplicates found!")
        return
    
    # Step 2: Show summary
    print(f"\nFound {len(duplicates)} duplicate pairs")
    print(f"Similarity threshold: {similarity_threshold}")
    
    # Step 3: Remove duplicates
    removed = remove_duplicates(duplicates, dry_run=dry_run)
    
    # Step 4: Summary
    print("\n" + "="*80)
    if dry_run:
        print(f"[DRY RUN] Would remove {len(duplicates)} duplicate documents")
        print("Run with dry_run=False to actually remove")
    else:
        print(f"✓ Removed {removed} duplicate documents")
        
        # Rebuild BM25 index
        from src.services.medical_chatbot_service import initialize_bm25_index
        print("\nRebuilding BM25 index...")
        initialize_bm25_index()
        print("✓ BM25 index rebuilt")
    
    print("="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Deduplicate medical documents')
    parser.add_argument('--threshold', type=float, default=0.95,
                       help='Similarity threshold (0-1, default: 0.95)')
    parser.add_argument('--execute', action='store_true',
                       help='Actually remove duplicates (default: dry run)')
    
    args = parser.parse_args()
    
    deduplicate_database(
        similarity_threshold=args.threshold,
        dry_run=not args.execute
    )
