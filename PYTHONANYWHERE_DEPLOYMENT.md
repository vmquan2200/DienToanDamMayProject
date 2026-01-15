# Hướng Dẫn Triển Khai Django lên PythonAnywhere với PostgreSQL Render

## Thông Tin Database
- **Database Provider**: Render (Singapore)
- **Database Type**: PostgreSQL
- **Connection URL**: `postgresql://dbname_7i27_user:PTtnGQFClEI0WLmlSomo4lz5d15BDlwm@dpg-d5j1422dbo4c73eflolg-a.singapore-postgres.render.com/dbname_7i27`

---

## Bước 1: Tạo Tài Khoản PythonAnywhere

1. Truy cập https://www.pythonanywhere.com
2. Đăng ký tài khoản miễn phí
3. Ghi nhớ username của bạn (ví dụ: `vmquan2200` hoặc `elonmust`)

---

## Bước 2: Upload Code lên PythonAnywhere

### Cách 1: Sử dụng Git (Khuyến nghị)

1. Mở **Bash Console** trên PythonAnywhere
2. Clone repository của bạn:

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### Cách 2: Upload File Zip

1. Nén toàn bộ project thành file zip
2. Vào **Files** tab trên PythonAnywhere
3. Upload file zip và giải nén

---

## Bước 3: Cài Đặt Virtual Environment

Trong **Bash Console**:

```bash
# Di chuyển vào thư mục project
cd ~/DienToanDamMayProject

# Tạo virtual environment
mkvirtualenv --python=/usr/bin/python3.10 myproject-env

# Kích hoạt virtual environment
workon myproject-env

# Cài đặt các package
pip install -r requirements.txt
```

**Lưu ý**: Nếu gặp lỗi với `psycopg2-binary`, hãy thử:
```bash
pip install psycopg2-binary --no-cache-dir
```

---

## Bước 4: Tạo File .env

Tạo file `.env` trong thư mục project:

```bash
nano .env
```

Thêm nội dung sau:

```env
DJANGO_SECRET_KEY=your-super-secret-key-here-change-this
DJANGO_DEBUG=False
DATABASE_URL=postgresql://dbname_7i27_user:PTtnGQFClEI0WLmlSomo4lz5d15BDlwm@dpg-d5j1422dbo4c73eflolg-a.singapore-postgres.render.com/dbname_7i27
```

**Quan trọng**: Thay đổi `DJANGO_SECRET_KEY` thành một chuỗi bí mật của riêng bạn!

Lưu file: `Ctrl + O`, `Enter`, `Ctrl + X`

---

## Bước 5: Migrate Database

```bash
# Đảm bảo virtual environment đang được kích hoạt
workon myproject-env

# Chuyển đến thư mục project
cd ~/DienToanDamMayProject

# Chạy migrations
python manage.py migrate

# Tạo superuser (admin)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

---

## Bước 6: Cấu Hình Web App trên PythonAnywhere

1. Vào tab **Web** trên PythonAnywhere
2. Click **Add a new web app**
3. Chọn **Manual configuration**
4. Chọn **Python 3.10**

### Cấu hình các phần sau:

#### A. Source Code
```
/home/your-username/DienToanDamMayProject
```

#### B. Working Directory
```
/home/your-username/DienToanDamMayProject
```

#### C. Virtualenv
```
/home/your-username/.virtualenvs/myproject-env
```

#### D. WSGI Configuration File

Click vào link **WSGI configuration file**, xóa toàn bộ nội dung và thay bằng:

```python
import os
import sys
from dotenv import load_dotenv

# Thêm đường dẫn project vào sys.path
path = '/home/your-username/DienToanDamMayProject'
if path not in sys.path:
    sys.path.insert(0, path)

# Load environment variables từ .env
load_dotenv(os.path.join(path, '.env'))

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'mycourse.settings'

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Lưu ý**: Thay `your-username` bằng username PythonAnywhere của bạn!

---

## Bước 7: Cấu Hình Static Files

Trong tab **Web**, kéo xuống phần **Static files**:

| URL        | Directory                                          |
|------------|----------------------------------------------------|
| /static/   | /home/your-username/DienToanDamMayProject/staticfiles |
| /media/    | /home/your-username/DienToanDamMayProject/media       |

---

## Bước 8: Reload Web App

1. Kéo lên đầu trang trong tab **Web**
2. Click nút **Reload** màu xanh lá
3. Đợi vài giây để web app khởi động lại

---

## Bước 9: Kiểm Tra Website

1. Truy cập: `https://your-username.pythonanywhere.com`
2. Kiểm tra login/signup: `https://your-username.pythonanywhere.com/accounts/login/`
3. Kiểm tra admin: `https://your-username.pythonanywhere.com/admin/`

---

## Xử Lý Lỗi Thường Gặp

### Lỗi 1: DisallowedHost

**Giải pháp**: Thêm domain của bạn vào `ALLOWED_HOSTS` trong `settings.py`:

```python
ALLOWED_HOSTS = [
    'your-username.pythonanywhere.com',
    'localhost',
    '127.0.0.1',
]

CSRF_TRUSTED_ORIGINS = [
    'https://your-username.pythonanywhere.com',
]
```

### Lỗi 2: Static Files không hiển thị

**Giải pháp**:
```bash
workon myproject-env
cd ~/DienToanDamMayProject
python manage.py collectstatic --noinput
```

Sau đó reload web app.

### Lỗi 3: Database Connection Error

**Giải pháp**:
- Kiểm tra file `.env` có đúng DATABASE_URL không
- Kiểm tra database Render còn hoạt động không
- Thử ping database từ Bash Console:

```bash
nc -zv dpg-d5j1422dbo4c73eflolg-a.singapore-postgres.render.com 5432
```

### Lỗi 4: Internal Server Error (500)

**Giải pháp**:
1. Xem error log trong tab **Web** > **Log files** > **Error log**
2. Bật DEBUG tạm thời để xem lỗi chi tiết (nhớ tắt sau khi fix):
   - Sửa `.env`: `DJANGO_DEBUG=True`
   - Reload web app

---

## Cập Nhật Code

Khi có thay đổi code mới:

```bash
# Vào Bash Console
cd ~/DienToanDamMayProject

# Pull code mới (nếu dùng Git)
git pull origin main

# Kích hoạt virtual environment
workon myproject-env

# Cài đặt package mới (nếu có)
pip install -r requirements.txt

# Chạy migrations (nếu có thay đổi database)
python manage.py migrate

# Collect static files (nếu có thay đổi CSS/JS)
python manage.py collectstatic --noinput
```

Sau đó vào tab **Web** và click **Reload**.

---

## Bảo Mật

1. **KHÔNG** commit file `.env` vào Git
2. **BẮT BUỘC** thay đổi `SECRET_KEY` trong production
3. Luôn để `DEBUG=False` khi deploy
4. Sử dụng HTTPS (PythonAnywhere tự động cung cấp)
5. Định kỳ backup database Render

---

## Lưu Ý về Free Tier

### PythonAnywhere Free:
- 512MB disk space
- 1 web app
- Domain: `username.pythonanywhere.com`
- Phải reload web app sau 3 tháng không hoạt động

### Render PostgreSQL Free:
- 1GB storage
- 90 ngày free (sau đó phải nâng cấp hoặc migrate)
- Có thể bị ngủ nếu không có kết nối

---

## Hỗ Trợ

Nếu gặp vấn đề:
1. Kiểm tra error log trên PythonAnywhere
2. Kiểm tra database còn hoạt động trên Render Dashboard
3. Tham khảo: https://help.pythonanywhere.com/

---

## Checklist Triển Khai

- [ ] Tạo tài khoản PythonAnywhere
- [ ] Upload/Clone code lên server
- [ ] Tạo và kích hoạt virtual environment
- [ ] Cài đặt requirements.txt
- [ ] Tạo file .env với DATABASE_URL
- [ ] Chạy migrations
- [ ] Tạo superuser
- [ ] Collectstatic
- [ ] Cấu hình Web App
- [ ] Cấu hình WSGI file
- [ ] Cấu hình Static files mapping
- [ ] Reload web app
- [ ] Test website
- [ ] Test admin panel
- [ ] Test login/signup

---

**Chúc bạn deploy thành công! 🚀**
