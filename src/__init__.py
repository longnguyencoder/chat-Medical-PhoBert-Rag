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

mail = Mail()

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Load configuration
    app.config.from_object(Config)
    
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
    
    api.add_namespace(auth_ns, path='/api/auth')
    api.add_namespace(medical_chatbot_ns, path='/api/medical-chatbot')
    api.add_namespace(notification_ns, path='/api/notification')
    
    with app.app_context():
        db.create_all()
    
    return app