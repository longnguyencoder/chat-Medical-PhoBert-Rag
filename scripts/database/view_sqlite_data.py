"""
View SQLite Database Data
==========================
Quick script to view data in SQLite database
"""

import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = os.path.join('instance', 'chatbot.db')

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def view_database():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Database info
    print_section("📊 DATABASE INFO")
    file_size = os.path.getsize(DB_PATH) / 1024 / 1024  # MB
    print(f"Location: {os.path.abspath(DB_PATH)}")
    print(f"Size: {file_size:.2f} MB")
    
    # List tables
    print_section("📋 TABLES")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  • {table[0]}: {count} records")
    
    # Users
    print_section("👥 USERS (Last 5)")
    cursor.execute("""
        SELECT user_id, email, full_name, is_verified, created_at 
        FROM users 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    users = cursor.fetchall()
    if users:
        print(f"{'ID':<5} {'Email':<30} {'Name':<20} {'Verified':<10} {'Created'}")
        print("-" * 90)
        for user in users:
            verified = "✓" if user[3] else "✗"
            print(f"{user[0]:<5} {user[1]:<30} {user[2]:<20} {verified:<10} {user[4]}")
    else:
        print("  No users found")
    
    # Conversations
    print_section("💬 CONVERSATIONS (Last 5)")
    cursor.execute("""
        SELECT c.conversation_id, c.user_id, c.title, c.started_at,
               COUNT(m.message_id) as msg_count
        FROM conversations c
        LEFT JOIN messages m ON c.conversation_id = m.conversation_id
        GROUP BY c.conversation_id
        ORDER BY c.started_at DESC 
        LIMIT 5
    """)
    convs = cursor.fetchall()
    if convs:
        print(f"{'ID':<5} {'User':<6} {'Messages':<10} {'Title':<40} {'Started'}")
        print("-" * 90)
        for conv in convs:
            title = conv[2][:37] + "..." if len(conv[2]) > 40 else conv[2]
            print(f"{conv[0]:<5} {conv[1]:<6} {conv[4]:<10} {title:<40} {conv[3]}")
    else:
        print("  No conversations found")
    
    # Messages
    print_section("📝 MESSAGES (Last 10)")
    cursor.execute("""
        SELECT m.message_id, m.conversation_id, m.sender, m.message_type,
               m.message_text, m.sent_at
        FROM messages m
        ORDER BY m.sent_at DESC 
        LIMIT 10
    """)
    msgs = cursor.fetchall()
    if msgs:
        print(f"{'ID':<6} {'Conv':<6} {'Sender':<8} {'Type':<8} {'Message':<50} {'Sent'}")
        print("-" * 110)
        for msg in msgs:
            text = msg[4][:47] + "..." if len(msg[4]) > 50 else msg[4]
            print(f"{msg[0]:<6} {msg[1]:<6} {msg[2]:<8} {msg[3]:<8} {text:<50} {msg[5]}")
    else:
        print("  No messages found")
    
    # Statistics
    print_section("📊 STATISTICS")
    
    # Message types
    cursor.execute("""
        SELECT message_type, COUNT(*) as count
        FROM messages
        GROUP BY message_type
    """)
    msg_types = cursor.fetchall()
    if msg_types:
        print("Message Types:")
        for mt in msg_types:
            print(f"  • {mt[0]}: {mt[1]} messages")
    
    # Active conversations (with messages in last 7 days)
    cursor.execute("""
        SELECT COUNT(DISTINCT conversation_id)
        FROM messages
        WHERE sent_at > datetime('now', '-7 days')
    """)
    active_convs = cursor.fetchone()[0]
    print(f"\nActive conversations (last 7 days): {active_convs}")
    
    # Total messages today
    cursor.execute("""
        SELECT COUNT(*)
        FROM messages
        WHERE DATE(sent_at) = DATE('now')
    """)
    today_msgs = cursor.fetchone()[0]
    print(f"Messages today: {today_msgs}")
    
    conn.close()
    
    print_section("✅ DONE")
    print("To view more data:")
    print("  1. Use DB Browser: https://sqlitebrowser.org/")
    print("  2. Read guide: docs/guides/VIEW_SQLITE_DATA.md")
    print()

if __name__ == "__main__":
    view_database()
