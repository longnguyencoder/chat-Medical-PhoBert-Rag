"""
Add cached chat endpoint to medical_chatbot_controller

This file contains a new endpoint that demonstrates caching functionality.
Add this code to the end of medical_chatbot_controller.py
"""

# ============================================================================
# CACHED CHAT ENDPOINT (DEMO)
# ============================================================================

from src.services.cached_chatbot_service import (
    cached_search,
    cached_response,
    get_cache_stats,
    clear_cache
)

# Cache stats model
cache_stats_model = medical_chatbot_ns.model('CacheStats', {
    'size': fields.Integer(description='Current cache size'),
    'max_size': fields.Integer(description='Maximum cache size'),
    'hits': fields.Integer(description='Cache hits'),
    'misses': fields.Integer(description='Cache misses'),
    'hit_rate': fields.Float(description='Cache hit rate percentage'),
    'total_requests': fields.Integer(description='Total requests')
})

@medical_chatbot_ns.route('/chat-cached')
class CachedMedicalChat(Resource):
    @medical_chatbot_ns.expect(chat_request)
    @medical_chatbot_ns.response(200, 'Success', chat_response)
    @medical_chatbot_ns.response(400, 'Bad Request')
    @medical_chatbot_ns.doc('cached_chat_with_medical_bot')
    def post(self):
        """
        Chat with caching enabled (DEMO)
        
        This endpoint demonstrates the caching layer:
        - First request: Normal speed (3-5s)
        - Subsequent identical requests: Fast (< 0.5s)
        
        Note: Caching is disabled for conversation-specific queries
        """
        try:
            data = request.json
            
            if not data:
                return {'message': 'Request body is required'}, 400
            
            question = data.get('question', '').strip()
            
            if not question:
                return {'message': 'Question is required'}, 400
            
            logger.info(f"Processing cached question: {question[:100]}...")
            
            # 1. Extract intent
            extraction_result = extract_user_intent_and_features(question)
            extracted_features = extraction_result.get('extracted_features', {})
            
            # 2. CACHED Search
            search_result = cached_search(
                combined_search_with_filters,
                question,
                extracted_features
            )
            search_results = search_result.get('results', [])
            search_from_cache = search_result.get('from_cache', False)
            
            # 3. CACHED Response Generation
            response = cached_response(
                generate_natural_response,
                question,
                search_results,
                extracted_features,
                conversation_id=None,  # No conversation for demo
                user_name=None
            )
            response_from_cache = response.get('from_cache', False)
            
            # Build response with cache info
            result = {
                'question': question,
                'answer': response.get('answer'),
                'confidence': response.get('confidence', 'unknown'),
                'cache_info': {
                    'search_cached': search_from_cache,
                    'response_cached': response_from_cache,
                    'fully_cached': search_from_cache and response_from_cache
                },
                'search_summary': {
                    'total_found': len(search_results),
                    'query_expansion_used': search_result.get('query_expansion_used'),
                    'hybrid_search_used': search_result.get('hybrid_search_used'),
                    'reranking_used': search_result.get('reranking_used')
                },
                'sources': [
                    {
                        'disease_name': src['metadata'].get('disease_name'),
                        'relevance_score': src.get('relevance_score')
                    }
                    for src in search_results[:3]
                ]
            }
            
            return result, 200
            
        except Exception as e:
            logger.error(f"Error in cached chat: {str(e)}", exc_info=True)
            return {'message': f'Internal server error: {str(e)}'}, 500


@medical_chatbot_ns.route('/cache/stats')
class CacheStats(Resource):
    @medical_chatbot_ns.response(200, 'Success', cache_stats_model)
    @medical_chatbot_ns.doc('get_cache_statistics')
    def get(self):
        """Get cache statistics"""
        try:
            stats = get_cache_stats()
            return stats, 200
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {'message': f'Error: {str(e)}'}, 500


@medical_chatbot_ns.route('/cache/clear')
class CacheClear(Resource):
    @medical_chatbot_ns.response(200, 'Success')
    @medical_chatbot_ns.doc('clear_cache')
    def post(self):
        """Clear all cache entries"""
        try:
            clear_cache()
            return {'message': 'Cache cleared successfully'}, 200
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return {'message': f'Error: {str(e)}'}, 500
