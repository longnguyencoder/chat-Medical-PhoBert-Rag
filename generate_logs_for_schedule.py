"""
Script to manually generate medication logs for a schedule
"""
import sys
sys.path.insert(0, 'd:/ChatbotMedical_server/ChatbotMedical_server')

from src import create_app
from src.models.base import db
from src.models.medication_schedule import MedicationSchedule
from src.services import medication_service

app = create_app()

with app.app_context():
    schedule_id = 7
    
    print(f"Checking schedule {schedule_id}...")
    schedule = MedicationSchedule.query.get(schedule_id)
    
    if not schedule:
        print(f"❌ Schedule {schedule_id} not found!")
        sys.exit(1)
    
    print(f"✅ Found schedule: {schedule.medication_name}")
    print(f"   User: {schedule.user_id}")
    print(f"   Times: {schedule.get_time_of_day_list()}")
    print(f"   Active: {schedule.is_active}")
    
    print("\n🔧 Regenerating logs for the next 7 days...")
    
    # Import the private function
    from src.services.medication_service import _generate_logs_for_schedule
    
    # Generate logs
    _generate_logs_for_schedule(schedule, days=7)
    db.session.commit()
    
    print("✅ Logs generated successfully!")
    
    # Count logs
    from src.models.medication_log import MedicationLog
    log_count = MedicationLog.query.filter_by(schedule_id=schedule_id).count()
    print(f"📊 Total logs for schedule {schedule_id}: {log_count}")
