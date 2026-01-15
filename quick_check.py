"""
Quick check - Kiểm tra nhanh database config
"""
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

print("=" * 60)
print("⚡ QUICK DATABASE CHECK")
print("=" * 60)
print()

# Kiểm tra DATABASE_URL
database_url = os.environ.get('DATABASE_URL', '')

if database_url:
    print("✅ DATABASE_URL được tìm thấy trong .env")
    
    # Parse URL để hiển thị thông tin (ẩn password)
    if database_url.startswith('postgresql://'):
        print("✅ Database type: PostgreSQL")
        
        # Extract host
        try:
            # Format: postgresql://user:pass@host:port/dbname
            parts = database_url.split('@')
            if len(parts) > 1:
                host_part = parts[1].split('/')[0]
                print(f"🌐 Host: {host_part}")
                
                if 'render.com' in host_part:
                    print("☁️  Provider: Render (CLOUD DATABASE)")
                    print()
                    print("🎉 KẾT LUẬN: Website sẽ sử dụng database RENDER!")
                else:
                    print("🌐 Provider: Custom PostgreSQL server")
        except:
            print("⚠️  Không thể parse DATABASE_URL")
    else:
        print("⚠️  DATABASE_URL không phải PostgreSQL format")
else:
    print("❌ DATABASE_URL KHÔNG tìm thấy trong .env")
    print()
    print("⚠️  Website sẽ sử dụng SQLite (local database)")
    print()
    print("💡 Hướng dẫn fix:")
    print("   1. Tạo file .env trong thư mục gốc")
    print("   2. Thêm dòng:")
    print("      DATABASE_URL=postgresql://...")

print()
print("=" * 60)
