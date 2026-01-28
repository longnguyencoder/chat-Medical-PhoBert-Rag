import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import create_app
from src.models.base import db
from src.models.medication_log import MedicationLog
from src.models.medication_schedule import MedicationSchedule

app = create_app()

TARGET_LOG_ID = 5
NEW_USER_ID = 5

with app.app_context():
    print(f"Checking Log ID {TARGET_LOG_ID}...")
    log = MedicationLog.query.get(TARGET_LOG_ID)
    
    if not log:
        print(f"❌ Log {TARGET_LOG_ID} not found!")
        sys.exit(1)
        
    current_owner = log.user_id
    schedule_id = log.schedule_id
    
    print(f"ℹ️  Log {TARGET_LOG_ID} belongs to User {current_owner} (Schedule {schedule_id})")
    print(f"ℹ️  Goal: Transfer to User {NEW_USER_ID}")
    
    if current_owner == NEW_USER_ID:
        print("✅ Already belongs to the correct user. Nothing to do.")
        sys.exit(0)

    # 1. Update the Schedule
    schedule = MedicationSchedule.query.get(schedule_id)
    if schedule:
        print(f"🔄 Transferring Schedule {schedule_id} from User {schedule.user_id} to User {NEW_USER_ID}...")
        schedule.user_id = NEW_USER_ID
    else:
        print(f"⚠️ Schedule {schedule_id} not found!")

    # 2. Update ALL logs for this schedule (to keep consistency)
    logs = MedicationLog.query.filter_by(schedule_id=schedule_id).all()
    count = 0
    for l in logs:
        l.user_id = NEW_USER_ID
        count += 1
    
    print(f"🔄 Transferred {count} logs to User {NEW_USER_ID}.")
    
    db.session.commit()
    print("✅ Transfer Complete!")
