import os
import sys
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def add_conversation_columns():
    """Add is_archived and is_pinned columns to Conversations table"""
    
    db_url = os.getenv('DATABASE_POSTGRESQL_URL')
    
    if not db_url:
        print("❌ ERROR: DATABASE_POSTGRESQL_URL not found in .env file")
        return False
    
    print("=" * 60)
    print("Adding Missing Columns to Conversations Table")
    print("=" * 60)
    
    try:
        # Connect to database
        print("\nConnecting to PostgreSQL...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        print("✅ Connected successfully")
        
        # Check if columns already exist
        print("\nChecking existing columns...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'Conversations' 
            AND column_name IN ('is_archived', 'is_pinned');
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        columns_to_add = []
        if 'is_archived' not in existing_columns:
            columns_to_add.append('is_archived')
        else:
            print("  ℹ️  Column 'is_archived' already exists")
            
        if 'is_pinned' not in existing_columns:
            columns_to_add.append('is_pinned')
        else:
            print("  ℹ️  Column 'is_pinned' already exists")
        
        if not columns_to_add:
            print("\n✅ All columns already exist. No migration needed.")
            cursor.close()
            conn.close()
            return True
        
        # Add missing columns
        print(f"\nAdding columns: {', '.join(columns_to_add)}")
        
        for column in columns_to_add:
            sql = f'ALTER TABLE "Conversations" ADD COLUMN {column} BOOLEAN DEFAULT FALSE;'
            print(f"  Executing: {sql}")
            cursor.execute(sql)
            print(f"  ✅ Added column '{column}'")
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Verify columns were added
        print("\nVerifying columns...")
        cursor.execute("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'Conversations' 
            AND column_name IN ('is_archived', 'is_pinned')
            ORDER BY column_name;
        """)
        
        results = cursor.fetchall()
        print("\nCurrent columns:")
        for row in results:
            print(f"  - {row[0]}: {row[1]}, default={row[2]}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Migration successful!")
        print("=" * 60)
        print("\n⚠️  IMPORTANT: Restart your server for changes to take effect")
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Database Error:")
        print(f"   {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected Error:")
        print(f"   {type(e).__name__}: {str(e)}")
        return False
    
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    success = add_conversation_columns()
    sys.exit(0 if success else 1)
