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
from src.utils.auth_middleware import token_required  # Import decorator JWT

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
            
            # Get user name if available
            user_name = None
            if user_id:
                user = User.query.get(user_id)
                if user and user.full_name:
                    user_name = user.full_name

            # 3. Generate response with conversation context
            response = generate_natural_response(
                question, 
                search_results, 
                extracted_features,
                conversation_id=conversation.conversation_id if conversation else None,
                user_name=user_name
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

# ============================================================================
# API MỚI: CHAT VỚI JWT AUTHENTICATION
# ============================================================================
@medical_chatbot_ns.route('/chat-secure')
class SecureMedicalChat(Resource):
    @medical_chatbot_ns.expect(medical_chatbot_ns.model('SecureChatRequest', {
        'question': fields.String(required=True, description='Câu hỏi y tế'),
        'conversation_id': fields.Integer(description='ID cuộc trò chuyện (tùy chọn)')
    }))
    @medical_chatbot_ns.response(200, 'Success')
    @medical_chatbot_ns.response(401, 'Unauthorized')
    @token_required  # ← Kiểm tra JWT token
    def post(self, current_user):
        """
        Chat BẢO MẬT với JWT - Không cần truyền user_id.
        
        Header: Authorization: Bearer <token>
        Body: {"question": "..."}
        """
        try:
            data = request.json
            question = data.get('question', '').strip()
            conversation_id = data.get('conversation_id')
            
            if not question:
                return {'message': 'Question is required'}, 400
            
            # Lấy user_id từ token (an toàn)
            user_id = current_user['user_id']
            user_name = current_user.get('full_name')
            
            # Xử lý conversation
            conversation = None
            if conversation_id:
                conversation = Conversation.query.filter_by(
                    conversation_id=conversation_id, user_id=user_id
                ).first()
            
            if not conversation:
                conversation = Conversation(
                    user_id=user_id,
                    started_at=datetime.utcnow(),
                    source_language='vi',
                    title=question[:50] + "..."
                )
                db.session.add(conversation)
                db.session.commit()
            
            # Lưu tin nhắn user
            user_msg = Message(
                conversation_id=conversation.conversation_id,
                sender='user',
                message_text=question,
                message_type='text',
                sent_at=datetime.utcnow()
            )
            db.session.add(user_msg)
            db.session.commit()
            
            # RAG pipeline
            extraction_result = extract_user_intent_and_features(question)
            extracted_features = extraction_result.get('extracted_features', {})
            search_result = combined_search_with_filters(question, extracted_features)
            search_results = search_result.get('results', [])
            
            response = generate_natural_response(
                question, search_results, extracted_features,
                conversation_id=conversation.conversation_id,
                user_name=user_name
            )
            answer = response.get('answer')
            
            # Lưu câu trả lời bot
            bot_msg = Message(
                conversation_id=conversation.conversation_id,
                sender='bot',
                message_text=answer,
                message_type='text',
                sent_at=datetime.utcnow()
            )
            db.session.add(bot_msg)
            db.session.commit()
            
            return {
                'question': question,
                'answer': answer,
                'conversation_id': conversation.conversation_id,
                'user_info': {'user_id': user_id, 'name': user_name}
            }, 200
            
        except Exception as e:
            logger.error(f"Error in secure chat: {str(e)}")
            db.session.rollback()
            return {'message': 'Internal server error'}, 500

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


# Models for Conversation Management
conversation_model = medical_chatbot_ns.model('Conversation', {
    'conversation_id': fields.Integer(description='Conversation ID'),
    'title': fields.String(description='Conversation Title'),
    'started_at': fields.String(description='Start time'),
    'summary': fields.String(description='Conversation Summary')
})

conversation_list_response = medical_chatbot_ns.model('ConversationListResponse', {
    'conversations': fields.List(fields.Nested(conversation_model))
})

create_conversation_request = medical_chatbot_ns.model('CreateConversationRequest', {
    'user_id': fields.Integer(required=True, description='User ID'),
    'title': fields.String(description='Optional initial title')
})

@medical_chatbot_ns.route('/conversations')
class ConversationList(Resource):
    @medical_chatbot_ns.expect(create_conversation_request)
    @medical_chatbot_ns.response(201, 'Created', conversation_model)
    @medical_chatbot_ns.doc('create_conversation')
    def post(self):
        """Create a new conversation"""
        try:
            data = request.json
            user_id = data.get('user_id')
            title = data.get('title', 'New Conversation')
            
            if not user_id:
                return {'message': 'user_id is required'}, 400
                
            conversation = Conversation(
                user_id=user_id,
                started_at=datetime.utcnow(),
                source_language='vi',
                title=title
            )
            db.session.add(conversation)
            db.session.commit()
            
            return {
                'conversation_id': conversation.conversation_id,
                'title': conversation.title,
                'started_at': conversation.started_at.isoformat(),
                'summary': conversation.summary
            }, 201
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            db.session.rollback()
            return {'message': 'Internal server error'}, 500

    @medical_chatbot_ns.doc('list_conversations', params={'user_id': 'User ID'})
    @medical_chatbot_ns.response(200, 'Success', conversation_list_response)
    def get(self):
        """Get list of conversations for a user"""
        try:
            user_id = request.args.get('user_id', type=int)
            if not user_id:
                return {'message': 'user_id is required'}, 400
                
            conversations = Conversation.query.filter_by(user_id=user_id)\
                .order_by(Conversation.started_at.desc()).all()
                
            return {
                'conversations': [
                    {
                        'conversation_id': c.conversation_id,
                        'title': c.title,
                        'started_at': c.started_at.isoformat() if c.started_at else None,
                        'summary': c.summary
                    }
                    for c in conversations
                ]
            }, 200
            
        except Exception as e:
            logger.error(f"Error listing conversations: {str(e)}")
            return {'message': 'Internal server error'}, 500

# Update conversation title request model
update_conversation_request = medical_chatbot_ns.model('UpdateConversationRequest', {
    'user_id': fields.Integer(required=True, description='User ID'),
    'title': fields.String(required=True, description='New title')
})

@medical_chatbot_ns.route('/conversations/<int:conversation_id>')
class ConversationDetail(Resource):
    @medical_chatbot_ns.expect(medical_chatbot_ns.model('UpdateConversationJWT', {
        'title': fields.String(required=True, description='New title')
    }))
    @medical_chatbot_ns.response(200, 'Success', conversation_model)
    @medical_chatbot_ns.response(401, 'Unauthorized')
    @medical_chatbot_ns.doc('update_conversation', security='Bearer')
    @token_required
    def put(self, current_user, conversation_id):
        """Update conversation title (JWT Required)"""
        try:
            data = request.json
            user_id = current_user['user_id']  # From JWT token
            new_title = data.get('title')
            
            if not new_title:
                return {'message': 'title is required'}, 400
            
            conversation = Conversation.query.get(conversation_id)
            if not conversation:
                return {'message': 'Conversation not found'}, 404
            
            if conversation.user_id != user_id:
                return {'message': 'Unauthorized'}, 403
            
            conversation.title = new_title
            db.session.commit()
            
            return {
                'conversation_id': conversation.conversation_id,
                'title': conversation.title,
                'started_at': conversation.started_at.isoformat(),
                'summary': conversation.summary
            }, 200
            
        except Exception as e:
            logger.error(f"Error updating conversation: {str(e)}")
            db.session.rollback()
            return {'message': 'Internal server error'}, 500
    
    @medical_chatbot_ns.response(200, 'Deleted')
    @medical_chatbot_ns.response(401, 'Unauthorized')
    @medical_chatbot_ns.doc('delete_conversation', security='Bearer')
    @token_required
    def delete(self, current_user, conversation_id):
        """Delete conversation and all its messages (JWT Required)"""
        try:
            user_id = current_user['user_id']  # From JWT token
            
            conversation = Conversation.query.get(conversation_id)
            if not conversation:
                return {'message': 'Conversation not found'}, 404
            
            if conversation.user_id != user_id:
                return {'message': 'Unauthorized'}, 403
            
            # Delete all messages first
            Message.query.filter_by(conversation_id=conversation_id).delete()
            
            # Delete conversation
            db.session.delete(conversation)
            db.session.commit()
            
            return {'message': 'Conversation deleted successfully'}, 200
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            db.session.rollback()
            return {'message': 'Internal server error'}, 500

@medical_chatbot_ns.route('/conversations/search')
class ConversationSearch(Resource):
    @medical_chatbot_ns.doc('search_conversations', params={
        'user_id': 'User ID',
        'keyword': 'Search keyword'
    })
    @medical_chatbot_ns.response(200, 'Success', conversation_list_response)
    def get(self):
        """Search conversations by keyword in title or messages"""
        try:
            user_id = request.args.get('user_id', type=int)
            keyword = request.args.get('keyword', '').strip()
            
            if not user_id:
                return {'message': 'user_id is required'}, 400
            
            if not keyword:
                return {'message': 'keyword is required'}, 400
            
            # Search in conversation titles
            conversations = Conversation.query.filter(
                Conversation.user_id == user_id,
                Conversation.title.ilike(f'%{keyword}%')
            ).order_by(Conversation.started_at.desc()).all()
            
            # Also search in message content
            message_convs = db.session.query(Conversation).join(Message).filter(
                Conversation.user_id == user_id,
                Message.message_text.ilike(f'%{keyword}%')
            ).distinct().order_by(Conversation.started_at.desc()).all()
            
            # Combine and deduplicate
            all_convs = {c.conversation_id: c for c in conversations + message_convs}
            
            return {
                'conversations': [
                    {
                        'conversation_id': c.conversation_id,
                        'title': c.title,
                        'started_at': c.started_at.isoformat() if c.started_at else None,
                        'summary': c.summary
                    }
                    for c in all_convs.values()
                ]
            }, 200
            
        except Exception as e:
            logger.error(f"Error searching conversations: {str(e)}")
            return {'message': 'Internal server error'}, 500

# Regenerate request model
regenerate_request = medical_chatbot_ns.model('RegenerateRequest', {
    'user_id': fields.Integer(required=True, description='User ID'),
    'conversation_id': fields.Integer(required=True, description='Conversation ID'),
    'message_id': fields.Integer(required=True, description='Bot message ID to regenerate')
})

@medical_chatbot_ns.route('/chat/regenerate')
class RegenerateResponse(Resource):
    @medical_chatbot_ns.expect(medical_chatbot_ns.model('RegenerateJWT', {
        'conversation_id': fields.Integer(required=True, description='Conversation ID'),
        'message_id': fields.Integer(required=True, description='Bot message ID to regenerate')
    }))
    @medical_chatbot_ns.response(200, 'Success', chat_response)
    @medical_chatbot_ns.response(401, 'Unauthorized')
    @medical_chatbot_ns.doc('regenerate_response', security='Bearer')
    @token_required
    def post(self, current_user):
        """Regenerate bot response for a message (JWT Required)"""
        try:
            data = request.json
            user_id = current_user['user_id']  # From JWT token
            conversation_id = data.get('conversation_id')
            message_id = data.get('message_id')
            
            if not all([conversation_id, message_id]):
                return {'message': 'conversation_id and message_id are required'}, 400
            
            # Verify conversation ownership
            conversation = Conversation.query.get(conversation_id)
            if not conversation or conversation.user_id != user_id:
                return {'message': 'Conversation not found or unauthorized'}, 403
            
            # Get the bot message to regenerate
            bot_message = Message.query.get(message_id)
            if not bot_message or bot_message.sender != 'bot':
                return {'message': 'Bot message not found'}, 404
            
            # Find the user question before this bot response
            user_message = Message.query.filter(
                Message.conversation_id == conversation_id,
                Message.sender == 'user',
                Message.sent_at < bot_message.sent_at
            ).order_by(Message.sent_at.desc()).first()
            
            if not user_message:
                return {'message': 'Original question not found'}, 404
            
            question = user_message.message_text
            
            # Extract intent and search
            extraction_result = extract_user_intent_and_features(question)
            extracted_features = extraction_result.get('extracted_features', {})
            
            search_result = combined_search_with_filters(question, extracted_features)
            search_results = search_result.get('results', [])
            
            # Generate new response
            response = generate_natural_response(
                question,
                search_results,
                extracted_features,
                conversation_id=conversation_id
            )
            new_answer = response.get('answer')
            
            # Delete old bot message
            db.session.delete(bot_message)
            
            # Save new bot message
            new_bot_msg = Message(
                conversation_id=conversation_id,
                sender='bot',
                message_text=new_answer,
                message_type='text',
                sent_at=datetime.utcnow()
            )
            db.session.add(new_bot_msg)
            db.session.commit()
            
            return {
                'question': question,
                'answer': new_answer,
                'confidence': response.get('confidence', 'unknown'),
                'conversation_id': conversation_id,
                'message_id': new_bot_msg.message_id,
                'sources': [
                    {
                        'disease_name': src['metadata'].get('disease_name'),
                        'relevance_score': src.get('relevance_score')
                    }
                    for src in response.get('sources', [])
                ]
            }, 200
            
        except Exception as e:
            logger.error(f"Error regenerating response: {str(e)}")
            db.session.rollback()
            return {'message': 'Internal server error'}, 500

@medical_chatbot_ns.route('/conversations/<int:conversation_id>/archive')
class ArchiveConversation(Resource):
    @medical_chatbot_ns.response(200, 'Success')
    @medical_chatbot_ns.response(401, 'Unauthorized')
    @medical_chatbot_ns.doc('archive_conversation', security='Bearer')
    @token_required
    def post(self, current_user, conversation_id):
        """Archive or unarchive a conversation (JWT Required)"""
        try:
            user_id = current_user['user_id']  # From JWT token
            
            conversation = Conversation.query.get(conversation_id)
            if not conversation:
                return {'message': 'Conversation not found'}, 404
            
            if conversation.user_id != user_id:
                return {'message': 'Unauthorized'}, 403
            
            # Toggle archive status
            conversation.is_archived = not conversation.is_archived
            db.session.commit()
            
            status = "archived" if conversation.is_archived else "unarchived"
            return {'message': f'Conversation {status} successfully', 'is_archived': conversation.is_archived}, 200
            
        except Exception as e:
            logger.error(f"Error archiving conversation: {str(e)}")
            db.session.rollback()
            return {'message': 'Internal server error'}, 500

@medical_chatbot_ns.route('/conversations/<int:conversation_id>/pin')
class PinConversation(Resource):
    @medical_chatbot_ns.response(200, 'Success')
    @medical_chatbot_ns.response(401, 'Unauthorized')
    @medical_chatbot_ns.doc('pin_conversation', security='Bearer')
    @token_required
    def post(self, current_user, conversation_id):
        """Pin or unpin a conversation (JWT Required)"""
        try:
            user_id = current_user['user_id']  # From JWT token
            
            conversation = Conversation.query.get(conversation_id)
            if not conversation:
                return {'message': 'Conversation not found'}, 404
            
            if conversation.user_id != user_id:
                return {'message': 'Unauthorized'}, 403
            
            # Toggle pin status
            conversation.is_pinned = not conversation.is_pinned
            db.session.commit()
            
            status = "pinned" if conversation.is_pinned else "unpinned"
            return {'message': f'Conversation {status} successfully', 'is_pinned': conversation.is_pinned}, 200
            
        except Exception as e:
            logger.error(f"Error pinning conversation: {str(e)}")
            db.session.rollback()
            return {'message': 'Internal server error'}, 500

@medical_chatbot_ns.route('/messages/<int:message_id>')
class MessageDetail(Resource):
    @medical_chatbot_ns.response(200, 'Deleted')
    @medical_chatbot_ns.response(401, 'Unauthorized')
    @medical_chatbot_ns.doc('delete_message', security='Bearer')
    @token_required
    def delete(self, current_user, message_id):
        """Delete a specific message (JWT Required)"""
        try:
            user_id = current_user['user_id']  # From JWT token
            
            message = Message.query.get(message_id)
            if not message:
                return {'message': 'Message not found'}, 404
            
            # Check ownership via conversation
            conversation = Conversation.query.get(message.conversation_id)
            if not conversation or conversation.user_id != user_id:
                return {'message': 'Unauthorized'}, 403
            
            db.session.delete(message)
            db.session.commit()
            
            return {'message': 'Message deleted successfully'}, 200
            
        except Exception as e:
            logger.error(f"Error deleting message: {str(e)}")
            db.session.rollback()
            return {'message': 'Internal server error'}, 500
