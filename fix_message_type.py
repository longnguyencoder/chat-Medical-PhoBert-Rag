"""
Fix Database: Update message_type from 'audio' to 'voice'
==========================================================
Script này sửa lỗi enum trong database bằng cách update
tất cả messages có message_type='audio' thành 'voice'
"""

from src import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Update tất cả messages có message_type='audio' thành 'voice'
        result = db.session.execute(
            text("UPDATE messages SET message_type = 'voice' WHERE message_type = 'audio'")
        )
        
        rows_updated = result.rowcount
        db.session.commit()
        
        print(f"✅ Success! Updated {rows_updated} messages from 'audio' to 'voice'")
        print(f"   Database is now fixed!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")
        print(f"   Please check database connection")
