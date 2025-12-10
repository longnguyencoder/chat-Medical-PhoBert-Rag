from src.models.base import db
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
from src.models.medication_log import MedicationLog  # ← Thêm model mới

__all__ = [
    'User',
    'Attraction', 
    'Message',
    'Conversation',
    'OTP',
    'Itinerary',
    'ItineraryItem',
    'Notification',
    'HealthProfile',
    'MedicationSchedule',
    'MedicationLog'
] 