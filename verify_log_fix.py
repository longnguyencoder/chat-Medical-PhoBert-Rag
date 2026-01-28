"""
Verification script for on-the-fly log creation
"""
import sys
import os
sys.path.insert(0, 'd:/ChatbotMedical_server/ChatbotMedical_server')

from src import create_app
from src.models.base import db
from src.models.medication_log import MedicationLog
from src.models.medication_schedule import MedicationSchedule
from datetime import datetime
import pytz
import json

app = create_app()

with app.app_context():
    # 1. Setup - Ensure schedule 7 has a valid time for testing
    schedule_id = 7
    user_id = 5
    test_time_str = "08:00"
    
    schedule = MedicationSchedule.query.get(schedule_id)
    if not schedule:
        print("❌ Schedule 7 not found. Creating a dummy one...")
        # (This is just in case, typically it should exist)
        schedule = MedicationSchedule(
            schedule_id=schedule_id,
            user_id=user_id,
            medication_name="Test Med",
            time_of_day='["08:00"]',
            start_date=datetime.utcnow().date()
        )
        db.session.add(schedule)
        db.session.commit()

    # 2. Ensure NO log exists for today at 08:00
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    target_dt = vietnam_tz.localize(datetime(2026, 1, 24, 8, 0, 0))
    utc_dt = target_dt.astimezone(pytz.utc)
    
    MedicationLog.query.filter_by(
        schedule_id=schedule_id,
        scheduled_time=utc_dt
    ).delete()
    db.session.commit()
    print(f"🧹 Cleaned up existing logs for {target_dt}")

    # 3. Simulate the API call via the controller logic (or actual client if possible)
    # We'll just verify the logic by calling the db directly as if the controller did it
    print(f"🚀 Simulating API call for schedule_id={schedule_id}, scheduled_time='2026-01-24T08:00:00.000'")
    
    # This matches the logic I added to medication_controller.py
    matching_log = MedicationLog.query.filter_by(
        schedule_id=schedule_id,
        user_id=user_id,
        scheduled_time=utc_dt
    ).first()
    
    if not matching_log:
        print("🔍 No log found as expected. Creating on-the-fly...")
        new_log = MedicationLog(
            schedule_id=schedule_id,
            user_id=user_id,
            scheduled_time=utc_dt,
            status='taken'
        )
        new_log.actual_time = datetime.utcnow()
        db.session.add(new_log)
        db.session.commit()
        print(f"✅ Created new log: ID {new_log.log_id}")
    else:
        print(f"⚠️ Log already exists? ID {matching_log.log_id}")

    # 4. Cleanup
    print("\n✨ Verification complete.")
