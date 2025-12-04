from src.config.config import Config
from sqlalchemy import create_engine, text
import os

def update_db_schema():
    print(f"Connecting to database: {Config.SQLALCHEMY_DATABASE_URI}")
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as conn:
        # Check if columns exist
        result = conn.execute(text("PRAGMA table_info(Conversations)"))
        columns = [row[1] for row in result]
        
        if 'is_archived' not in columns:
            print("Adding 'is_archived' column...")
            try:
                conn.execute(text("ALTER TABLE Conversations ADD COLUMN is_archived BOOLEAN DEFAULT 0"))
                print("✓ Added 'is_archived'")
            except Exception as e:
                print(f"Error adding is_archived: {e}")
        else:
            print("'is_archived' already exists.")
            
        if 'is_pinned' not in columns:
            print("Adding 'is_pinned' column...")
            try:
                conn.execute(text("ALTER TABLE Conversations ADD COLUMN is_pinned BOOLEAN DEFAULT 0"))
                print("✓ Added 'is_pinned'")
            except Exception as e:
                print(f"Error adding is_pinned: {e}")
        else:
            print("'is_pinned' already exists.")
            
        conn.commit()
        print("Database schema update completed.")

if __name__ == "__main__":
    update_db_schema()
