"""
BM25 Search Module for Medical Chatbot

This module provides keyword-based search using BM25 algorithm
to complement the vector-based semantic search.
"""

import logging
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import re

logger = logging.getLogger(__name__)


class BM25SearchEngine:
    """BM25-based keyword search engine for medical documents"""
    
    def __init__(self):
        self.bm25 = None
        self.documents = []
        self.document_ids = []
        self.metadatas = []
        
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize Vietnamese text for BM25.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            List of tokens (words)
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep Vietnamese characters
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Split into words
        words = text.split()
        
        # Remove stop words
        stop_words = {
            'là', 'của', 'và', 'có', 'được', 'này', 'đó', 'các', 'cho', 
            'từ', 'với', 'một', 'những', 'trong', 'để', 'khi', 'bị', 'bởi',
            'về', 'theo', 'như', 'đã', 'sẽ', 'thì', 'hoặc', 'nhưng', 'mà'
        }
        
        # Filter stop words and short words
        tokens = [w for w in words if w not in stop_words and len(w) > 1]
        
        return tokens
    
    def index_documents(self, documents: List[str], document_ids: List[str], 
                       metadatas: List[Dict]) -> None:
        """
        Index documents for BM25 search.
        
        Args:
            documents: List of document texts
            document_ids: List of document IDs
            metadatas: List of document metadata
        """
        logger.info(f"Indexing {len(documents)} documents for BM25 search...")
        
        self.documents = documents
        self.document_ids = document_ids
        self.metadatas = metadatas
        
        # Tokenize all documents
        tokenized_docs = [self.tokenize(doc) for doc in documents]
        
        # Create BM25 index
        self.bm25 = BM25Okapi(tokenized_docs)
        
        logger.info(f"✓ BM25 index created with {len(documents)} documents")
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search documents using BM25.
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of search results with scores
        """
        if self.bm25 is None:
            logger.warning("BM25 index not initialized")
            return []
        
        # Tokenize query
        tokenized_query = self.tokenize(query)
        
        if not tokenized_query:
            logger.warning(f"Query tokenization resulted in empty tokens: {query}")
            return []
        
        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top k results
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include results with positive scores
                results.append({
                    'id': self.document_ids[idx],
                    'document': self.documents[idx],
                    'metadata': self.metadatas[idx],
                    'bm25_score': float(scores[idx]),
                    'rank': len(results) + 1
                })
        
        logger.info(f"BM25 search found {len(results)} results for query: '{query}'")
        if results:
            logger.info(f"Top BM25 score: {results[0]['bm25_score']:.3f}")
        
        return results
    
    def is_ready(self) -> bool:
        """Check if BM25 index is ready"""
        return self.bm25 is not None and len(self.documents) > 0


def create_searchable_text(metadata: Dict) -> str:
    """
    Create searchable text from metadata for BM25 indexing.
    
    Args:
        metadata: Document metadata
        
    Returns:
        Combined searchable text
    """
    parts = [
        str(metadata.get('disease_name', '')),
        str(metadata.get('symptoms', '')),
        str(metadata.get('treatment', '')),
        str(metadata.get('prevention', '')),
        str(metadata.get('description', '')),
        str(metadata.get('question', '')),
        str(metadata.get('answer', ''))
    ]
    
    return ' '.join(parts)
