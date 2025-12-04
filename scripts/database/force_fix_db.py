
import sys
import os
import psycopg2
from urllib.parse import urlparse

# Add src to path
sys.path.append(os.getcwd())

from src.config import Config

def force_fix():
    db_url = Config.SQLALCHEMY_DATABASE_URI
    print(f"Connecting to database...")
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if column exists
        print("Checking for 'summary' column...")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'Conversations' AND column_name = 'summary';
        """)
        result = cur.fetchone()
        
        if result:
            print("✅ Column 'summary' ALREADY EXISTS.")
        else:
            print("⚠️ Column 'summary' MISSING. Adding it now...")
            cur.execute('ALTER TABLE "Conversations" ADD COLUMN summary TEXT;')
            print("✅ Column 'summary' ADDED SUCCESSFULLY.")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    force_fix()
