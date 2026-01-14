# Web Học Lập Trình - Django Project

Dự án web học lập trình được xây dựng bằng Django.

## Yêu cầu hệ thống

- Python 3.8 trở lên
- pip (Python package manager)

## Hướng dẫn cài đặt và chạy project

### Bước 1: Kiểm tra Python

Mở terminal/command prompt và kiểm tra phiên bản Python:

```bash
python --version
```

hoặc

```bash
python3 --version
```

Nếu chưa có Python, tải và cài đặt từ [python.org](https://www.python.org/downloads/)

### Bước 2: Tạo Virtual Environment (Khuyến nghị)

Tạo môi trường ảo để cô lập các package của project:

**Trên Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Trên Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Sau khi kích hoạt, bạn sẽ thấy `(venv)` ở đầu dòng lệnh.

### Bước 3: Cài đặt các thư viện cần thiết

Cài đặt tất cả các package từ file `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Bước 4: Tạo file .env (Tùy chọn)

Project sử dụng file `.env` để cấu hình các biến môi trường. Bạn có thể tạo file `.env` trong thư mục gốc với nội dung:

```
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
```

**Lưu ý:** Nếu không tạo file `.env`, project sẽ sử dụng các giá trị mặc định trong `settings.py`.

### Bước 5: Chạy migrations

Tạo và áp dụng các migration để tạo cấu trúc database:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Bước 6: Tạo superuser (Tùy chọn)

Tạo tài khoản admin để truy cập Django admin panel:

```bash
python manage.py createsuperuser
```

Nhập username, email và password khi được yêu cầu.

### Bước 7: Thu thập static files

Thu thập các file tĩnh (CSS, JS, images) vào thư mục `staticfiles`:

```bash
python manage.py collectstatic
```

Chọn `yes` khi được hỏi.

### Bước 8: Chạy server

Khởi động Django development server:

```bash
python manage.py runserver
```

Server sẽ chạy tại: **http://127.0.0.1:8000/**

### Bước 9: Truy cập ứng dụng

- **Trang chủ:** http://127.0.0.1:8000/
- **Admin panel:** http://127.0.0.1:8000/admin/
- **Đăng nhập:** http://127.0.0.1:8000/accounts/login/
- **Đăng ký:** http://127.0.0.1:8000/accounts/signup/

## Các lệnh hữu ích khác

### Chạy shell Django
```bash
python manage.py shell
```

### Tạo migration mới sau khi thay đổi models
```bash
python manage.py makemigrations
python manage.py migrate
```

### Xem danh sách các lệnh có sẵn
```bash
python manage.py help
```

### Chạy tests (nếu có)
```bash
python manage.py test
```

## Cấu trúc project

```
DienToanDamMayProject/
├── manage.py              # Django management script
├── requirements.txt       # Danh sách các package Python cần thiết
├── README.md             # File hướng dẫn này
├── mycourse/             # Django project settings
│   ├── settings.py       # Cấu hình chính
│   ├── urls.py           # URL routing chính
│   └── wsgi.py           # WSGI config
├── courses/              # Django app chính
│   ├── models.py         # Database models
│   ├── views.py          # Views/controllers
│   ├── urls.py           # URL routing của app
│   └── templates/        # HTML templates
└── staticfiles/          # Static files đã được collect
```

## Xử lý lỗi thường gặp

### Lỗi: "No module named 'django'"
- Đảm bảo đã cài đặt requirements: `pip install -r requirements.txt`
- Kiểm tra virtual environment đã được kích hoạt

### Lỗi: "ModuleNotFoundError"
- Cài đặt lại các package: `pip install -r requirements.txt`

### Lỗi: "Database is locked"
- Đóng các kết nối database khác
- Xóa file `db.sqlite3` và chạy lại migrations (sẽ mất dữ liệu)

### Lỗi: "Port 8000 already in use"
- Sử dụng port khác: `python manage.py runserver 8001`
- Hoặc tìm và đóng process đang sử dụng port 8000

## Lưu ý

- Project sử dụng SQLite database (file `db.sqlite3` sẽ được tạo tự động)
- Email backend được cấu hình là console (email sẽ hiển thị trong terminal)
- Static files đã được collect sẵn trong thư mục `staticfiles/`

## Hỗ trợ

Nếu gặp vấn đề, vui lòng kiểm tra:
1. Python version (cần 3.8+)
2. Đã cài đặt đầy đủ requirements
3. Virtual environment đã được kích hoạt
4. Database migrations đã được chạy
