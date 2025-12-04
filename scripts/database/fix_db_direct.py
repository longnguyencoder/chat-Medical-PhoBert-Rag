
import sys
import os
from sqlalchemy import create_engine, text, inspect

# Add src to path
sys.path.append(os.getcwd())

from src.config.config import Config

def fix_db():
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        inspector = inspect(engine)
        
        with engine.connect() as conn:
            print("Checking columns...")
            columns = [col['name'] for col in inspector.get_columns('Conversations')]
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
