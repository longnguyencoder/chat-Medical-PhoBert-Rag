"""
Database Migration Script - Add is_admin column to Users table
================================================================

Mục đích:
- Thêm cột is_admin vào bảng Users để phân quyền admin
- Tạo một admin user mặc định để test

Cách chạy:
1. Đảm bảo server đang KHÔNG chạy
2. Chạy: python add_admin_column.py
3. Khởi động lại server

Lưu ý:
- Script này sẽ tự động thêm cột is_admin nếu chưa có
- Tạo admin user với email: admin@medical.com / password: admin123
"""

from src import create_app
from src.models.base import db
from src.models.user import User
from werkzeug.security import generate_password_hash
from sqlalchemy import text

def add_admin_column():
    """Thêm cột is_admin vào bảng Users"""
    app = create_app()
    
    with app.app_context():
        try:
            # Kiểm tra xem cột is_admin đã tồn tại chưa
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('Users')]
            
            if 'is_admin' not in columns:
                print("📝 Thêm cột is_admin vào bảng Users...")
                
                # Thêm cột is_admin với giá trị mặc định là False
                with db.engine.connect() as conn:
                    # PostgreSQL syntax
                    conn.execute(text('ALTER TABLE "Users" ADD COLUMN is_admin BOOLEAN DEFAULT FALSE'))
                    conn.commit()
                
                print("✅ Đã thêm cột is_admin thành công!")
            else:
                print("ℹ️  Cột is_admin đã tồn tại, bỏ qua bước này.")
            
            # Tạo admin user mặc định
            create_default_admin()
            
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            db.session.rollback()

def create_default_admin():
    """Tạo admin user mặc định"""
    try:
        # Kiểm tra xem admin đã tồn tại chưa
        admin = User.query.filter_by(email='admin@medical.com').first()
        
        if not admin:
            print("👤 Tạo admin user mặc định...")
            
            admin = User(
                full_name='Administrator',
                email='admin@medical.com',
                password_hash=generate_password_hash('admin123'),
                is_verified=True,
                is_admin=True,
                language_preference='vi'
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Đã tạo admin user:")
            print("   📧 Email: admin@medical.com")
            print("   🔑 Password: admin123")
            print("   ⚠️  Hãy đổi password sau khi đăng nhập!")
        else:
            # Cập nhật is_admin = True cho admin hiện tại
            if not admin.is_admin:
                print("🔄 Cập nhật quyền admin cho user admin@medical.com...")
                admin.is_admin = True
                db.session.commit()
                print("✅ Đã cập nhật quyền admin!")
            else:
                print("ℹ️  Admin user đã tồn tại.")
    
    except Exception as e:
        print(f"❌ Lỗi khi tạo admin: {e}")
        db.session.rollback()

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 MIGRATION: Thêm cột is_admin và tạo admin user")
    print("=" * 60)
    add_admin_column()
    print("=" * 60)
    print("✅ Migration hoàn tất!")
    print("💡 Bây giờ bạn có thể khởi động server và đăng nhập với:")
    print("   Email: admin@medical.com")
    print("   Password: admin123")
    print("=" * 60)
