# 🚀 Hướng Dẫn Nhanh - Deploy lên PythonAnywhere

## Chuẩn Bị

### 1. Tạo file `.env` (QUAN TRỌNG!)

Tạo file `.env` trong thư mục gốc project với nội dung:

```env
DJANGO_SECRET_KEY=thay-doi-chuoi-bi-mat-nay
DJANGO_DEBUG=False
DATABASE_URL=postgresql://dbname_7i27_user:PTtnGQFClEI0WLmlSomo4lz5d15BDlwm@dpg-d5j1422dbo4c73eflolg-a.singapore-postgres.render.com/dbname_7i27
```

⚠️ **LƯU Ý**: Đổi `DJANGO_SECRET_KEY` thành chuỗi ngẫu nhiên của bạn!

### 2. Test Local (Tùy chọn)

```bash
# Cài packages
pip install -r requirements.txt

# Kiểm tra cấu hình
python setup_local.py

# Chạy migrations
python manage.py migrate

# Tạo admin user
python manage.py createsuperuser

# Test local
python manage.py runserver
```

---

## Deploy lên PythonAnywhere (5 Bước Chính)

### Bước 1: Upload Code

```bash
# Trong PythonAnywhere Bash Console
git clone <your-repo-url>
cd DienToanDamMayProject
```

### Bước 2: Setup Virtual Environment

```bash
mkvirtualenv --python=/usr/bin/python3.10 myproject-env
workon myproject-env
pip install -r requirements.txt
```

### Bước 3: Tạo File .env

```bash
nano .env
# Paste nội dung từ bước Chuẩn Bị
# Lưu: Ctrl+O, Enter, Ctrl+X
```

### Bước 4: Setup Database

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### Bước 5: Cấu Hình Web App

1. Vào tab **Web** > **Add a new web app**
2. Chọn **Manual configuration** > **Python 3.10**
3. Điền thông tin:
   - Source code: `/home/your-username/DienToanDamMayProject`
   - Working directory: `/home/your-username/DienToanDamMayProject`
   - Virtualenv: `/home/your-username/.virtualenvs/myproject-env`

4. Sửa **WSGI file** (thay `your-username`):

```python
import os
import sys
from dotenv import load_dotenv

path = '/home/your-username/DienToanDamMayProject'
if path not in sys.path:
    sys.path.insert(0, path)

load_dotenv(os.path.join(path, '.env'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'mycourse.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

5. Cấu hình **Static files**:
   - URL: `/static/` → Directory: `/home/your-username/DienToanDamMayProject/staticfiles`
   - URL: `/media/` → Directory: `/home/your-username/DienToanDamMayProject/media`

6. Click **Reload** ở đầu trang

---

## Kiểm Tra

- Website: `https://your-username.pythonanywhere.com`
- Admin: `https://your-username.pythonanywhere.com/admin/`
- Login: `https://your-username.pythonanywhere.com/accounts/login/`

---

## Xử Lý Lỗi

### Lỗi: DisallowedHost
Thêm domain vào `settings.py` → `ALLOWED_HOSTS`

### Lỗi: Static files không load
```bash
python manage.py collectstatic --noinput
```
Reload web app

### Lỗi: Database connection
Kiểm tra `.env` có đúng `DATABASE_URL` không

### Xem log lỗi
Tab **Web** > **Log files** > **Error log**

---

## Cập Nhật Code

```bash
cd ~/DienToanDamMayProject
git pull
workon myproject-env
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Sau đó **Reload** web app.

---

📖 **Chi tiết đầy đủ**: Xem file `PYTHONANYWHERE_DEPLOYMENT.md`

🔧 **Hỗ trợ**: https://help.pythonanywhere.com/
