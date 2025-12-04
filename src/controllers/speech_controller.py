"""
Speech-to-Text API Controller
==============================
Controller cung cấp REST API endpoints cho tính năng Speech-to-Text.

Endpoints:
1. POST /api/speech/transcribe - Chuyển audio thành text
2. POST /api/speech/chat - Chuyển audio thành text và hỏi chatbot
"""

from flask import request
from flask_restx import Namespace, Resource, fields
import logging
from werkzeug.datastructures import FileStorage

from src.services.speech_service import speech_service
from src.services.medical_chatbot_service import (
    extract_user_intent_and_features,
    combined_search_with_filters,
    generate_natural_response
)
from src.services.cached_chatbot_service import cached_search, cached_response
from src.utils.auth_middleware import token_required  # JWT decorator
from src.models.base import db
from src.models.conversation import Conversation
from src.models.message import Message
from datetime import datetime

# Khởi tạo logger
logger = logging.getLogger(__name__)

# Tạo namespace cho Speech API
speech_ns = Namespace(
    'speech',
    description='Speech-to-Text operations - Chuyển đổi giọng nói thành văn bản'
)

# ============================================================================
# API MODELS (Định nghĩa cấu trúc request/response cho Swagger UI)
# ============================================================================

# Model cho response của transcribe endpoint
transcribe_response = speech_ns.model('TranscribeResponse', {
    'success': fields.Boolean(description='Trạng thái thành công', example=True),
    'text': fields.String(description='Văn bản đã chuyển đổi', example='Tôi bị đau đầu và sốt'),
    'language': fields.String(description='Ngôn ngữ phát hiện được', example='vi'),
    'duration': fields.Float(description='Độ dài audio (giây)', example=3.5),
    'message': fields.String(description='Thông báo', example='Transcription successful')
})

# Model cho response của chat endpoint
chat_response = speech_ns.model('SpeechChatResponse', {
    'success': fields.Boolean(description='Trạng thái thành công'),
    'transcribed_text': fields.String(description='Văn bản đã chuyển đổi từ audio'),
    'question': fields.String(description='Câu hỏi (giống transcribed_text)'),
    'answer': fields.String(description='Câu trả lời từ chatbot'),
    'conversation_id': fields.Integer(description='ID cuộc hội thoại'),
    'message_id': fields.Integer(description='ID tin nhắn')
})

# Parser cho file upload
upload_parser = speech_ns.parser()
upload_parser.add_argument(
    'audio',
    location='files',
    type=FileStorage,
    required=True,
    help='File audio (mp3, wav, m4a, webm, ogg, flac). Tối đa 25MB'
)
upload_parser.add_argument(
    'language',
    location='form',
    type=str,
    required=False,
    default='vi',
    help='Mã ngôn ngữ (vi=Tiếng Việt, en=English, auto=tự động)'
)

# Parser cho chat endpoint (có thêm conversation_id)
chat_parser = upload_parser.copy()
chat_parser.add_argument(
    'conversation_id',
    location='form',
    type=int,
    required=False,
    help='ID cuộc hội thoại (để tiếp tục chat cũ)'
)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@speech_ns.route('/transcribe')
class TranscribeAudio(Resource):
    """
    Endpoint chuyển đổi audio thành text
    Không cần authentication - public endpoint
    """
    
    @speech_ns.expect(upload_parser)
    @speech_ns.response(200, 'Success', transcribe_response)
    @speech_ns.response(400, 'Bad Request - File không hợp lệ')
    @speech_ns.response(500, 'Internal Server Error - Lỗi xử lý')
    def post(self):
        """
        Chuyển đổi file audio thành văn bản
        
        Cách sử dụng:
        1. Chọn file audio từ máy tính
        2. (Tùy chọn) Chọn ngôn ngữ (mặc định: vi)
        3. Nhấn Execute
        
        Returns:
            JSON với text đã chuyển đổi
        """
        try:
            # Lấy file từ request
            if 'audio' not in request.files:
                return {
                    'success': False,
                    'message': 'No audio file provided'
                }, 400
            
            audio_file = request.files['audio']
            language = request.form.get('language', 'vi')
            
            logger.info(f"Received transcribe request: file={audio_file.filename}, language={language}")
            
            # Xử lý audio file
            result = speech_service.process_audio_file(audio_file, language=language)
            
            # Trả về kết quả
            return {
                'success': True,
                'text': result['text'],
                'language': result['language'],
                'duration': result.get('duration', 0),
                'message': 'Transcription successful'
            }, 200
            
        except ValueError as e:
            # Lỗi validation (file không hợp lệ)
            logger.warning(f"Validation error: {e}")
            return {
                'success': False,
                'message': str(e)
            }, 400
            
        except Exception as e:
            # Lỗi xử lý
            logger.error(f"Transcription error: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Failed to process audio: {str(e)}'
            }, 500


@speech_ns.route('/chat')
class SpeechToChat(Resource):
    """
    Endpoint chuyển audio thành text và tự động hỏi chatbot
    Yêu cầu JWT authentication
    """
    
    @speech_ns.expect(chat_parser)
    @speech_ns.response(200, 'Success', chat_response)
    @speech_ns.response(400, 'Bad Request')
    @speech_ns.response(401, 'Unauthorized - Cần JWT token')
    @speech_ns.response(500, 'Internal Server Error')
    @speech_ns.doc(security='Bearer')  # Yêu cầu JWT token
    @token_required
    def post(self, current_user):
        """
        Chuyển audio thành text và hỏi chatbot y tế
        
        Yêu cầu:
        - Header: Authorization: Bearer <JWT_TOKEN>
        - Body: multipart/form-data với file audio
        
        Quy trình:
        1. Chuyển audio thành text
        2. Tạo/lấy conversation
        3. Lưu tin nhắn user
        4. Gọi RAG pipeline để tạo câu trả lời
        5. Lưu tin nhắn bot
        6. Trả về kết quả
        
        Returns:
            JSON với text đã chuyển đổi và câu trả lời từ chatbot
        """
        try:
            # Lấy file từ request
            if 'audio' not in request.files:
                return {
                    'success': False,
                    'message': 'No audio file provided'
                }, 400
            
            audio_file = request.files['audio']
            language = request.form.get('language', 'vi')
            conversation_id = request.form.get('conversation_id', type=int)
            
            # Lấy user info từ JWT token
            user_id = current_user['user_id']
            user_name = current_user.get('full_name')
            
            logger.info(f"Received speech-to-chat request: user_id={user_id}, file={audio_file.filename}")
            
            # Bước 1: Chuyển audio thành text
            transcribe_result = speech_service.process_audio_file(audio_file, language=language)
            transcribed_text = transcribe_result['text']
            
            logger.info(f"Transcription successful: {transcribed_text[:100]}...")
            
            # Bước 2: Xử lý conversation (giống SecureMedicalChat)
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
                    title=transcribed_text[:50] + "..."
                )
                db.session.add(conversation)
                db.session.commit()
            
            # Bước 3: Lưu tin nhắn user
            user_msg = Message(
                conversation_id=conversation.conversation_id,
                sender='user',
                message_text=transcribed_text,
                message_type='voice',  # ← Fixed: 'voice' thay vì 'audio'
                sent_at=datetime.utcnow()
            )
            db.session.add(user_msg)
            db.session.commit()
            
            # Bước 4: RAG pipeline với caching
            extraction_result = extract_user_intent_and_features(transcribed_text)
            extracted_features = extraction_result.get('extracted_features', {})
            
            # CACHED Search
            search_result = cached_search(
                combined_search_with_filters,
                transcribed_text,
                extracted_features
            )
            search_results = search_result.get('results', [])
            
            # CACHED Response
            response = cached_response(
                generate_natural_response,
                transcribed_text,
                search_results,
                extracted_features,
                conversation_id=conversation.conversation_id,
                user_name=user_name
            )
            answer = response.get('answer')
            
            # Bước 5: Lưu câu trả lời bot
            bot_msg = Message(
                conversation_id=conversation.conversation_id,
                sender='bot',
                message_text=answer,
                message_type='text',
                sent_at=datetime.utcnow()
            )
            db.session.add(bot_msg)
            db.session.commit()
            
            # Bước 6: Trả về kết quả kết hợp
            return {
                'success': True,
                'transcribed_text': transcribed_text,
                'question': transcribed_text,
                'answer': answer,
                'conversation_id': conversation.conversation_id,
                'message_id': bot_msg.message_id,
                'language': transcribe_result['language'],
                'duration': transcribe_result.get('duration', 0)
            }, 200
            
        except ValueError as e:
            # Lỗi validation
            logger.warning(f"Validation error: {e}")
            return {
                'success': False,
                'message': str(e)
            }, 400
            
        except Exception as e:
            # Lỗi xử lý
            logger.error(f"Speech-to-chat error: {e}", exc_info=True)
            db.session.rollback()  # Rollback nếu có lỗi
            return {
                'success': False,
                'message': f'Failed to process request: {str(e)}'
            }, 500


@speech_ns.route('/health')
class SpeechHealthCheck(Resource):
    """
    Endpoint kiểm tra health của Speech service
    """
    
    @speech_ns.response(200, 'Service is healthy')
    @speech_ns.response(500, 'Service is unhealthy')
    def get(self):
        """
        Kiểm tra xem Speech service có hoạt động không
        
        Returns:
            JSON với trạng thái service
        """
        try:
            # Kiểm tra xem có thể import whisper không
            import whisper
            
            return {
                'success': True,
                'service': 'speech-to-text',
                'status': 'healthy',
                'model': speech_service.model_name,
                'model_loaded': speech_service.model is not None,
                'whisper_version': whisper.__version__
            }, 200
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'success': False,
                'service': 'speech-to-text',
                'status': 'unhealthy',
                'error': str(e)
            }, 500
