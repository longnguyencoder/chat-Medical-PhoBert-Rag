"""
Cached wrapper for medical chatbot service

This module provides cached versions of search and response generation
to reduce latency and API costs.
"""

import logging
from typing import Dict, List, Optional, Any
from src.services.cache_manager import get_cache_manager, generate_cache_key
from src.config.config import Config

logger = logging.getLogger(__name__)

# Initialize cache manager
cache = get_cache_manager(max_size=Config.CACHE_MAX_SIZE)
CACHE_ENABLED = Config.CACHE_ENABLED

logger.info(f"Cache initialized: enabled={CACHE_ENABLED}, max_size={Config.CACHE_MAX_SIZE}")


def cached_search(search_func, question: str, extracted_features: Dict[str, Any], n_results: int = 10) -> Dict[str, Any]:
    """
    Cached wrapper for search function
    
    Args:
        search_func: The actual search function to call
        question: User's question
        extracted_features: Extracted medical features
        n_results: Number of results to return
        
    Returns:
        Search results (from cache or fresh search)
    """
    if not CACHE_ENABLED:
        return search_func(question, extracted_features, n_results)
    
    # Generate cache key
    cache_key = generate_cache_key('search', question, n_results=n_results)
    
    # Try to get from cache
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.info(f"✓ Cache HIT for search: {question[:50]}...")
        cached_result['from_cache'] = True
        return cached_result
    
    # Cache miss - perform actual search
    logger.info(f"✗ Cache MISS for search: {question[:50]}...")
    result = search_func(question, extracted_features, n_results)
    
    # Cache the result
    if result.get('success'):
        cache.set(cache_key, result, ttl=Config.CACHE_TTL_SEARCH)
        logger.debug(f"Cached search result: {cache_key}")
    
    result['from_cache'] = False
    return result


def cached_response(
    response_func,
    question: str,
    search_results: List[Dict],
    extracted_features: Dict[str, Any],
    conversation_id: Optional[int] = None,
    user_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cached wrapper for response generation
    
    Args:
        response_func: The actual response generation function
        question: User's question
        search_results: Search results from RAG
        extracted_features: Extracted medical features
        conversation_id: Optional conversation ID
        user_name: Optional user name
        
    Returns:
        Generated response (from cache or fresh generation)
    """
    if not CACHE_ENABLED:
        return response_func(question, search_results, extracted_features, conversation_id, user_name)
    
    # Don't cache if conversation_id is provided (personalized responses)
    if conversation_id is not None:
        logger.debug(f"Skipping cache for conversation-specific response")
        result = response_func(question, search_results, extracted_features, conversation_id, user_name)
        result['from_cache'] = False
        return result
    
    # Generate cache key (without conversation context)
    cache_key = generate_cache_key('response', question)
    
    # Try to get from cache
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.info(f"✓ Cache HIT for response: {question[:50]}...")
        cached_result['from_cache'] = True
        return cached_result
    
    # Cache miss - generate response
    logger.info(f"✗ Cache MISS for response: {question[:50]}...")
    result = response_func(question, search_results, extracted_features, conversation_id, user_name)
    
    # Cache the result
    if result.get('answer'):
        cache.set(cache_key, result, ttl=Config.CACHE_TTL_RESPONSE)
        logger.debug(f"Cached response: {cache_key}")
    
    result['from_cache'] = False
    return result


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics
    
    Returns:
        Dictionary with cache statistics
    """
    return cache.get_stats()


def clear_cache() -> None:
    """Clear all cache entries"""
    cache.clear()
    logger.info("Cache cleared by user request")


def reset_cache_stats() -> None:
    """Reset cache statistics"""
    cache.reset_stats()
    logger.info("Cache statistics reset")
