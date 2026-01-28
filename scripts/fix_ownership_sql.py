import sqlite3
import os

db_path = os.path.join('instance', 'chatbot.db')
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

TARGET_LOG_ID = 5
NEW_USER_ID = 5

try:
    print(f"Checking Log ID {TARGET_LOG_ID}...")
    cursor.execute('SELECT schedule_id, user_id FROM MedicationLogs WHERE log_id = ?', (TARGET_LOG_ID,))
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ Log {TARGET_LOG_ID} not found!")
    else:
        schedule_id, current_owner = row
        print(f"ℹ️  Log {TARGET_LOG_ID} belongs to User {current_owner} (Schedule {schedule_id})")
        
        if current_owner == NEW_USER_ID:
            print("✅ Already belongs to the correct user.")
        else:
            # 1. Update Schedule
            print(f"🔄 Transferring Schedule {schedule_id} from User {current_owner} to User {NEW_USER_ID}...")
            cursor.execute('UPDATE MedicationSchedules SET user_id = ? WHERE schedule_id = ?', (NEW_USER_ID, schedule_id))
            
            # 2. Update Logs
            cursor.execute('UPDATE MedicationLogs SET user_id = ? WHERE schedule_id = ?', (NEW_USER_ID, schedule_id))
            affected = cursor.rowcount
            
            conn.commit()
            print(f"✅ Success! Updated Schedule and {affected} Logs.")

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    conn.close()
