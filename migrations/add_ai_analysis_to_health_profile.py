"""
Migration: Add AI Analysis field to HealthProfiles
===================================================
Thêm cột ai_analysis để lưu phân tích tự động từ AI.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import create_app
from src.models.base import db
from sqlalchemy import text

def add_ai_analysis_column():
    """Thêm cột ai_analysis vào bảng HealthProfiles"""
    app = create_app()
    
    with app.app_context():
        try:
            # Kiểm tra xem cột đã tồn tại chưa
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='HealthProfiles' 
                AND column_name='ai_analysis'
            """)
            
            result = db.session.execute(check_query).fetchone()
            
            if result:
                print("✓ Column 'ai_analysis' already exists in HealthProfiles table")
                return
            
            # Thêm cột mới
            print("Adding 'ai_analysis' column to HealthProfiles table...")
            
            alter_query = text("""
                ALTER TABLE "HealthProfiles"
                ADD COLUMN ai_analysis TEXT NULL
            """)
            
            db.session.execute(alter_query)
            db.session.commit()
            
            print("✓ Successfully added 'ai_analysis' column to HealthProfiles table")
            print("\nColumn details:")
            print("  - Name: ai_analysis")
            print("  - Type: TEXT")
            print("  - Nullable: TRUE")
            print("  - Purpose: Lưu phân tích sức khỏe tự động từ AI")
            
        except Exception as e:
            print(f"✗ Error adding column: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    print("="*60)
    print("MIGRATION: Add AI Analysis to Health Profiles")
    print("="*60)
    add_ai_analysis_column()
    print("="*60)
    print("Migration completed!")
    print("="*60)

