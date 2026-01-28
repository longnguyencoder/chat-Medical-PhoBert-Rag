import sys
import os
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock expensive modules BEFORE importing src
sys.modules['src.services.medical_chatbot_service'] = MagicMock()
sys.modules['src.services.scheduler_service'] = MagicMock()

from src import create_app
from src.models.base import db
from src.models.user import User
from src.models.medication_log import MedicationLog

app = create_app()

with app.app_context():
    print("=== Users ===")
    users = User.query.all()
    for u in users:
        print(f"ID: {u.user_id}, Name: {u.username}, Email: {u.email}")

    print("\n=== Medication Logs (First 20) ===")
    logs = MedicationLog.query.limit(20).all()
    for log in logs:
        print(f"\nLogID: {log.log_id}\nUserID: {log.user_id}\nStatus: {log.status}\nScheduleID: {log.schedule_id}")
    
    print(f"\nTotal Logs: {MedicationLog.query.count()}")

    print("\n=== Checking Log ID 5 ===")
    log_5 = MedicationLog.query.get(5)
    if log_5:
        print(f"Log 5 FOUND: UserID: {log_5.user_id}, Status: {log_5.status}, ScheduleID: {log_5.schedule_id}")
    else:
        print("Log 5 NOT FOUND")
