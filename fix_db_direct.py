
import sys
import os
from sqlalchemy import create_engine, text

# Add src to path
sys.path.append(os.getcwd())

from src.config import Config

def fix_db():
    print(f"Connecting to {Config.SQLALCHEMY_DATABASE_URI}...")
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    try:
        with engine.connect() as conn:
            print("Checking columns...")
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'Conversations';"))
            columns = [row[0] for row in result]
            print(f"Current columns: {columns}")
            
            if 'summary' not in columns:
                print("Adding summary column...")
                conn.execute(text('ALTER TABLE "Conversations" ADD COLUMN summary TEXT;'))
                conn.commit()
                print("✅ Column added successfully!")
            else:
                print("✓ Column already exists.")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_db()
