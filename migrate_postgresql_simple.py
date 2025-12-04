"""
Simple PostgreSQL Migration and Verification Script
This script will:
1. Check PostgreSQL connection
2. Create all tables from SQLAlchemy models
3. Verify tables were created successfully
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

def check_postgresql_connection():
    """Check if PostgreSQL is accessible"""
    print("=" * 60)
    print("STEP 1: Checking PostgreSQL Connection")
    print("=" * 60)
    
    db_url = os.getenv('DATABASE_POSTGRESQL_URL')
    
    if not db_url:
        print("❌ ERROR: DATABASE_POSTGRESQL_URL not found in .env file")
        print("\nPlease add to .env:")
        print("DATABASE_POSTGRESQL_URL=postgresql://user:password@host:port/database")
        return False
    
    # Hide password in output
    safe_url = db_url
    if '@' in db_url and ':' in db_url:
        parts = db_url.split('@')
        auth_parts = parts[0].split(':')
        if len(auth_parts) >= 3:
            safe_url = f"{auth_parts[0]}:{auth_parts[1]}:****@{parts[1]}"
    
    print(f"\nConnection URL: {safe_url}")
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Get PostgreSQL version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"\n✅ Connected successfully!")
        print(f"PostgreSQL version: {version.split(',')[0]}")
        
        # Get database name
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()[0]
        print(f"Database: {db_name}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Connection failed!")
        print(f"Error: {str(e)}")
        print("\nPossible causes:")
        print("  1. PostgreSQL is not running")
        print("  2. Database does not exist")
        print("  3. Wrong credentials in .env file")
        print("  4. Firewall blocking connection")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False

def create_tables():
    """Create all tables using SQLAlchemy models"""
    print("\n" + "=" * 60)
    print("STEP 2: Creating Database Tables")
    print("=" * 60)
    
    try:
        # Import Flask app and database
        from src import create_app
        from src.models.base import db
        
        # Import all models to ensure they're registered
        from src.models import (
            User, Conversation, Message, OTP, 
            Notification, Itinerary, ItineraryItem
        )
        
        print("\n📦 Creating Flask app context...")
        app = create_app()
        
        with app.app_context():
            print("🔨 Creating all tables...")
            db.create_all()
            
            print("\n✅ Tables created successfully!")
            
            # List all tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n📋 Created {len(tables)} tables:")
            for table in sorted(tables):
                print(f"   ✓ {table}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_tables():
    """Verify tables exist in PostgreSQL"""
    print("\n" + "=" * 60)
    print("STEP 3: Verifying Tables")
    print("=" * 60)
    
    db_url = os.getenv('DATABASE_POSTGRESQL_URL')
    
    expected_tables = [
        'Users', 'Conversations', 'Messages', 'OTP',
        'Notifications', 'Itineraries', 'ItineraryItems'
    ]
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n✅ Found {len(existing_tables)} tables in database:")
        
        all_found = True
        for table in expected_tables:
            if table in existing_tables:
                # Count rows
                cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
                count = cursor.fetchone()[0]
                print(f"   ✓ {table} ({count} rows)")
            else:
                print(f"   ✗ {table} (MISSING)")
                all_found = False
        
        cursor.close()
        conn.close()
        
        if all_found:
            print("\n✅ All expected tables exist!")
            return True
        else:
            print("\n⚠️  Some tables are missing")
            return False
            
    except Exception as e:
        print(f"\n❌ Error verifying tables: {str(e)}")
        return False

def main():
    """Main migration workflow"""
    print("\n" + "🚀 " * 20)
    print("PostgreSQL Migration Tool")
    print("🚀 " * 20)
    
    # Step 1: Check connection
    if not check_postgresql_connection():
        print("\n❌ Migration aborted: Cannot connect to PostgreSQL")
        print("\nPlease fix the connection issue and try again.")
        return 1
    
    # Step 2: Create tables
    if not create_tables():
        print("\n❌ Migration aborted: Cannot create tables")
        return 1
    
    # Step 3: Verify tables
    if not verify_tables():
        print("\n⚠️  Migration completed with warnings")
        return 1
    
    # Success!
    print("\n" + "=" * 60)
    print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\n✅ Your application is now using PostgreSQL")
    print("\nNext steps:")
    print("  1. Start your server: python main.py")
    print("  2. Test API endpoints")
    print("  3. Verify medical chatbot still works with ChromaDB")
    print("\n" + "=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
