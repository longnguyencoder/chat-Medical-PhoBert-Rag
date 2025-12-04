"""
Database migration script to add summary column to Conversations table.

Run this script once to update your existing database:
    python add_summary_column.py
"""

from src import create_app, db

def add_summary_column():
    app = create_app()
    
    with app.app_context():
        try:
            # Check if column already exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('Conversations')]
            
            if 'summary' in columns:
                print("✓ Column 'summary' already exists in Conversations table")
                return
            
            # Add column using raw SQL
            db.engine.execute(
                'ALTER TABLE "Conversations" ADD COLUMN summary TEXT;'
            )
            
            print("✅ Successfully added 'summary' column to Conversations table")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("\nIf the column already exists, you can ignore this error.")

if __name__ == "__main__":
    print("Adding 'summary' column to Conversations table...")
    add_summary_column()
