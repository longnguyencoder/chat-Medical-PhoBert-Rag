from flask import request
from flask_restx import Namespace, Resource, fields
import logging
from src.services.medical_chatbot_service import (
    extract_user_intent_and_features,
    combined_search_with_filters,
    generate_natural_response,
    get_or_create_collection
)

# Configure logging
logger = logging.getLogger(__name__)

medical_chatbot_ns = Namespace('medical-chatbot', description='Medical Chatbot operations using PhoBERT RAG')

# API Models
chat_request = medical_chatbot_ns.model('MedicalChatRequest', {
    'question': fields.String(required=True, description='User medical question in Vietnamese', example='Triệu chứng của cảm cúm là gì?')
})

chat_response = medical_chatbot_ns.model('MedicalChatResponse', {
    'question': fields.String(description='Original question'),
    'answer': fields.String(description='Generated answer'),
    'confidence': fields.String(description='Confidence level: high, medium, low, or none'),
    'extraction': fields.Raw(description='Extracted medical features'),
    'search_results': fields.Raw(description='Relevant search results'),
    'sources': fields.Raw(description='Top sources used for answer')
})

@medical_chatbot_ns.route('/chat')
class MedicalChat(Resource):
    @medical_chatbot_ns.expect(chat_request)
    @medical_chatbot_ns.response(200, 'Success', chat_response)
    @medical_chatbot_ns.response(400, 'Bad Request')
    @medical_chatbot_ns.response(500, 'Internal Server Error')
    @medical_chatbot_ns.doc('chat_with_medical_bot')
    def post(self):
        """
        Chat with the medical assistant powered by PhoBERT RAG.
        
        This endpoint uses:
        - PhoBERT for Vietnamese text embeddings
        - ChromaDB for vector storage
        - GPT-3.5 for natural language generation
        - Hybrid search (semantic + keyword matching)
        """
        try:
            data = request.json
            
            # Validate request
            if not data:
                logger.warning("Empty request received")
                return {'message': 'Request body is required'}, 400
            
            question = data.get('question', '').strip()
            
            if not question:
                logger.warning("Empty question received")
                return {'message': 'Question is required and cannot be empty'}, 400
            
            if len(question) < 5:
                logger.warning(f"Question too short: {question}")
                return {'message': 'Question is too short. Please provide more details.'}, 400
            
            if len(question) > 500:
                logger.warning(f"Question too long: {len(question)} characters")
                return {'message': 'Question is too long. Please keep it under 500 characters.'}, 400
            
            logger.info(f"Processing question: {question[:100]}...")
            
            # 1. Extract intent and features
            logger.info("Step 1: Extracting medical features")
            extraction_result = extract_user_intent_and_features(question)
            extracted_features = extraction_result.get('extracted_features', {})
            
            # 2. Search for medical info
            logger.info("Step 2: Searching medical knowledge base")
            search_result = combined_search_with_filters(question, extracted_features)
            
            if not search_result.get('success'):
                logger.error(f"Search failed: {search_result.get('message')}")
                return {
                    'message': 'Failed to search medical database',
                    'error': search_result.get('message')
                }, 500
            
            search_results = search_result.get('results', [])
            logger.info(f"Found {len(search_results)} relevant results")
            
            # 3. Generate response
            logger.info("Step 3: Generating natural language response")
            response = generate_natural_response(question, search_results, extracted_features)
            
            # Build response
            result = {
                'question': question,
                'answer': response.get('answer'),
                'confidence': response.get('confidence', 'unknown'),
                'avg_relevance_score': response.get('avg_relevance_score'),
                'extraction': {
                    'intent': extraction_result.get('intent'),
                    'features': extracted_features
                },
                'search_summary': {
                    'total_found': len(search_results),
                    'total_searched': search_result.get('total_searched', 0)
                },
                'sources': [
                    {
                        'disease_name': src['metadata'].get('disease_name'),
                        'relevance_score': src.get('relevance_score'),
                        'confidence': src.get('confidence')
                    }
                    for src in response.get('sources', [])
                ]
            }
            
            logger.info(f"Response generated successfully (confidence: {result['confidence']})")
            return result, 200
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return {
                'message': 'Internal server error',
                'error': str(e)
            }, 500

@medical_chatbot_ns.route('/health')
class HealthCheck(Resource):
    @medical_chatbot_ns.doc('health_check')
    def get(self):
        """Check if the medical chatbot service is healthy"""
        try:
            # Check ChromaDB connection
            collection = get_or_create_collection()
            count = collection.count()
            
            return {
                'status': 'healthy',
                'service': 'Medical Chatbot with PhoBERT RAG',
                'database': {
                    'connected': True,
                    'records': count
                },
                'models': {
                    'embedding': 'PhoBERT (vinai/phobert-base)',
                    'generation': 'GPT-3.5-turbo'
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }, 500

