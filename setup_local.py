"""
Script hỗ trợ setup môi trường local và kiểm tra cấu hình
"""
import os
import sys
from pathlib import Path

def check_env_file():
    """Kiểm tra file .env"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ Không tìm thấy file .env")
        print("📝 Hãy tạo file .env với nội dung sau:")
        print("\nDJANGO_SECRET_KEY=your-secret-key-here")
        print("DJANGO_DEBUG=True")
        print("DATABASE_URL=postgresql://...")
        return False
    else:
        print("✅ File .env đã tồn tại")
        return True

def check_database_url():
    """Kiểm tra DATABASE_URL"""
    from dotenv import load_dotenv
    load_dotenv()
    
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url:
        print("✅ DATABASE_URL đã được cấu hình")
        # Không hiển thị password
        safe_url = db_url.split('@')[1] if '@' in db_url else 'unknown'
        print(f"   Host: {safe_url}")
    else:
        print("⚠️  DATABASE_URL chưa được cấu hình")
        print("   Sẽ sử dụng SQLite làm database mặc định")

def check_packages():
    """Kiểm tra các package cần thiết"""
    required_packages = [
        'django',
        'psycopg2',
        'dj_database_url',
        'dotenv',
    ]
    
    print("\n📦 Kiểm tra packages:")
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Chưa cài đặt")

def main():
    print("=" * 50)
    print("🚀 KIỂM TRA CẤU HÌNH DJANGO PROJECT")
    print("=" * 50)
    print()
    
    # Kiểm tra .env
    has_env = check_env_file()
    print()
    
    # Kiểm tra database URL
    if has_env:
        check_database_url()
    print()
    
    # Kiểm tra packages
    check_packages()
    print()
    
    print("=" * 50)
    print("📖 HƯỚNG DẪN TIẾP THEO:")
    print("=" * 50)
    print()
    print("1. Cài đặt packages (nếu chưa):")
    print("   pip install -r requirements.txt")
    print()
    print("2. Chạy migrations:")
    print("   python manage.py migrate")
    print()
    print("3. Tạo superuser:")
    print("   python manage.py createsuperuser")
    print()
    print("4. Collect static files:")
    print("   python manage.py collectstatic")
    print()
    print("5. Chạy development server:")
    print("   python manage.py runserver")
    print()
    print("📄 Xem PYTHONANYWHERE_DEPLOYMENT.md để triển khai lên PythonAnywhere")
    print()

if __name__ == '__main__':
    main()
