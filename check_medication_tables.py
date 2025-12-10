"""
Quick Database Check
====================
Kiểm tra xem bảng medication đã được tạo chưa.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect
from src.config.config import Config

print("🔍 Checking database tables...")

try:
    # Kết nối trực tiếp đến database
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\n📊 Found {len(tables)} tables:")
    for table in sorted(tables):
        marker = "✅" if "Medication" in table else "  "
        print(f"{marker} {table}")
    
    # Kiểm tra medication tables
    if 'MedicationSchedules' in tables and 'MedicationLogs' in tables:
        print("\n✅ SUCCESS: Medication tables exist!")
    else:
        print("\n⚠️  Medication tables NOT found")
        print("   Run the server once to auto-create tables: python main.py")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
