"""
Speech-to-Text API Controller
==============================
Controller cung cấp các endpoints xử lý giọng nói (Speech-to-Text).
Giúp ứng dụng Mobile/Web có thể gửi file âm thanh và nhận về văn bản hoặc câu trả lời từ chatbot.

Endpoints:
1. POST /api/speech/transcribe - Chỉ chuyển đổi Audio -> Text (dùng cho tính năng nhập liệu bằng giọng nói).
2. POST /api/speech/chat - Chuyển đổi Audio -> Text, sau đó gửi Text vào RAG Pipeline để hỏi Chatbot.
"""

from flask import request
from flask_restx import Namespace, Resource, fields
import logging
from werkzeug.datastructures import FileStorage

from src.services.speech_service import speech_service  # Service xử lý file audio
from src.services.medical_chatbot_service import (
    extract_user_intent_and_features,
    combined_search_with_filters,
    generate_natural_response
)
from src.services.cached_chatbot_service import cached_search, cached_response  # Hỗ trợ cache để tăng tốc
from src.utils.auth_middleware import token_required  # Bảo mật API
from src.models.base import db
from src.models.conversation import Conversation
from src.models.message import Message
from datetime import datetime

# Khởi tạo logger để ghi nhận activity
logger = logging.getLogger(__name__)

# Namespace 'speech' -> URL gốc: /api/speech
speech_ns = Namespace(
    'speech',
    description='Speech-to-Text operations - Xử lý giọng nói y tế'
)

# ============================================================================
# API MODELS (Định nghĩa Interface cho Swagger API)
# ============================================================================

# Model Response cho API Transcribe
transcribe_response = speech_ns.model('TranscribeResponse', {
    'success': fields.Boolean(description='Trạng thái request (true/false)'),
    'text': fields.String(description='Văn bản đã được chuyển đổi từ giọng nói'),
    'language': fields.String(description='Ngôn ngữ phát hiện được (VD: vi, en)'),
    'duration': fields.Float(description='Độ dài file âm thanh (giây)'),
    'message': fields.String(description='Thông báo chi tiết')
})

# Model Response cho API Chat Voice
chat_response = speech_ns.model('SpeechChatResponse', {
    'success': fields.Boolean(description='Trạng thái request'),
    'transcribed_text': fields.String(description='Nội dung người dùng nói (đã chuyển thành chữ)'),
    'question': fields.String(description='Câu hỏi (như transcribed_text)'),
    'answer': fields.String(description='Câu trả lời từ Bác sĩ AI'),
    'conversation_id': fields.Integer(description='ID cuộc hội thoại'),
    'message_id': fields.Integer(description='ID tin nhắn trả lời'),
    'language': fields.String(description='Ngôn ngữ'),
    'duration': fields.Float(description='Thời lượng audio')
})

# Parser xử lý file upload (Multipart/form-data)
upload_parser = speech_ns.parser()
upload_parser.add_argument(
    'audio',
    location='files',
    type=FileStorage,
    required=True,
    help='File audio (hỗ trợ mp3, wav, m4a, webm, ogg, flac). Tối đa 25MB.'
)
upload_parser.add_argument(
    'language',
    location='form',
    type=str,
    required=False,
    default='vi',
    help='Mã ngôn ngữ mong muốn (vi=Tiếng Việt). Để trống để tự động phát hiện.'
)

# Parser mở rộng cho Chat endpoint (cần thêm conversation_id)
chat_parser = upload_parser.copy()
chat_parser.add_argument(
    'conversation_id',
    location='form',
    type=int,
    required=False,
    help='ID cuộc hội thoại (nếu muốn chat tiếp trong luồng cũ)'
)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@speech_ns.route('/transcribe')
class TranscribeAudio(Resource):
    """
    Endpoint đơn giản: Audio In -> Text Out.
    Thường dùng khi user bấm nút mic ở ô input text.
    """
    
    @speech_ns.expect(upload_parser)
    @speech_ns.response(200, 'Success', transcribe_response)
    @speech_ns.response(400, 'Bad Request - File lỗi')
    @speech_ns.response(500, 'Server Error')
    def post(self):
        """
        Chuyển file audio thành văn bản (Transcribe).
        """
        try:
            # 1. Kiểm tra file upload
            if 'audio' not in request.files:
                return {'success': False, 'message': 'No audio file provided'}, 400
            
            audio_file = request.files['audio']
            language = request.form.get('language', 'vi')
            
            logger.info(f"🎤 Transcribe request received: {audio_file.filename}")
            
            # 2. Gọi Service xử lý (Lưu temp -> Gọi Whisper API -> Xóa temp)
            result = speech_service.process_audio_file(audio_file, language=language)
            
            # 3. Trả về kết quả
            return {
                'success': True,
                'text': result['text'],
                'language': result['language'],
                'duration': result.get('duration', 0),
                'message': 'Transcription successful'
            }, 200
            
        except ValueError as e:
            # Lỗi do file không hợp lệ (sai định dạng, quá lớn...)
            logger.warning(f"Validation error: {e}")
            return {'success': False, 'message': str(e)}, 400
            
        except Exception as e:
            # Lỗi không mong muốn
            logger.error(f"Transcription error: {e}", exc_info=True)
            return {'success': False, 'message': f'Failed to process audio: {str(e)}'}, 500


@speech_ns.route('/chat')
class SpeechToChat(Resource):
    """
    Endpoint nâng cao: Audio In -> Text -> RAG Bot -> Answer Out.
    Giúp tạo trải nghiệm hội thoại bằng giọng nói mượt mà (Voice interaction).
    """
    
    @speech_ns.expect(chat_parser)
    @speech_ns.response(200, 'Success', chat_response)
    @speech_ns.response(401, 'Unauthorized')
    @speech_ns.doc(security='Bearer')
    @token_required
    def post(self, current_user):
        """
        Xử lý toàn bộ luồng Chat bằng giọng nói.
        """
        try:
            # --- PHASE 1: INPUT HANDLING (NHẬN DỮ LIỆU) ---
            if 'audio' not in request.files:
                return {'success': False, 'message': 'No audio file provided'}, 400
            
            audio_file = request.files['audio']
            language = request.form.get('language', 'vi')
            conversation_id = request.form.get('conversation_id', type=int)
            
            user_id = current_user['user_id']
            user_name = current_user.get('full_name')
            
            logger.info(f"🗣️ Voice Chat Request: User {user_id} - File {audio_file.filename}")
            
            # --- PHASE 2: SPEECH-TO-TEXT (CHUYỂN ĐỔI) ---
            transcribe_result = speech_service.process_audio_file(audio_file, language=language)
            transcribed_text = transcribe_result['text']
            
            logger.info(f"📝 Transcribed: {transcribed_text[:100]}...")
            
            # --- PHASE 3: CONVERSATION MANAGEMENT (QUẢN LÝ HỘI THOẠI) ---
            # Tìm hoặc tạo hội thoại mới
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
                    title=transcribed_text[:50] + "..."  # Dùng đoạn đầu câu nói làm tiêu đề
                )
                db.session.add(conversation)
                db.session.commit()
            
            # Lưu tin nhắn của User vào DB
            user_msg = Message(
                conversation_id=conversation.conversation_id,
                sender='user',
                message_text=transcribed_text,
                message_type='voice',  # Đánh dấu là tin nhắn thoại
                sent_at=datetime.utcnow()
            )
            db.session.add(user_msg)
            db.session.commit()
            
            # --- PHASE 4: RAG PIPELINE (TÌM KIẾM & TRẢ LỜI) ---
            
            # 1. Phân tích ý định (Intent Classification) & Trích xuất thực thể
            extraction_result = extract_user_intent_and_features(transcribed_text)
            extracted_features = extraction_result.get('extracted_features', {})
            
            # 2. Tìm kiếm thông tin (Hybrid Search) - Có dùng Cache
            search_result = cached_search(
                combined_search_with_filters,
                transcribed_text,
                extracted_features
            )
            search_results = search_result.get('results', [])
            
            # 3. Sinh câu trả lời (LLM Generation) - Có dùng Cache
            # (Truyền conversation_id để bot nhớ ngữ cảnh cũ)
            response = cached_response(
                generate_natural_response,
                transcribed_text,
                search_results,
                extracted_features,
                conversation_id=conversation.conversation_id,
                user_name=user_name
            )
            answer = response.get('answer')
            
            # --- PHASE 5: SAVE & RETURN (LƯU VÀ TRẢ VỀ) ---
            
            # Lưu câu trả lời của Bot
            bot_msg = Message(
                conversation_id=conversation.conversation_id,
                sender='bot',
                message_text=answer,
                message_type='text',  # Bot trả lời bằng text (App sẽ TTS nếu cần)
                sent_at=datetime.utcnow()
            )
            db.session.add(bot_msg)
            db.session.commit()
            
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
            logger.warning(f"Validation error: {e}")
            return {'success': False, 'message': str(e)}, 400
            
        except Exception as e:
            logger.error(f"Speech-to-chat error: {e}", exc_info=True)
            db.session.rollback()
            return {'success': False, 'message': f'Failed to process request: {str(e)}'}, 500


@speech_ns.route('/health')
class SpeechHealthCheck(Resource):
    """
    Endpoint kiểm tra trạng thái Speech Service.
    """
    
    @speech_ns.response(200, 'Healthy')
    @speech_ns.response(500, 'Unhealthy')
    def get(self):
        """Kiểm tra dependency (OpenAI, Whisper lib)."""
        try:
            import whisper  # Kiểm tra thư viện (nếu dùng local)
            
            return {
                'success': True,
                'service': 'speech-to-text',
                'status': 'healthy',
                'type': 'openai-api', # Đang dùng API
                'model_loaded': True
            }, 200
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'success': False,
                'status': 'unhealthy',
                'error': str(e)
            }, 500
