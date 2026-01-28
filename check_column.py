
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import create_app
from src.models.base import db
from sqlalchemy import text

def check_column():
    app = create_app()
    with app.app_context():
        try:
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='HealthProfiles' 
                AND column_name='ai_analysis'
            """)
            result = db.session.execute(check_query).fetchone()
            if result:
                print("EXIST")
            else:
                print("NOT_EXIST")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    check_column()
