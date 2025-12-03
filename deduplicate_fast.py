"""
FAST Deduplication using ChromaDB search

Instead of comparing all pairs (slow), use ChromaDB to find similar documents
"""

from src.services.medical_chatbot_service import get_or_create_collection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_duplicates_fast(similarity_threshold: float = 0.95):
    """
    Fast duplicate detection using ChromaDB search
    
    For each document, search for similar documents.
    Much faster than pairwise comparison!
    """
    logger.info("Finding duplicates (FAST method)...")
    
    collection = get_or_create_collection()
    
    # Get all documents
    all_docs = collection.get(include=["embeddings", "metadatas"])
    total_docs = len(all_docs['ids'])
    
    logger.info(f"Checking {total_docs} documents...")
    
    duplicates = []
    checked = set()
    
    # For each document, search for similar ones
    for i, doc_id in enumerate(all_docs['ids']):
        if i % 100 == 0:
            logger.info(f"Progress: {i}/{total_docs}")
        
        if doc_id in checked:
            continue
        
        # Get embedding
        embedding = all_docs['embeddings'][i]
        
        # Search for similar documents
        results = collection.query(
            query_embeddings=[embedding],
            n_results=10,  # Top 10 similar
            include=["distances"]
        )
        
        # Check results
        for j, (result_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
            if result_id == doc_id:
                continue  # Skip self
            
            # Convert distance to similarity (cosine)
            # ChromaDB uses L2 distance, convert to similarity
            similarity = 1 - (distance / 2)  # Approximate conversion
            
            if similarity >= similarity_threshold:
                # Found duplicate!
                pair = tuple(sorted([doc_id, result_id]))
                if pair not in checked:
                    duplicates.append((doc_id, result_id, similarity))
                    checked.add(pair)
    
    logger.info(f"Found {len(duplicates)} duplicate pairs")
    
    return duplicates


def remove_duplicates_fast(dry_run: bool = True):
    """
    Fast deduplication
    """
    print("="*80)
    print("FAST DEDUPLICATION TOOL")
    print("="*80)
    
    # Find duplicates
    duplicates = find_duplicates_fast(similarity_threshold=0.95)
    
    if not duplicates:
        print("\n✓ No duplicates found!")
        return
    
    print(f"\nFound {len(duplicates)} duplicate pairs")
    
    # Show some examples
    print("\nExamples:")
    for i, (id1, id2, sim) in enumerate(duplicates[:5], 1):
        print(f"{i}. {id1} ↔ {id2} (similarity: {sim:.3f})")
    
    if len(duplicates) > 5:
        print(f"... and {len(duplicates) - 5} more")
    
    if dry_run:
        print(f"\n[DRY RUN] Would remove ~{len(duplicates)} documents")
        print("Run with --execute to actually remove")
    else:
        # Actually remove (use logic from original script)
        from deduplicate_database import remove_duplicates
        removed = remove_duplicates(duplicates, dry_run=False)
        print(f"\n✓ Removed {removed} duplicate documents")
    
    print("="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    
    remove_duplicates_fast(dry_run=not args.execute)
