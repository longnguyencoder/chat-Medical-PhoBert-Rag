from flask import request
from flask_restx import Namespace, Resource, fields
import logging
from datetime import datetime
from src.services.medical_chatbot_service import (
    extract_user_intent_and_features,
    combined_search_with_filters,
    generate_natural_response,
    get_or_create_collection
)
from src.models.base import db
from src.models.message import Message
from src.models.conversation import Conversation
from src.models.user import User

# Configure logging
logger = logging.getLogger(__name__)

medical_chatbot_ns = Namespace('medical-chatbot', description='Medical Chatbot operations using PhoBERT RAG')

# API Models
chat_request = medical_chatbot_ns.model('MedicalChatRequest', {
    'question': fields.String(required=True, description='User medical question in Vietnamese', example='Triệu chứng của cảm cúm là gì?'),
    'user_id': fields.Integer(description='User ID for chat history', example=1),
    'conversation_id': fields.Integer(description='Conversation ID to continue chat', example=1)
})

chat_response = medical_chatbot_ns.model('MedicalChatResponse', {
    'question': fields.String(description='Original question'),
    'answer': fields.String(description='Generated answer'),
    'confidence': fields.String(description='Confidence level: high, medium, low, or none'),
    'conversation_id': fields.Integer(description='ID of the conversation'),
    'extraction': fields.Raw(description='Extracted medical features'),
    'search_results': fields.Raw(description='Relevant search results'),
    'sources': fields.Raw(description='Top sources used for answer')
})

history_item = medical_chatbot_ns.model('HistoryItem', {
    'message_id': fields.Integer,
    'sender': fields.String,
    'message_text': fields.String,
    'sent_at': fields.String
})

history_response = medical_chatbot_ns.model('HistoryResponse', {
    'conversation_id': fields.Integer,
    'messages': fields.List(fields.Nested(history_item))
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
        Saves chat history if user_id is provided.
        """
        try:
            data = request.json
            
            # Validate request
            if not data:
                return {'message': 'Request body is required'}, 400
            
            question = data.get('question', '').strip()
            user_id = data.get('user_id')
            conversation_id = data.get('conversation_id')
            
            if not question:
                return {'message': 'Question is required'}, 400
            
            # Handle Chat History - Start/Continue Conversation
            conversation = None
            if user_id:
                if conversation_id:
                    conversation = Conversation.query.filter_by(conversation_id=conversation_id, user_id=user_id).first()
                
                if not conversation:
                    # Create new conversation
                    conversation = Conversation(
                        user_id=user_id,
                        started_at=datetime.utcnow(),
                        source_language='vi',
                        title=question[:50] + "..."
                    )
                    db.session.add(conversation)
                    db.session.commit()
                    conversation_id = conversation.conversation_id
                
                # Save User Message
                user_msg = Message(
                    conversation_id=conversation.conversation_id,
                    sender='user',
                    message_text=question,
                    message_type='text',
                    sent_at=datetime.utcnow()
                )
                db.session.add(user_msg)
                db.session.commit()

            logger.info(f"Processing question: {question[:100]}...")
            
            # 1. Extract intent
            extraction_result = extract_user_intent_and_features(question)
            extracted_features = extraction_result.get('extracted_features', {})
            
            # 2. Search
            search_result = combined_search_with_filters(question, extracted_features)
            search_results = search_result.get('results', [])
            
            # 3. Generate response with conversation context
            response = generate_natural_response(
                question, 
                search_results, 
                extracted_features,
                conversation_id=conversation.conversation_id if conversation else None
            )
            answer = response.get('answer')
            
            # Save Bot Response
            if conversation:
                bot_msg = Message(
                    conversation_id=conversation.conversation_id,
                    sender='bot',
                    message_text=answer,
                    message_type='text',
                    sent_at=datetime.utcnow()
                )
                db.session.add(bot_msg)
                db.session.commit()
                
                # Auto-generate summary every 5 messages
                message_count = Message.query.filter_by(
                    conversation_id=conversation.conversation_id
                ).count()
                
                if message_count >= 5 and message_count % 5 == 0:
                    from src.services.medical_chatbot_service import generate_conversation_summary
                    summary = generate_conversation_summary(conversation.conversation_id)
                    if summary:
                        conversation.summary = summary
                        db.session.commit()
                        logger.info(f"✓ Updated conversation summary (total messages: {message_count})")
            
            
            # Build response
            result = {
                'question': question,
                'answer': answer,
                'confidence': response.get('confidence', 'unknown'),
                'conversation_id': conversation_id,
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
            
            return result, 200
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            db.session.rollback()
            return {
                'message': 'Internal server error',
                'error': str(e)
            }, 500

@medical_chatbot_ns.route('/history/<int:conversation_id>')
class ChatHistory(Resource):
    @medical_chatbot_ns.response(200, 'Success', history_response)
    @medical_chatbot_ns.response(403, 'Forbidden - Not your conversation')
    @medical_chatbot_ns.response(404, 'Conversation not found')
    @medical_chatbot_ns.doc('get_chat_history', params={'user_id': 'User ID to verify ownership'})
    def get(self, conversation_id):
        """Get chat history for a specific conversation (requires user_id for security)"""
        try:
            # Get user_id from query parameter
            user_id = request.args.get('user_id', type=int)
            
            if not user_id:
                return {'message': 'user_id is required'}, 400
            
            conversation = Conversation.query.get(conversation_id)
            if not conversation:
                return {'message': 'Conversation not found'}, 404
            
            # Security check: Verify the conversation belongs to this user
            if conversation.user_id != user_id:
                return {'message': 'You do not have permission to view this conversation'}, 403
                
            messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.sent_at).all()
            
            return {
                'conversation_id': conversation_id,
                'user_id': conversation.user_id,
                'title': conversation.title,
                'started_at': conversation.started_at.isoformat() if conversation.started_at else None,
                'messages': [
                    {
                        'message_id': msg.message_id,
                        'sender': msg.sender,
                        'message_text': msg.message_text,
                        'sent_at': msg.sent_at.isoformat() if msg.sent_at else None
                    }
                    for msg in messages
                ]
            }, 200
        except Exception as e:
            logger.error(f"Error retrieving history: {str(e)}")
            return {'message': 'Internal server error'}, 500

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

