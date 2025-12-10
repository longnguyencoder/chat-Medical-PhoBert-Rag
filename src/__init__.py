from flask import Flask
from flask_restx import Api
from flask_cors import CORS
from flask_mail import Mail
from src.models.base import db
from src.config.config import Config

# Import all models to ensure they are registered with SQLAlchemy
from src.models.user import User
from src.models.attraction import Attraction
from src.models.message import Message
from src.models.conversation import Conversation
from src.models.otp import OTP
from src.models.itinerary import Itinerary
from src.models.itinerary_item import ItineraryItem
from src.models.notification import Notification
from src.models.health_profile import HealthProfile
from src.models.medication_schedule import MedicationSchedule
from src.models.medication_log import MedicationLog

mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # Configure CORS for local development
    # Allows client and backend on same machine to communicate
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",  # Allow all origins for development
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })
    
    # Load configuration
    app.config.from_object(Config)
    
    # Cấu hình cho file upload (Speech-to-Text)
    # MAX_CONTENT_LENGTH: Giới hạn kích thước request (25MB)
    # UPLOAD_FOLDER: Thư mục lưu file tạm (không dùng vì dùng tempfile)
    app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB
    
    # Configure API with JWT authorization
    authorizations = {
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token"
        }
    }
    
    api = Api(
        title='Medical Chatbot API',
        version='1.0',
        description='A medical question answering system using PhoBERT',
        doc='/docs',
        authorizations=authorizations,
        security='Bearer'
    )
    
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    
    # Register API
    api.init_app(app)
    
    # Add namespaces
    from src.controllers.auth_controller import auth_ns
    from src.controllers.medical_chatbot_controller import medical_chatbot_ns
    from src.controllers.notification_controller import notification_ns
    from src.controllers.speech_controller import speech_ns  # Speech-to-Text API
    from src.controllers.admin_controller import admin_ns  # Admin statistics API
    from src.controllers.health_profile_controller import health_profile_ns  # Health Profile API
    from src.controllers.medication_controller import medication_ns  # Medication Reminder API
    
    api.add_namespace(auth_ns, path='/api/auth')
    api.add_namespace(medical_chatbot_ns, path='/api/medical-chatbot')
    api.add_namespace(notification_ns, path='/api/notification')
    api.add_namespace(speech_ns, path='/api/speech')  # Speech-to-Text endpoints
    api.add_namespace(admin_ns, path='/api/admin')  # Admin statistics endpoints
    api.add_namespace(health_profile_ns, path='/api/health-profile')  # Health Profile endpoints
    api.add_namespace(medication_ns, path='/api/medication')  # Medication Reminder endpoints
    
    with app.app_context():
        db.create_all()
        
        # Initialize BM25 index for hybrid search
        try:
            from src.services.medical_chatbot_service import initialize_bm25_index
            initialize_bm25_index()
        except Exception as e:
            print(f"Warning: Failed to initialize BM25 index: {e}")
        
        # Initialize medication reminder scheduler
        try:
            from src.services.scheduler_service import init_scheduler
            init_scheduler(app)
        except Exception as e:
            print(f"Warning: Failed to initialize scheduler: {e}")
    
    return app