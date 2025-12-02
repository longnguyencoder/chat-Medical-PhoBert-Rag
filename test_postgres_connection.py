import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def test_postgresql_connection():
    """Test PostgreSQL connection using DATABASE_POSTGRESQL_URL"""
    
    db_url = os.getenv('DATABASE_POSTGRESQL_URL')
    
    print("=" * 60)
    print("Testing PostgreSQL Connection")
    print("=" * 60)
    print(f"\nConnection String: {db_url}")
    print()
    
    if not db_url:
        print("❌ ERROR: DATABASE_POSTGRESQL_URL not found in .env file")
        return False
    
    try:
        # Parse the URL to show details (without password)
        if '@' in db_url:
            parts = db_url.split('@')
            host_db = parts[1]
            print(f"Connecting to: {host_db}")
        
        # Try to connect
        print("\nAttempting connection...")
        conn = psycopg2.connect(db_url)
        
        print("✅ Connection successful!")
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"\nPostgreSQL version: {version[0]}")
        
        # Check if Users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'Users'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ 'Users' table exists")
            
            # Count users
            cursor.execute("SELECT COUNT(*) FROM \"Users\";")
            count = cursor.fetchone()[0]
            print(f"   Total users: {count}")
        else:
            print("⚠️  'Users' table does not exist - you may need to run migrations")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ All checks passed!")
        print("=" * 60)
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Connection Error:")
        print(f"   {str(e)}")
        print("\nPossible causes:")
        print("   1. PostgreSQL is not running")
        print("   2. Database does not exist")
        print("   3. Wrong username/password")
        print("   4. Wrong host/port")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected Error:")
        print(f"   {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    test_postgresql_connection()
