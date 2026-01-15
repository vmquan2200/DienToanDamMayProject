"""
Script kiểm tra kết nối database
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mycourse.settings')
django.setup()

from django.db import connection
from django.conf import settings

def check_database():
    """Kiểm tra database connection và thông tin"""
    print("=" * 60)
    print("🔍 KIỂM TRA DATABASE CONNECTION")
    print("=" * 60)
    print()
    
    # Lấy thông tin database
    db_config = settings.DATABASES['default']
    
    print("📋 Thông Tin Database:")
    print(f"   Engine: {db_config['ENGINE']}")
    print(f"   Name: {db_config.get('NAME', 'N/A')}")
    print(f"   Host: {db_config.get('HOST', 'N/A')}")
    print(f"   Port: {db_config.get('PORT', 'N/A')}")
    print(f"   User: {db_config.get('USER', 'N/A')}")
    print()
    
    # Xác định loại database
    if 'postgresql' in db_config['ENGINE']:
        db_type = "PostgreSQL"
        is_cloud = db_config.get('HOST', '') != ''
        print(f"💾 Loại Database: {db_type}")
        if is_cloud:
            print(f"☁️  Cloud Database: YES")
            if 'render.com' in db_config.get('HOST', ''):
                print(f"🌐 Provider: Render")
        else:
            print(f"💻 Local Database")
    elif 'sqlite' in db_config['ENGINE']:
        db_type = "SQLite"
        print(f"💾 Loại Database: {db_type}")
        print(f"💻 Local Database File")
    else:
        db_type = "Unknown"
        print(f"💾 Loại Database: {db_type}")
    
    print()
    print("-" * 60)
    
    # Test kết nối
    print("🔌 Testing Connection...")
    try:
        connection.ensure_connection()
        cursor = connection.cursor()
        
        # Lấy version database
        if 'postgresql' in db_config['ENGINE']:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Kết nối THÀNH CÔNG!")
            print(f"📦 PostgreSQL Version: {version.split(',')[0]}")
        elif 'sqlite' in db_config['ENGINE']:
            cursor.execute("SELECT sqlite_version();")
            version = cursor.fetchone()[0]
            print(f"✅ Kết nối THÀNH CÔNG!")
            print(f"📦 SQLite Version: {version}")
        else:
            print(f"✅ Kết nối THÀNH CÔNG!")
        
        # Đếm số bảng trong database
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """ if 'postgresql' in db_config['ENGINE'] else """
            SELECT COUNT(*) 
            FROM sqlite_master 
            WHERE type='table'
        """)
        table_count = cursor.fetchone()[0]
        print(f"📊 Số bảng trong database: {table_count}")
        
        # Kiểm tra một số bảng Django cơ bản
        try:
            from django.contrib.auth.models import User
            user_count = User.objects.count()
            print(f"👥 Số users trong hệ thống: {user_count}")
        except Exception as e:
            print(f"⚠️  Chưa có bảng User (chưa migrate?)")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ LỖI KẾT NỐI!")
        print(f"   Chi tiết: {e}")
        print()
        print("💡 Gợi ý:")
        print("   - Kiểm tra file .env có đúng DATABASE_URL không")
        print("   - Kiểm tra database Render còn hoạt động không")
        print("   - Kiểm tra internet connection")
        return False
    
    print()
    print("=" * 60)
    
    # Kết luận
    if 'postgresql' in db_config['ENGINE'] and 'render.com' in db_config.get('HOST', ''):
        print("✅ WEBSITE ĐANG SỬ DỤNG DATABASE RENDER (CLOUD)")
    elif 'postgresql' in db_config['ENGINE']:
        print("✅ WEBSITE ĐANG SỬ DỤNG POSTGRESQL")
    elif 'sqlite' in db_config['ENGINE']:
        print("⚠️  WEBSITE ĐANG SỬ DỤNG SQLITE (LOCAL)")
        print("    Database URL chưa được cấu hình hoặc file .env chưa đúng")
    
    print("=" * 60)
    return True

if __name__ == '__main__':
    check_database()
