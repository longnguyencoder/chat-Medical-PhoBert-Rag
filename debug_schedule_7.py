"""
Debug script to check medication logs for schedule_id 7
"""
import sys
sys.path.insert(0, 'd:/ChatbotMedical_server/ChatbotMedical_server')

from src.models.base import db
from src.models.medication_schedule import MedicationSchedule
from src.models.medication_log import MedicationLog
from src import create_app
from datetime import datetime
import pytz

app = create_app()

with app.app_context():
    print("=" * 80)
    print("CHECKING SCHEDULE ID 7")
    print("=" * 80)
    
    # Get schedule details
    schedule = MedicationSchedule.query.get(7)
    if schedule:
        print(f"\n✅ Schedule found:")
        print(f"   - Medication: {schedule.medication_name}")
        print(f"   - User ID: {schedule.user_id}")
        print(f"   - Times: {schedule.get_time_of_day_list()}")
        print(f"   - Start Date: {schedule.start_date}")
        print(f"   - End Date: {schedule.end_date}")
        print(f"   - Is Active: {schedule.is_active}")
        print(f"   - Created: {schedule.created_at}")
    else:
        print("\n❌ Schedule ID 7 not found!")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("CHECKING LOGS FOR SCHEDULE 7")
    print("=" * 80)
    
    # Get all logs for this schedule
    logs = MedicationLog.query.filter_by(schedule_id=7).order_by(MedicationLog.scheduled_time).all()
    
    if logs:
        print(f"\n✅ Found {len(logs)} logs:")
        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        
        for log in logs:
            scheduled_vn = log.scheduled_time.astimezone(vietnam_tz)
            print(f"\n   Log ID {log.log_id}:")
            print(f"      - Scheduled: {scheduled_vn.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"      - Status: {log.status}")
            print(f"      - User ID: {log.user_id}")
            if log.actual_time:
                actual_vn = log.actual_time.astimezone(vietnam_tz)
                print(f"      - Actual: {actual_vn.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    else:
        print("\n❌ No logs found for schedule 7!")
        print("\nThis means logs were never generated. Possible reasons:")
        print("1. Schedule was created before the auto-generation feature was added")
        print("2. An error occurred during log generation")
        print("3. The schedule start_date is in the future")
    
    print("\n" + "=" * 80)
    print("CHECKING FOR TODAY'S 08:00 LOG")
    print("=" * 80)
    
    # Check specifically for 2026-01-24 08:00
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    target_time = vietnam_tz.localize(datetime(2026, 1, 24, 8, 0, 0))
    
    from datetime import timedelta
    matching_logs = MedicationLog.query.filter(
        MedicationLog.schedule_id == 7,
        MedicationLog.scheduled_time >= target_time - timedelta(minutes=5),
        MedicationLog.scheduled_time <= target_time + timedelta(minutes=5)
    ).all()
    
    if matching_logs:
        print(f"\n✅ Found {len(matching_logs)} log(s) around 2026-01-24 08:00:")
        for log in matching_logs:
            scheduled_vn = log.scheduled_time.astimezone(vietnam_tz)
            print(f"   - Log ID {log.log_id}: {scheduled_vn.strftime('%Y-%m-%d %H:%M:%S %Z')} ({log.status})")
    else:
        print("\n❌ No log found for 2026-01-24 08:00 ±5 minutes")
        print("\nSearching for ANY logs on 2026-01-24...")
        
        day_start = vietnam_tz.localize(datetime(2026, 1, 24, 0, 0, 0))
        day_end = vietnam_tz.localize(datetime(2026, 1, 25, 0, 0, 0))
        
        day_logs = MedicationLog.query.filter(
            MedicationLog.schedule_id == 7,
            MedicationLog.scheduled_time >= day_start,
            MedicationLog.scheduled_time < day_end
        ).all()
        
        if day_logs:
            print(f"\n✅ Found {len(day_logs)} log(s) on 2026-01-24:")
            for log in day_logs:
                scheduled_vn = log.scheduled_time.astimezone(vietnam_tz)
                print(f"   - Log ID {log.log_id}: {scheduled_vn.strftime('%Y-%m-%d %H:%M:%S %Z')} ({log.status})")
        else:
            print("\n❌ No logs at all on 2026-01-24")
    
    print("\n" + "=" * 80)
