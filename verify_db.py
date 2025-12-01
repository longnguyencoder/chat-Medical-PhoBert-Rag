
import sys
import os
from sqlalchemy import create_engine, inspect

# Add src to path
sys.path.append(os.getcwd())

from src.config import Config

def check_column():
    print(f"Checking database...")
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('Conversations')]
    
    if 'summary' in columns:
        print("✅ SUCCESS: 'summary' column exists!")
    else:
        print("❌ FAILURE: 'summary' column is MISSING!")

if __name__ == "__main__":
    check_column()
