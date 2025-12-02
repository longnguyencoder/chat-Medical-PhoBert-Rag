import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'chatbot.db')
db_path = os.path.abspath(db_path)

print(f"Database path: {db_path}")
print(f"Database exists: {os.path.exists(db_path)}")
print()

if not os.path.exists(db_path):
    print("ERROR: Database file does not exist!")
    exit(1)

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if Users table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Users';")
table_exists = cursor.fetchone()

if not table_exists:
    print("ERROR: 'Users' table does not exist!")
    conn.close()
    exit(1)

print("✅ 'Users' table exists")
print()

# Count total users
cursor.execute("SELECT COUNT(*) FROM Users;")
total_users = cursor.fetchone()[0]
print(f"Total users in database: {total_users}")
print()

# Check for specific user
email = "giupviecgiahoang8@gmail.com"
cursor.execute("SELECT user_id, email, full_name, is_verified, created_at FROM Users WHERE email = ?;", (email,))
user = cursor.fetchone()

if user:
    print(f"✅ User found:")
    print(f"  ID: {user[0]}")
    print(f"  Email: {user[1]}")
    print(f"  Full Name: {user[2]}")
    print(f"  Is Verified: {user[3]}")
    print(f"  Created At: {user[4]}")
else:
    print(f"❌ User with email '{email}' NOT FOUND")
    print()
    print("All users in database:")
    cursor.execute("SELECT user_id, email, full_name, is_verified FROM Users;")
    all_users = cursor.fetchall()
    for u in all_users:
        print(f"  - ID: {u[0]}, Email: {u[1]}, Name: {u[2]}, Verified: {u[3]}")

conn.close()
