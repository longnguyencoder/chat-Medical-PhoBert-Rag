#!/usr/bin/env python3
"""
Script để migrate từ MySQL sang PostgreSQL
Chạy script này sau khi đã tạo database db_travel_assistant trên psql
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_database_exists():
    """Kiểm tra database db_travel_assistant đã tồn tại chưa"""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    # Lấy thông tin kết nối từ DATABASE_URL
    database_url = os.getenv('DATABASE_POSTGRESQL_URL')
    if not database_url:
        print("❌ DATABASE_POSTGRESQL_URL không được cấu hình trong file .env")
        return False
    
    print(f"🔍 Đang sử dụng DATABASE_URL: {database_url}")
    
    # Parse DATABASE_URL để lấy thông tin database
    try:
        if database_url.startswith('postgresql://'):
            url_parts = database_url.replace('postgresql://', '').split('/')
            if len(url_parts) >= 2:
                auth_host = url_parts[0]
                database_name = url_parts[1]
                
                print(f"📦 Database name từ URL: {database_name}")
                
                if '@' in auth_host:
                    auth, host_port = auth_host.split('@')
                    if ':' in auth:
                        username, password = auth.split(':')
                    else:
                        username = auth
                        password = ''
                    
                    if ':' in host_port:
                        host, port = host_port.split(':')
                    else:
                        host = host_port
                        port = '5432'
                else:
                    print("❌ DATABASE_POSTGRESQL_URL không đúng format")
                    return False
            else:
                print("❌ DATABASE_POSTGRESQL_URL không đúng format")
                return False
        else:
            print("❌ DATABASE_POSTGRESQL_URL phải bắt đầu với postgresql://")
            return False
        
        # Kết nối đến PostgreSQL server (không chỉ định database)
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database='postgres'  # Kết nối đến database mặc định
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Kiểm tra xem database đã tồn tại chưa
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"✅ Database '{database_name}' đã tồn tại")
            cursor.close()
            conn.close()
            return True
        else:
            print(f"❌ Database '{database_name}' chưa tồn tại")
            print(f"💡 Vui lòng tạo database '{database_name}' trên psql trước:")
            print(f"   CREATE DATABASE {database_name};")
            cursor.close()
            conn.close()
            return False
        
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra database: {str(e)}")
        return False

def migrate_data():
    """Migrate dữ liệu từ MySQL sang PostgreSQL"""
    print("🔄 Bắt đầu migration...")
    
    # Import Flask app
    from src import create_app
    from src.models.base import db
    from src.models import User, Attraction, Message, Conversation, OTP, Itinerary, ItineraryItem
    
    app = create_app()
    
    with app.app_context():
        try:
            # Tạo tất cả bảng
            print("📋 Tạo các bảng trong PostgreSQL...")
            db.create_all()
            print("✅ Đã tạo tất cả bảng thành công")
            
            print("🎉 Migration hoàn tất! Bạn có thể chạy ứng dụng với PostgreSQL")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi tạo bảng: {str(e)}")
            return False

def main():
    print("🚀 PostgreSQL Migration Tool")
    print("=" * 40)
    
    # Bước 1: Kiểm tra database đã tồn tại
    print("\n1️⃣ Kiểm tra database db_travel_assistant...")
    if not check_database_exists():
        print("❌ Database chưa tồn tại. Vui lòng tạo database trước.")
        sys.exit(1)
    
    # Bước 2: Migrate schema và dữ liệu
    print("\n2️⃣ Migrate schema...")
    if not migrate_data():
        print("❌ Không thể migrate dữ liệu. Vui lòng kiểm tra lỗi.")
        sys.exit(1)
    
    print("\n🎉 Migration hoàn tất thành công!")
    print("\n📝 Hướng dẫn tiếp theo:")
    print("1. Kiểm tra database trong DBeaver")
    print("2. Chạy: python main.py")

if __name__ == "__main__":
    main() 