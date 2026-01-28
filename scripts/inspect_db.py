import sqlite3
import os

db_path = os.path.join('instance', 'chatbot.db')
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Table: MedicationLogs ===")
cursor.execute('SELECT log_id, user_id, status FROM MedicationLogs')
rows = cursor.fetchall()
for row in rows:
    print(row)

print("=== Table: Users ===")
try:
    cursor.execute('SELECT user_id, username FROM Users')
    for row in cursor.fetchall():
        print(row)
except Exception as e:
    print(f"Error reading Users: {e}")

conn.close()
