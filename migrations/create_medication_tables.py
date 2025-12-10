"""
Simple Database Migration - Create Medication Tables
====================================================
Script đơn giản để tạo bảng medication.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("🔄 Starting migration...")

try:
    from src import create_app
    from src.models.base import db
    
    print("✅ Imported modules successfully")
    
    app = create_app()
    print("✅ Created Flask app")
    
    with app.app_context():
        print("🔄 Creating tables...")
        db.create_all()
        print("✅ Tables created!")
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\n📊 Database tables ({len(tables)}):")
        for table in sorted(tables):
            print(f"   - {table}")
        
        if 'MedicationSchedules' in tables and 'MedicationLogs' in tables:
            print("\n✅ SUCCESS: Medication tables created!")
        else:
            print("\n⚠️  WARNING: Medication tables not found")
            
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
