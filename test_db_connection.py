#!/usr/bin/env python3
"""
Test script to check PostgreSQL database connection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not installed. Please install it first:")
    print("   pip install psycopg2-binary")
    sys.exit(1)

from src.config.config import Config

def test_database_connection():
    """Test connection to PostgreSQL database"""
    
    print("🔍 Testing Database Connection")
    print("=" * 40)
    
    # Check if environment variables are set
    print("📋 Checking configuration...")
    
    config_vars = {
        'DB_HOST': Config.DB_HOST,
        'DB_NAME': Config.DB_NAME,
        'DB_USER': Config.DB_USER,
        'DB_PASSWORD': Config.DB_PASSWORD,
        'DB_PORT': Config.DB_PORT
    }
    
    missing_vars = []
    for var_name, var_value in config_vars.items():
        if var_value is None:
            missing_vars.append(var_name)
        else:
            # Hide password for security
            display_value = var_value if var_name != 'DB_PASSWORD' else '***'
            print(f"   ✅ {var_name}: {display_value}")
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("   Please check your .env file")
        return False
    
    # Test connection
    print(f"\n🔌 Attempting to connect to database...")
    print(f"   Host: {Config.DB_HOST}")
    print(f"   Port: {Config.DB_PORT}")
    print(f"   Database: {Config.DB_NAME}")
    print(f"   User: {Config.DB_USER}")
    
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=Config.DB_PORT
        )
        
        print("✅ Database connection successful!")
        
        # Test basic operations
        cursor = conn.cursor()
        
        # Check PostgreSQL version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"📊 PostgreSQL version: {version.split(',')[0]}")
        
        # Check if required tables exist
        print("\n📋 Checking required tables...")
        
        required_tables = ['Users', 'Itineraries', 'Notifications']
        existing_tables = []
        
        for table in required_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table,))
            
            exists = cursor.fetchone()[0]
            if exists:
                print(f"   ✅ {table} table exists")
                existing_tables.append(table)
            else:
                print(f"   ❌ {table} table does not exist")
        
        # Check table counts
        print("\n📊 Table record counts:")
        for table in existing_tables:
            cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
            count = cursor.fetchone()[0]
            print(f"   📈 {table}: {count} records")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Database connection test completed successfully!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Connection failed: {e}")
        
        # Provide helpful error messages
        if "connection refused" in str(e).lower():
            print("\n💡 Possible solutions:")
            print("   1. Check if PostgreSQL is running")
            print("   2. Verify the host and port in your .env file")
            print("   3. Check firewall settings")
        elif "authentication failed" in str(e).lower():
            print("\n💡 Possible solutions:")
            print("   1. Check username and password in .env file")
            print("   2. Verify user exists in PostgreSQL")
            print("   3. Check pg_hba.conf configuration")
        elif "database" in str(e).lower() and "does not exist" in str(e).lower():
            print("\n💡 Possible solutions:")
            print("   1. Create the database first")
            print("   2. Check database name in .env file")
        
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def check_postgresql_installation():
    """Check if PostgreSQL is installed and running"""
    
    print("\n🔍 Checking PostgreSQL Installation")
    print("=" * 40)
    
    import subprocess
    import platform
    
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Check if PostgreSQL service is running on Windows
            result = subprocess.run(['sc', 'query', 'postgresql'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ PostgreSQL service found on Windows")
            else:
                print("❌ PostgreSQL service not found on Windows")
                
        elif system == "darwin":  # macOS
            # Check if PostgreSQL is running via brew
            result = subprocess.run(['brew', 'services', 'list'], 
                                  capture_output=True, text=True)
            if 'postgresql' in result.stdout:
                print("✅ PostgreSQL service found via Homebrew")
            else:
                print("❌ PostgreSQL service not found via Homebrew")
                
        elif system == "linux":
            # Check if PostgreSQL is running on Linux
            result = subprocess.run(['systemctl', 'is-active', 'postgresql'], 
                                  capture_output=True, text=True)
            if result.stdout.strip() == 'active':
                print("✅ PostgreSQL service is running on Linux")
            else:
                print("❌ PostgreSQL service is not running on Linux")
                
    except FileNotFoundError:
        print("⚠️  Could not check PostgreSQL service status")
        print("   Please check manually if PostgreSQL is installed and running")

if __name__ == "__main__":
    print("🚀 Database Connection Test")
    print("=" * 50)
    
    # Check PostgreSQL installation
    check_postgresql_installation()
    
    # Test database connection
    success = test_database_connection()
    
    if success:
        print("\n✅ All tests passed! Your database is ready.")
        print("\n📋 Next steps:")
        print("   1. Run migration: python migrate_notifications.py")
        print("   2. Start your Flask app: python main.py")
        print("   3. Test notification system: python test_notification.py")
    else:
        print("\n❌ Database connection failed.")
        print("   Please check the configuration and try again.")
        sys.exit(1) 