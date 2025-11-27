#!/usr/bin/env python3
"""
Migration script to add Notifications table to PostgreSQL database
"""

import psycopg2
from psycopg2 import sql
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.config import Config

def create_notifications_table():
    """Create Notifications table in PostgreSQL database"""
    
    # Database connection parameters from config
    db_params = {
        'host': Config.DB_HOST,
        'database': Config.DB_NAME,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'port': Config.DB_PORT
    }
    
    try:
        # Connect to PostgreSQL database
        print("🔌 Connecting to PostgreSQL database...")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Check if Notifications table already exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'Notifications'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("⚠️  Notifications table already exists!")
            return
        
        # Create Notifications table
        print("📋 Creating Notifications table...")
        
        create_table_sql = """
        CREATE TABLE "Notifications" (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            itinerary_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            notification_type VARCHAR(50) DEFAULT 'itinerary_reminder',
            is_read BOOLEAN DEFAULT FALSE,
            scheduled_for TIMESTAMP NOT NULL,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_deleted BOOLEAN DEFAULT FALSE,
            
            -- Foreign key constraints
            CONSTRAINT fk_notifications_user 
                FOREIGN KEY (user_id) 
                REFERENCES "Users"(user_id) 
                ON DELETE CASCADE,
                
            CONSTRAINT fk_notifications_itinerary 
                FOREIGN KEY (itinerary_id) 
                REFERENCES "Itineraries"(id) 
                ON DELETE CASCADE
        );
        """
        
        cursor.execute(create_table_sql)
        
        # Create indexes for better performance
        print("📊 Creating indexes...")
        
        # Index for user_id (for querying user notifications)
        cursor.execute("""
            CREATE INDEX idx_notifications_user_id 
            ON "Notifications"(user_id);
        """)
        
        # Index for scheduled_for (for scheduler queries)
        cursor.execute("""
            CREATE INDEX idx_notifications_scheduled_for 
            ON "Notifications"(scheduled_for);
        """)
        
        # Index for notification_type
        cursor.execute("""
            CREATE INDEX idx_notifications_type 
            ON "Notifications"(notification_type);
        """)
        
        # Index for is_deleted (for filtering deleted notifications)
        cursor.execute("""
            CREATE INDEX idx_notifications_deleted 
            ON "Notifications"(is_deleted);
        """)
        
        # Index for sent_at (for scheduler queries)
        cursor.execute("""
            CREATE INDEX idx_notifications_sent_at 
            ON "Notifications"(sent_at);
        """)
        
        # Commit the transaction
        conn.commit()
        
        print("✅ Notifications table created successfully!")
        print("📋 Table structure:")
        print("   - id: SERIAL PRIMARY KEY")
        print("   - user_id: INTEGER (FK to Users)")
        print("   - itinerary_id: INTEGER (FK to Itineraries)")
        print("   - title: VARCHAR(255)")
        print("   - message: TEXT")
        print("   - notification_type: VARCHAR(50)")
        print("   - is_read: BOOLEAN")
        print("   - scheduled_for: TIMESTAMP")
        print("   - sent_at: TIMESTAMP")
        print("   - created_at: TIMESTAMP")
        print("   - is_deleted: BOOLEAN")
        print("\n📊 Indexes created:")
        print("   - idx_notifications_user_id")
        print("   - idx_notifications_scheduled_for")
        print("   - idx_notifications_type")
        print("   - idx_notifications_deleted")
        print("   - idx_notifications_sent_at")
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("🔌 Database connection closed.")

def verify_table_structure():
    """Verify the Notifications table structure"""
    
    db_params = {
        'host': Config.DB_HOST,
        'database': Config.DB_NAME,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'port': Config.DB_PORT
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Get table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'Notifications'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        print("\n🔍 Verifying table structure:")
        print("=" * 60)
        print(f"{'Column Name':<20} {'Data Type':<15} {'Nullable':<10} {'Default'}")
        print("=" * 60)
        
        for column in columns:
            column_name, data_type, is_nullable, column_default = column
            default = column_default if column_default else 'NULL'
            print(f"{column_name:<20} {data_type:<15} {is_nullable:<10} {default}")
        
        # Check indexes
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'Notifications';
        """)
        
        indexes = cursor.fetchall()
        
        print(f"\n📊 Found {len(indexes)} indexes:")
        for index in indexes:
            print(f"   - {index[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verifying table: {e}")

def insert_sample_data():
    """Insert sample notification data for testing"""
    
    db_params = {
        'host': Config.DB_HOST,
        'database': Config.DB_NAME,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'port': Config.DB_PORT
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Check if we have any users and itineraries
        cursor.execute('SELECT COUNT(*) FROM "Users";')
        user_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM "Itineraries";')
        itinerary_count = cursor.fetchone()[0]
        
        if user_count == 0 or itinerary_count == 0:
            print("⚠️  No users or itineraries found. Skipping sample data insertion.")
            return
        
        # Get first user and itinerary
        cursor.execute('SELECT user_id FROM "Users" LIMIT 1;')
        user_id = cursor.fetchone()[0]
        
        cursor.execute('SELECT id FROM "Itineraries" LIMIT 1;')
        itinerary_id = cursor.fetchone()[0]
        
        # Insert sample notification
        sample_sql = """
        INSERT INTO "Notifications" (
            user_id, itinerary_id, title, message, 
            notification_type, scheduled_for, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
        );
        """
        
        from datetime import datetime, timedelta
        
        sample_data = (
            user_id,
            itinerary_id,
            "Sample Reminder",
            "This is a sample notification for testing purposes.",
            "itinerary_reminder",
            datetime.now() + timedelta(hours=1)  # Schedule for 1 hour from now
        )
        
        cursor.execute(sample_sql, sample_data)
        conn.commit()
        
        print("✅ Sample notification data inserted successfully!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error inserting sample data: {e}")

if __name__ == "__main__":
    print("🚀 Starting Notifications table migration...")
    print("=" * 50)
    
    # Create the table
    create_notifications_table()
    
    # Verify the structure
    verify_table_structure()
    
    # Insert sample data (optional)
    print("\n📝 Inserting sample data...")
    insert_sample_data()
    
    print("\n🎉 Migration completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Restart your Flask application")
    print("   2. The notification system will be automatically enabled")
    print("   3. New itineraries will automatically create reminder notifications")
    print("   4. Run 'python test_notification.py' to test the system") 