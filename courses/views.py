from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, get_user_model, logout
from django.db.models import Sum, Avg, Count, Q, F
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.core.signing import dumps, loads, BadSignature, SignatureExpired
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
import qrcode
import io
import base64
import os
from allauth.account.models import EmailConfirmation
from .models import (
    Course, Cart, Payment, Review, Contact, LearningPathEnrollment,
    LearningPath, WeeklySchedule, DailyTask, ForumPost, PostLike, PostComment
)
from .forms import ReviewForm

def home(request):
    category = request.GET.get('category', '')
    sort = request.GET.get('sort', 'newest')

    # Lấy danh sách khóa học với annotate cho các meta cần thiết
    courses = Course.objects.all().annotate(
        enrollment_count=Count('payment', filter=Q(payment__status='completed')),
        average_rating=Avg('review__rating')
    )
    if category:
        courses = courses.filter(category=category)

    # Áp dụng sắp xếp
    if sort == 'popular':
        courses = courses.order_by('-enrollment_count', '-created_at')
    elif sort == 'price_asc':
        courses = courses.order_by('price')
    elif sort == 'price_desc':
        courses = courses.order_by('-price')
    elif sort == 'rating':
        courses = courses.order_by('-average_rating', '-created_at')
    else:
        courses = courses.order_by('-created_at')
    # Paginate courses (9 per page)
    page_number = request.GET.get('page', 1)
    paginator = Paginator(courses, 9)
    courses = paginator.get_page(page_number)
    
    # Đếm số khóa học theo danh mục
    category_counts = {
        'all_count': Course.objects.count(),
        'python_count': Course.objects.filter(category='python').count(),
        'django_count': Course.objects.filter(category='django').count(),
        'web_count': Course.objects.filter(category='web').count(),
        'data_count': Course.objects.filter(category='data').count(),
    }
    
    # Danh sách danh mục cho template
    course_categories = Course.CATEGORY_CHOICES

    return render(request, 'courses/course_list.html', {
        'courses': courses,
        'selected_category': category,
        'course_categories': course_categories,
        'sort': sort,
        **category_counts  # Truyền tất cả counts vào template
    })

@login_required
def add_to_cart(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Kiểm tra xem request có phải AJAX không
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Kiểm tra nếu khóa học đã có trong giỏ
    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        course=course
    )
    
    if is_ajax:
        # Nếu là AJAX request, trả về JSON
        if created:
            return JsonResponse({
                'success': True,
                'message': f'Đã thêm "{course.title}" vào giỏ hàng!',
                'cart_count': Cart.objects.filter(user=request.user).count()
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f'"{course.title}" đã có trong giỏ hàng!',
                'cart_count': Cart.objects.filter(user=request.user).count()
            })
    else:
        # Nếu là request bình thường, giữ nguyên logic cũ
        if created:
            messages.success(request, f'Đã thêm "{course.title}" vào giỏ hàng!')
        else:
            messages.info(request, f'"{course.title}" đã có trong giỏ hàng!')
        
        return redirect('course_list')

@login_required
# Xem giỏ hàng
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    return render(request, 'courses/cart.html', {'cart_items': cart_items})

# Tìm kiếm khóa học
def search_courses(request):
    query = request.GET.get('q', '')
    if query:
        courses = Course.objects.filter(title__icontains=query) | Course.objects.filter(description__icontains=query)
    else:
        courses = Course.objects.all()
    
    return render(request, 'courses/search_results.html', {
        'courses': courses,
        'query': query
    })


@login_required
def payment_success(request):
    return render(request, 'courses/payment_success.html')

@login_required
# Trang tổng quan người dùng
def dashboard(request):
    enrolled_courses = Course.objects.filter(
        id__in=Cart.objects.filter(user=request.user).values('course_id')
    )
    
    return render(request, 'courses/dashboard.html', {
        'enrolled_courses': enrolled_courses
    })


@login_required
# Thanh toán trực tiếp một khóa học, xóa các khóa học khác trong giỏ
def checkout_direct(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Xóa tất cả items trong giỏ hàng trước đó
    Cart.objects.filter(user=request.user).delete()
    
    # Thêm khóa học vào giỏ hàng
    Cart.objects.create(user=request.user, course=course)
    
    # Chuyển hướng đến trang thanh toán
    return redirect('checkout')

@login_required
# Thanh toán các khóa học trong giỏ
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    
    if not cart_items.exists():
        messages.warning(request, 'Giỏ hàng của bạn đang trống!')
        return redirect('course_list')
    
    total_amount = sum(item.course.price for item in cart_items)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        # Nếu người dùng chọn MoMo hoặc chuyển khoản, hiển thị trang hướng dẫn thanh toán
        if payment_method in ('momo', 'banking'):
            return render(request, 'courses/payment_course.html', {
                'cart_items': cart_items,
                'total_amount': total_amount,
                'payment_method': payment_method,
            })

        # Với COD hoặc các phương thức khác, thực hiện thanh toán ngay lập tức (hiện tại giữ logic cũ)
        for item in cart_items:
            Payment.objects.create(
                user=request.user,
                course=item.course,
                amount=item.course.price,
                payment_method=payment_method,
                status='completed'
            )

        # Xóa giỏ hàng sau khi thanh toán
        cart_items.delete()

        messages.success(request, 'Thanh toán thành công! Bạn đã sở hữu khóa học.')
        return redirect('my_courses')
    
    return render(request, 'courses/checkout.html', {
        'cart_items': cart_items,
        'total_amount': total_amount
    })


@login_required
# Tạo QR code cho thanh toán MoMo
def generate_qr_code(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Tạo nội dung QR code (có thể thay bằng API MoMo thực tế)
    qr_content = f"Thanh toán MoMo\nKhóa học: {course.title}\nSố tiền: {course.price} VNĐ\nNgười nhận: Học Lập Trình\nSĐT: 0909123456"
    
    # Tạo QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    
    # Tạo image từ QR code
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Chuyển image thành base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return JsonResponse({'qr_code': qr_base64})


@login_required
def payment_course_view(request):
    """Render the payment instruction page for MoMo or banking via GET.
    This allows client-side redirects (GET) to show the QR/info page reliably.
    """
    payment_method = request.GET.get('method')
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, 'Giỏ hàng của bạn đang trống!')
        return redirect('course_list')

    total_amount = sum(item.course.price for item in cart_items)

    return render(request, 'courses/payment_course.html', {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'payment_method': payment_method,
    })


@login_required
def payment_confirm_view(request):
    """Handle user-confirmed payments from the `payment_course` page.
    
    User submits payment with transaction_id, system creates Payment records
    with status='pending' for admin to review and approve.
    """
    if request.method != 'POST':
        return redirect('payment_course')

    payment_method = request.POST.get('payment_method') or 'unknown'
    transaction_id = request.POST.get('transaction_id', '').strip()

    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, 'Giỏ hàng của bạn đang trống!')
        return redirect('course_list')

    # Validate transaction_id for MoMo and Banking
    if payment_method in ('momo', 'banking') and not transaction_id:
        messages.error(request, 'Vui lòng nhập mã giao dịch!')
        return redirect('payment_course')

    # Create Payment records with status='pending' for admin approval
    created_payments = []
    for item in cart_items:
        payment = Payment.objects.create(
            user=request.user,
            course=item.course,
            amount=item.course.price,
            payment_method=payment_method,
            status='pending',
            transaction_id=transaction_id if transaction_id else None,
        )
        created_payments.append(payment)

    # Remove cart items after creating pending payments
    cart_items.delete()

    messages.success(
        request, 
        f'Đã gửi yêu cầu thanh toán cho {len(created_payments)} khóa học. '
        'Vui lòng chờ admin xác nhận. Bạn sẽ nhận được email khi thanh toán được xác nhận.'
    )
    return redirect('my_courses')


def activate_payment(request, token):
    try:
        data = loads(token, salt='payment-activation', max_age=60 * 60 * 24)  # 24 hours
    except SignatureExpired:
        messages.error(request, 'Liên kết kích hoạt đã hết hạn. Vui lòng thử lại.')
        return redirect('checkout')
    except BadSignature:
        messages.error(request, 'Liên kết kích hoạt không hợp lệ.')
        return redirect('checkout')

    user_pk = data.get('user')
    course_ids = data.get('courses', [])
    payment_method = data.get('payment_method', 'unknown')

    try:
        target_user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        messages.error(request, 'Người dùng không tồn tại.')
        return redirect('checkout')

    # Create Payment records (avoid duplicates)
    from datetime import date as _date
    from .models import LearningPath, WeeklySchedule, DailyTask, Lesson, LearningPathEnrollment

    for cid in course_ids:
        try:
            course = Course.objects.get(pk=cid)
        except Course.DoesNotExist:
            continue

        payment, created = Payment.objects.get_or_create(
            user=target_user,
            course=course,
            defaults={
                'amount': course.price,
                'payment_method': payment_method,
                'status': 'completed'
            }
        )

        # Ensure a LearningPath exists for the course
        lp, lp_created = LearningPath.objects.get_or_create(
            course=course,
            defaults={
                'total_weeks': 4,
                'hours_per_week': 5,
                'difficulty': 'beginner'
            }
        )

        # If there are no weekly schedules, try to generate them from Lesson entries
        if not WeeklySchedule.objects.filter(learning_path=lp).exists():
            lessons = Lesson.objects.filter(course=course).order_by('order')
            total_weeks = lp.total_weeks or 4

            # Create weekly containers
            weekly_objs = []
            for w in range(1, total_weeks + 1):
                ws = WeeklySchedule.objects.create(
                    learning_path=lp,
                    week_number=w,
                    title=f'Tuần {w}',
                    objectives=f'Nội dung tuần {w}',
                    total_hours=lp.hours_per_week or 5
                )
                weekly_objs.append(ws)

            # Distribute lessons across weeks roughly evenly
            if lessons.exists():
                n = lessons.count()
                per_week = max(1, n // total_weeks)
                extra = n % total_weeks
                it = iter(lessons)
                for i, ws in enumerate(weekly_objs, start=1):
                    count_this_week = per_week + (1 if i <= extra else 0)
                    for dnum in range(1, count_this_week + 1):
                        try:
                            lesson = next(it)
                        except StopIteration:
                            break
                        DailyTask.objects.create(
                            weekly_schedule=ws,
                            day_number=dnum,
                            title=lesson.title,
                            description=f'Bài học: {lesson.title}',
                            duration_minutes=60,
                            resources=lesson.video_url or ''
                        )
            else:
                # No lessons: create a placeholder task per week
                for ws in weekly_objs:
                    DailyTask.objects.create(
                        weekly_schedule=ws,
                        day_number=1,
                        title=f'Bài học tuần {ws.week_number}',
                        description='Nội dung học tập và video hướng dẫn',
                        duration_minutes=60,
                        resources=''
                    )

        # Create or update enrollment for the user
        enrollment, created_en = LearningPathEnrollment.objects.get_or_create(
            user=target_user,
            learning_path=lp,
            defaults={
                'assigned_by': None,
                'start_date': _date.today(),
                'status': 'active'
            }
        )
        if not created_en:
            # If enrollment exists but inactive, activate and set start_date if missing
            if enrollment.status != 'active':
                enrollment.status = 'active'
            if not enrollment.start_date:
                enrollment.start_date = _date.today()
            enrollment.save()

    # Remove related cart items for that user
    Cart.objects.filter(user=target_user, course__id__in=course_ids).delete()

    messages.success(request, 'Thanh toán đã được xác nhận và khóa học đã được kích hoạt. Lộ trình học đã sẵn sàng.')
    return redirect('my_courses')


@login_required
# Thêm đánh giá cho khóa học
def add_review(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        Review.objects.create(
            user=request.user,
            course=course,
            rating=rating,
            comment=comment
        )
        
        messages.success(request, 'Cảm ơn bạn đã đánh giá khóa học!')
        return redirect('course_detail', course_id=course_id)
    
    return redirect('course_detail', course_id=course_id)

@staff_member_required
def admin_dashboard(request):
    pending_payments = Payment.objects.filter(status='pending').select_related('user', 'course').order_by('-created_at')
    
    stats = {
        'total_courses': Course.objects.count(),
        'total_users': User.objects.count(),
        'total_sales': Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_orders': Payment.objects.count(),
        'pending_orders': pending_payments.count(),
    }
    
    return render(request, 'courses/admin_dashboard.html', {
        'stats': stats,
        'pending_payments': pending_payments,
        'today': timezone.now()
    })

@staff_member_required
def admin_approve_payment(request, payment_id):
    if request.method != 'POST':
        return redirect('admin_dashboard')
        
    payment = get_object_or_404(Payment, id=payment_id, status='pending')
    
    try:
        # 1. Cập nhật trạng thái thanh toán
        payment.status = 'completed'
        payment.approved_at = timezone.now()
        payment.approved_by = request.user
        payment.save()
        
        # 2. Kích hoạt lộ trình học tập
        from .models import LearningPath, WeeklySchedule, DailyTask, Lesson, LearningPathEnrollment
        from datetime import date as _date
        
        course = payment.course
        user = payment.user
        
        # Đảm bảo LearningPath tồn tại
        learning_path, lp_created = LearningPath.objects.get_or_create(
            course=course,
            defaults={
                'total_weeks': 4,
                'hours_per_week': 5,
                'difficulty': 'beginner'
            }
        )
        
        # Tạo lịch trình hàng tuần nếu chưa có
        if not WeeklySchedule.objects.filter(learning_path=learning_path).exists():
            lessons = Lesson.objects.filter(course=course).order_by('order')
            total_weeks = learning_path.total_weeks or 4
            
            weekly_objs = []
            for w in range(1, total_weeks + 1):
                ws = WeeklySchedule.objects.create(
                    learning_path=learning_path,
                    week_number=w,
                    title=f'Tuần {w}',
                    objectives=f'Nội dung tuần {w}',
                    total_hours=learning_path.hours_per_week or 5
                )
                weekly_objs.append(ws)
            
            # Phân bổ bài học vào các tuần
            if lessons.exists():
                n = lessons.count()
                per_week = max(1, n // total_weeks)
                extra = n % total_weeks
                it = iter(lessons)
                for i, ws in enumerate(weekly_objs, start=1):
                    count_this_week = per_week + (1 if i <= extra else 0)
                    for dnum in range(1, count_this_week + 1):
                        try:
                            lesson = next(it)
                        except StopIteration:
                            break
                        DailyTask.objects.create(
                            weekly_schedule=ws,
                            day_number=dnum,
                            title=lesson.title,
                            description=f'Bài học: {lesson.title}',
                            duration_minutes=60,
                            resources=lesson.video_url or ''
                        )
            else:
                for ws in weekly_objs:
                    DailyTask.objects.create(
                        weekly_schedule=ws,
                        day_number=1,
                        title=f'Bài học tuần {ws.week_number}',
                        description='Nội dung học tập và video hướng dẫn',
                        duration_minutes=60,
                        resources=''
                    )
        
        # 3. Tạo ghi danh (Enrollment)
        enrollment, created_en = LearningPathEnrollment.objects.get_or_create(
            user=user,
            learning_path=learning_path,
            defaults={
                'assigned_by': request.user,
                'start_date': _date.today(),
                'status': 'active'
            }
        )
        if not created_en:
            enrollment.status = 'active'
            if not enrollment.start_date:
                enrollment.start_date = _date.today()
            enrollment.assigned_by = request.user
            enrollment.save()
        
        # 4. Gửi email thông báo
        try:
            course_list_url = request.build_absolute_uri(reverse('my_courses'))
            subject = '✅ Thanh toán đã được xác nhận - Khóa học đã được kích hoạt'
            message = f'''
Xin chào {user.get_full_name() or user.username}!

Thanh toán của bạn cho khóa học "{course.title}" đã được xác nhận thành công.

📚 THÔNG TIN KHÓA HỌC:
• Tên khóa học: {course.title}
• Số tiền: {payment.amount:,.0f} VNĐ
• Phương thức: {payment.get_payment_method_display()}
• Mã giao dịch: {payment.transaction_id or 'N/A'}
• Thời gian xác nhận: {payment.approved_at.strftime('%d/%m/%Y %H:%M')}

🎉 Khóa học đã được kích hoạt và sẵn sàng để bạn bắt đầu học!

Bạn có thể truy cập khóa học tại: {course_list_url}

Chúc bạn học tập hiệu quả!

Trân trọng,
Đội ngũ Học Lập Trình
            '''
            send_mail(
                subject,
                message.strip(),
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error sending email: {e}")
            
        messages.success(request, f'Đã duyệt thanh toán #{payment.id} thành công!')
    except Exception as e:
        messages.error(request, f'Lỗi khi duyệt thanh toán: {str(e)}')
        
    return redirect('admin_dashboard')

@staff_member_required
def admin_reject_payment(request, payment_id):
    if request.method != 'POST':
        return redirect('admin_dashboard')
        
    payment = get_object_or_404(Payment, id=payment_id, status='pending')
    payment.status = 'failed'
    payment.save()
    
    messages.warning(request, f'Đã từ chối thanh toán #{payment.id}.')
    return redirect('admin_dashboard')

# Trang About
def about(request):
    return render(request, 'courses/about.html')

def handler404(request, exception):
    return render(request, 'courses/404.html', status=404)

def handler500(request):
    return render(request, 'courses/500.html', status=500)


def dev_login(request):
    """Development-only helper: log in the `EMAIL_HOST_USER` account when visited with correct token.
    Usage: /dev-login/?token=THE_TOKEN
    Token should be set in .env as DEV_LOGIN_TOKEN. Only works when DEBUG=True.
    """
    if not settings.DEBUG:
        return HttpResponseForbidden('Not allowed')
    token = request.GET.get('token')
    expected = os.environ.get('DEV_LOGIN_TOKEN')
    if not expected or token != expected:
        return HttpResponseForbidden('Invalid token')
    user = get_user_model().objects.filter(email__iexact=settings.EMAIL_HOST_USER).first()
    if not user:
        return HttpResponseNotFound('User not found')
    # When logging in programmatically, Django's login expects the user to
    # have a 'backend' attribute. Set it to the first configured backend.
    backend = None
    try:
        backend = settings.AUTHENTICATION_BACKENDS[0]
    except Exception:
        backend = 'django.contrib.auth.backends.ModelBackend'
    setattr(user, 'backend', backend)
    auth_login(request, user)
    return redirect('/')


def dev_confirm_and_login(request, key=None):
    """Development-only helper: confirm an EmailConfirmation by key and log the user in.
    Usage: /dev-confirm/<key>/
    Only works when `DEBUG=True`.
    This is a dev helper to allow end-to-end testing of email confirmation + auto-login.
    """
    # Only allow dev confirm when DEBUG + explicit env flag enabled
    if not (getattr(settings, 'DEBUG', False) and getattr(settings, 'DEV_AUTO_LOGIN_ON_CONFIRM', False)):
        return HttpResponseForbidden('Not allowed')
    if key is None:
        key = request.GET.get('key') or request.GET.get('token')
    if not key:
        return HttpResponseNotFound('No key provided')

    # Some allauth versions use keyed lookup differently; query directly by key
    from allauth.account.models import EmailConfirmation as _EC
    conf = _EC.objects.filter(key=key).first()
    if not conf:
        return HttpResponseNotFound('Confirmation not found')

    # Ensure sent timestamp exists so allauth treats it as valid
    if not conf.sent:
        conf.sent = timezone.now()
        conf.save()

    try:
        # Confirm via allauth (requires request)
        conf.confirm(request)
    except Exception:
        # Fallback: mark the email verified directly
        conf.email_address.verified = True
        conf.email_address.save()

    user = conf.email_address.user
    backend = None
    try:
        backend = settings.AUTHENTICATION_BACKENDS[0]
    except Exception:
        backend = 'django.contrib.auth.backends.ModelBackend'
    setattr(user, 'backend', backend)
    auth_login(request, user)
    return redirect('/my-dashboard/')

# Trang Contact với form và gửi email
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Validation
        errors = []
        if not name:
            errors.append('Vui lòng nhập họ tên')
        if not email:
            errors.append('Vui lòng nhập email')
        elif '@' not in email:
            errors.append('Email không hợp lệ')
        if not message:
            errors.append('Vui lòng nhập nội dung')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'courses/contact.html', {
                'name': name,
                'email': email,
                'phone': phone,
                'message': message
            })
        
        # Lưu vào database
        contact_entry = Contact.objects.create(
            name=name,
            email=email,
            phone=phone if phone else None,
            message=message
        )
        
        # Gửi email thông báo cho ADMIN (bất đồng bộ)
        try:
            admin_subject = f'📧 LIÊN HỆ MỚI: {name} - #{contact_entry.id}'
            admin_message = f"""
            THÔNG TIN LIÊN HỆ MỚI 🎯

            👤 Họ tên: {name}
            📧 Email: {email}
            📞 Số điện thoại: {phone if phone else 'Chưa cung cấp'}
            🆔 Mã liên hệ: #{contact_entry.id}
            📅 Thời gian: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}

            📝 NỘI DUNG:
            {message}

            —
            Hệ thống Học Lập Trình
            """

            send_mail(
                admin_subject,
                admin_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],  # Gửi cho admin
                fail_silently=True,
            )
            
        except Exception as e:
            print(f"⚠️ Lỗi gửi email cho admin: {e}")

        # Gửi email xác nhận cho NGƯỜI DÙNG (bất đồng bộ)
        try:
            user_subject = '✅ Cảm ơn bạn đã liên hệ với Học Lập Trình!'
            user_message = f"""
            Xin chào {name}! 👋

            Cảm ơn bạn đã liên hệ với Học Lập Trình. Chúng tôi đã nhận được tin nhắn của bạn và sẽ phản hồi trong thời gian sớm nhất (thường trong vòng 24h).

            📋 THÔNG TIN LIÊN HỆ CỦA BẠN:
            • Họ tên: {name}
            • Email: {email}
            • Số điện thoại: {phone if phone else 'Không có'}
            • Mã liên hệ: #{contact_entry.id}
            • Thời gian: {timezone.now().strftime('%d/%m/%Y %H:%M')}

            📝 NỘI DUNG BẠN GỬI:
            {message}

            🔍 TRẠNG THÁI: Đã tiếp nhận ✅

            💬 Chúng tôi sẽ liên hệ lại với bạn sớm nhất có thể. 
            Nếu cần hỗ trợ khẩn cấp, vui lòng gọi hotline: 0909 123 456

            Trân trọng,
            Đội ngũ Học Lập Trình 🚀
            📧 vult8073@ut.edu.vn
            🌐 https://hoclaptrinh.ut.edu.vn
            """

            send_mail(
                user_subject,
                user_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],  # Gửi cho người dùng
                fail_silently=True,
            )
            
        except Exception as e:
            print(f"⚠️ Lỗi gửi email xác nhận: {e}")

        messages.success(request, '✅ Cảm ơn bạn đã liên hệ! Chúng tôi đã gửi email xác nhận và sẽ phản hồi sớm nhất.')
        return redirect('contact')
    
    return render(request, 'courses/contact.html')

@login_required
# Trang tổng quan người dùng
def user_dashboard(request):
    try:
        # Lấy các khóa học đã mua
        purchased_courses = Course.objects.filter(
            payment__user=request.user, 
            payment__status='completed'
        ).distinct()
        
        # Lấy các khóa học trong giỏ hàng
        cart_courses = Course.objects.filter(
            cart__user=request.user
        )
        
        # Lấy lịch sử thanh toán
        payment_history = Payment.objects.filter(
            user=request.user
        ).select_related('course').order_by('-created_at')[:10]
        
        # Lấy bài viết forum của user
        user_posts = ForumPost.objects.filter(
            author=request.user
        ).order_by('-created_at')[:5]
        
        # Lấy reviews của user
        user_reviews = Review.objects.filter(
            user=request.user
        ).select_related('course').order_by('-created_at')[:5]
        
        # Thống kê cá nhân
        user_stats = {
            'total_courses': purchased_courses.count(),
            'total_spent': Payment.objects.filter(
                user=request.user, 
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
            'courses_in_cart': cart_courses.count(),
            'total_posts': ForumPost.objects.filter(author=request.user).count(),
            'total_reviews': Review.objects.filter(user=request.user).count(),
        }
        
        # Lấy enrollments (lộ trình được gán)
        enrollments = LearningPathEnrollment.objects.filter(
            user=request.user
        ).select_related('learning_path__course', 'assigned_by')

        return render(request, 'courses/user_dashboard.html', {
            'purchased_courses': purchased_courses,
            'cart_courses': cart_courses,
            'payment_history': payment_history,
            'user_posts': user_posts,
            'user_reviews': user_reviews,
            'user_stats': user_stats,
            'enrollments': enrollments,
        })
    except Exception as e:
        # Log error và hiển thị trang lỗi
        import traceback
        print(f"Error in user_dashboard: {e}")
        print(traceback.format_exc())
        messages.error(request, f'Có lỗi xảy ra: {str(e)}')
        return redirect('course_list')


@login_required
def my_courses(request):
    # Lấy các khóa học đã thanh toán thành công
    paid_courses = Course.objects.filter(
        payment__user=request.user, 
        payment__status='completed'
    ).distinct()
    
    return render(request, 'courses/my_courses.html', {'courses': paid_courses})

@login_required
def my_schedule(request, enrollment_id):
    from .models import LearningPathEnrollment, WeeklySchedule, DailyTask
    from datetime import timedelta
    enrollment = get_object_or_404(LearningPathEnrollment, id=enrollment_id)

    # chỉ owner hoặc staff được xem
    if enrollment.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden('Không có quyền truy cập')

    lp = enrollment.learning_path

    # Lấy ngày bắt đầu — nếu không có, dùng ngày hôm nay
    start = enrollment.start_date
    if not start:
        from datetime import date
        start = date.today()

    # Xây dựng map ngày -> list of tasks
    schedule_map = {}
    for week in WeeklySchedule.objects.filter(learning_path=lp).prefetch_related('days'):
        for day in week.days.all():
            # tính ngày: start + (week_number-1)*7 + (day_number-1)
            day_offset = (week.week_number - 1) * 7 + (day.day_number - 1)
            event_date = start + timedelta(days=day_offset)
            key = event_date.isoformat()
            if key not in schedule_map:
                schedule_map[key] = []
            schedule_map[key].append({
                'week_number': week.week_number,
                'day_number': day.day_number,
                'title': day.title,
                'description': day.description,
            })

    # Sort keys
    ordered = dict(sorted(schedule_map.items()))

    return render(request, 'courses/schedule.html', {
        'enrollment': enrollment,
        'schedule': ordered,
    })

# Đăng xuất người dùng
def custom_logout(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Đã đăng xuất thành công!')
        return redirect('course_list')
    return redirect('course_list')

# Tạo view chi tiết khóa học với hiển thị đánh giá và form đánh giá
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    reviews = Review.objects.filter(course=course).order_by('-created_at')
    
    # Kiểm tra user đã mua khóa học chưa
    user_has_purchased = False
    if request.user.is_authenticated:
        user_has_purchased = Payment.objects.filter(
            user=request.user, 
            course=course, 
            status='completed'
        ).exists()
        # Nếu admin đã gán learning path cho user, cũng coi là có quyền truy cập
        if not user_has_purchased:
            from .models import LearningPathEnrollment
            user_has_purchased = LearningPathEnrollment.objects.filter(
                user=request.user,
                learning_path__course=course,
                status='active'
            ).exists()
    
    # Kiểm tra user đã review chưa
    user_review = None
    if request.user.is_authenticated:
        try:
            user_review = Review.objects.get(user=request.user, course=course)
        except Review.DoesNotExist:
            user_review = None
    
    # Xử lý form review
    if request.method == 'POST' and request.user.is_authenticated and user_has_purchased:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.course = course
            review.save()
            messages.success(request, 'Cảm ơn bạn đã đánh giá khóa học!')
            return redirect('course_detail', course_id=course_id)
    else:
        form = ReviewForm()
    
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'reviews': reviews,
        'user_has_purchased': user_has_purchased,
        'user_review': user_review,
        'form': form,
        'average_rating': reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
        'total_reviews': reviews.count()
    })



@login_required
# Gửi đánh giá qua AJAX
def submit_review(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        
        # Kiểm tra user đã mua khóa học chưa
        has_purchased = Payment.objects.filter(
            user=request.user, 
            course=course, 
            status='completed'
        ).exists()
        
        if not has_purchased:
            return JsonResponse({'success': False, 'error': 'Bạn cần mua khóa học trước khi đánh giá'})
        
        # Kiểm tra đã review chưa
        if Review.objects.filter(user=request.user, course=course).exists():
            return JsonResponse({'success': False, 'error': 'Bạn đã đánh giá khóa học này rồi'})
        
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            Review.objects.create(
                user=request.user,
                course=course,
                rating=rating,
                comment=comment
            )
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'Vui lòng điền đầy đủ thông tin'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# Danh sách bài viết diễn đàn với tìm kiếm và lọc tags
def forum_list(request):
    search_query = request.GET.get('q', '')
    tag_filter = request.GET.get('tag', '')
    sort = request.GET.get('sort', 'new')
    
    posts = ForumPost.objects.annotate(
        like_count=Count('postlike'),
        comment_count=Count('comments')
    )
    
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    if tag_filter:
        posts = posts.filter(tags__icontains=tag_filter)

    # Sorting: new (latest), popular (most likes), comments (most commented)
    if sort == 'popular':
        posts = posts.order_by('-like_count', '-created_at')
    elif sort == 'comments':
        posts = posts.order_by('-comment_count', '-created_at')
    else:
        posts = posts.order_by('-created_at')
    
    # Lấy danh sách tags phổ biến
    popular_tags = ForumPost.objects.exclude(tags__isnull=True).exclude(tags__exact='')\
        .values_list('tags', flat=True)
    
    # Community stats for hero
    total_posts = ForumPost.objects.count()
    total_comments = PostComment.objects.count()
    active_users = User.objects.count()

    return render(request, 'courses/forum_list.html', {
        'posts': posts,
        'search_query': search_query,
        'tag_filter': tag_filter,
        'popular_tags': popular_tags,
        'sort': sort,
        'total_posts': total_posts,
        'total_comments': total_comments,
        'active_users': active_users
    })


def forum_tag(request, tag):
    posts = ForumPost.objects.annotate(
        like_count=Count('postlike'),
        comment_count=Count('comments')
    ).filter(tags__icontains=tag)

    popular_tags = ForumPost.objects.exclude(tags__isnull=True).exclude(tags__exact='')\
        .values_list('tags', flat=True)

    return render(request, 'courses/forum_list.html', {
        'posts': posts,
        'search_query': '',
        'tag_filter': tag,
        'popular_tags': popular_tags
    })


def recent_activity(request):
    """Return recent activity (posts and comments) as JSON for polling updates."""
    # Get recent posts and comments
    recent_posts = list(ForumPost.objects.all().order_by('-created_at')[:10].values(
        'id', 'author__username', 'title', 'created_at'))
    recent_comments = list(PostComment.objects.all().order_by('-created_at')[:10].values(
        'id', 'author__username', 'post_id', 'content', 'created_at'))

    # Normalize and merge
    events = []
    for p in recent_posts:
        events.append({
            'type': 'post',
            'id': p['id'],
            'user': p['author__username'],
            'title': p['title'],
            'created_at': p['created_at'].isoformat()
        })
    for c in recent_comments:
        events.append({
            'type': 'comment',
            'id': c['id'],
            'user': c['author__username'],
            'post_id': c['post_id'],
            'content': c['content'][:140],
            'created_at': c['created_at'].isoformat()
        })

    # Sort by created_at desc and limit
    events_sorted = sorted(events, key=lambda e: e['created_at'], reverse=True)[:10]

    return JsonResponse({'events': events_sorted})


def user_profile(request, username):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = get_object_or_404(User, username=username)

    # User stats
    posts = ForumPost.objects.filter(author=user).annotate(
        like_count=Count('postlike'),
        comment_count=Count('comments')
    ).order_by('-created_at')

    author_posts_count = posts.count()
    author_comments_count = PostComment.objects.filter(author=user).count()

    return render(request, 'courses/user_profile.html', {
        'profile_user': user,
        'posts': posts,
        'author_posts_count': author_posts_count,
        'author_comments_count': author_comments_count
    })


@login_required
def forum_toggle_pin(request, post_id):
    if request.method != 'POST':
        return HttpResponse(status=405)

    post = get_object_or_404(ForumPost, id=post_id)
    if not request.user.is_staff:
        return HttpResponse(status=403)

    post.is_pinned = not bool(post.is_pinned)
    post.save()
    messages.success(request, 'Đã cập nhật trạng thái ghim bài viết.')
    return redirect('forum_detail', post_id=post.id)


@login_required
def forum_toggle_feature(request, post_id):
    if request.method != 'POST':
        return HttpResponse(status=405)

    post = get_object_or_404(ForumPost, id=post_id)
    if not request.user.is_staff:
        return HttpResponse(status=403)

    post.is_featured = not bool(post.is_featured)
    post.save()
    messages.success(request, 'Đã cập nhật trạng thái nổi bật của bài viết.')
    return redirect('forum_detail', post_id=post.id)

@login_required
def forum_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        tags = request.POST.get('tags', '')
        
        if title and content:
            post = ForumPost.objects.create(
                author=request.user,
                title=title,
                content=content,
                tags=tags
            )
            messages.success(request, 'Đã tạo bài viết thành công!')
            return redirect('forum_detail', post_id=post.id)
    
    return render(request, 'courses/forum_create.html')

def forum_detail(request, post_id):
    post = get_object_or_404(
        ForumPost.objects.annotate(
            like_count=Count('postlike'),
            comment_count=Count('comments')
        ), 
        id=post_id
    )
    
    # Kiểm tra user đã like chưa
    user_has_liked = False
    if request.user.is_authenticated:
        user_has_liked = PostLike.objects.filter(user=request.user, post=post).exists()

    # Tăng lượt xem (atomic) và tính các thông số động
    ForumPost.objects.filter(id=post.id).update(views=F('views') + 1)
    post.refresh_from_db(fields=['views'])

    # Paginate comments for the post (used by template's load-more)
    comments_qs = post.comments.all().order_by('created_at')
    page_number = request.GET.get('cpage', 1)
    paginator = Paginator(comments_qs, 5)
    comments_page = paginator.get_page(page_number)

    # Tổng số bình luận cho post (toàn bộ, không phải page)
    post_total_comments = comments_qs.count()

    # Ước lượng thời gian đọc (phút) dựa trên từ (khoảng 200 wpm)
    words = 0
    if post.content:
        words = len(post.content.split())
    reading_time = max(1, (words + 199) // 200)

    # Author stats
    author = post.author
    author_posts_count = ForumPost.objects.filter(author=author).count()
    author_comments_count = PostComment.objects.filter(author=author).count()

    # Related posts (simple heuristic: other posts ordered by comment & like)
    related_posts = ForumPost.objects.annotate(
        like_count=Count('postlike'),
        comment_count=Count('comments')
    ).exclude(id=post.id).order_by('-comment_count', '-like_count')[:5]

    # Community statistics (global)
    total_posts = ForumPost.objects.count()
    total_comments = PostComment.objects.count()
    total_users = User.objects.count()

    return render(request, 'courses/forum_detail.html', {
        'post': post,
        'comments': comments_page,
        'user_has_liked': user_has_liked,
        'like_count': post.like_count,
        'post_total_comments': post_total_comments,
        'total_posts': total_posts,
        'total_comments': total_comments,
        'total_users': total_users,
        'reading_time': reading_time,
        'author_posts_count': author_posts_count,
        'author_comments_count': author_comments_count,
        'related_posts': related_posts
    })

@login_required
def forum_edit(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id, author=request.user)
    
    if request.method == 'POST':
        post.title = request.POST.get('title', post.title)
        post.content = request.POST.get('content', post.content)
        post.tags = request.POST.get('tags', post.tags)
        post.save()
        messages.success(request, 'Đã cập nhật bài viết!')
        return redirect('forum_detail', post_id=post.id)
    
    return render(request, 'courses/forum_edit.html', {'post': post})

@login_required
def toggle_like(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(ForumPost, id=post_id)
        like, created = PostLike.objects.get_or_create(
            user=request.user,
            post=post
        )
        
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        
        like_count = PostLike.objects.filter(post=post).count()
        
        return JsonResponse({
            'liked': liked,
            'like_count': like_count
        })
    
    return JsonResponse({'error': 'Invalid request'})

@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(ForumPost, id=post_id)
        content = request.POST.get('content')
        
        if content:
            comment = PostComment.objects.create(
                author=request.user,
                post=post,
                content=content
            )
            
            return JsonResponse({
                'success': True,
                'comment': {
                    'author': comment.author.username,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M'),
                    'avatar': '👤'  # Có thể thay bằng avatar thật
                }
            })
    
    return JsonResponse({'success': False, 'error': 'Nội dung không được để trống'})


@login_required
# Xóa khóa học khỏi giỏ hàng
def remove_from_cart(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    cart_item = get_object_or_404(Cart, user=request.user, course=course)
    cart_item.delete()
    # Nếu là AJAX request trả về JSON, ngược lại redirect như trước
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': f'Đã xóa "{course.title}" khỏi giỏ hàng!',
            'cart_count': Cart.objects.filter(user=request.user).count()
        })

    messages.success(request, f'Đã xóa "{course.title}" khỏi giỏ hàng!')
    return redirect('view_cart')

@login_required
def forum_delete(request, post_id):
    if request.method != 'POST':
        return HttpResponse(status=405)

    post = get_object_or_404(ForumPost, id=post_id)
    # Allow only author or staff to delete
    if not (request.user == post.author or request.user.is_staff):
        return HttpResponseForbidden('Không có quyền xoá bài viết này')

    post.delete()
    messages.success(request, 'Đã xoá bài viết.')
    return redirect('forum_list')

@login_required
def learning_path(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Kiểm tra user đã mua khóa học chưa
    has_access = Payment.objects.filter(
        user=request.user, 
        course=course, 
        status='completed'
    ).exists() or LearningPathEnrollment.objects.filter(
        user=request.user,
        learning_path__course=course,
        status='active'
    ).exists()
    
    if not has_access:
        messages.error(request, 'Bạn cần mua khóa học để xem lộ trình học tập!')
        return redirect('course_detail', course_id=course_id)
    
    # Lấy learning path hoặc tạo mặc định
    learning_path, created = LearningPath.objects.get_or_create(
        course=course,
        defaults={
            'total_weeks': 4,
            'hours_per_week': 5,
            'difficulty': 'beginner'
        }
    )
    
    weekly_schedules = WeeklySchedule.objects.filter(learning_path=learning_path).prefetch_related('days')
    
    # Tính tổng tiến độ
    total_tasks = DailyTask.objects.filter(weekly_schedule__learning_path=learning_path).count()
    completed_tasks = DailyTask.objects.filter(
        weekly_schedule__learning_path=learning_path,
        is_completed=True
    ).count()
    
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Tính tuần hiện tại dựa trên ngày bắt đầu nếu user có enrollment,
    # nếu user mua khóa học thì cho full access (current_week = total_weeks)
    from datetime import date
    current_week = 1
    enrollment = None
    if request.user.is_authenticated:
        # check enrollment start_date
        try:
            enrollment = LearningPathEnrollment.objects.filter(
                user=request.user,
                learning_path=learning_path,
                status='active'
            ).order_by('-created_at').first()
        except Exception:
            enrollment = None

        has_payment = Payment.objects.filter(user=request.user, course=course, status='completed').exists()
        if has_payment:
            current_week = learning_path.total_weeks
            # If user has paid but admin hasn't created an enrollment, create one now
            if not enrollment:
                try:
                    from datetime import date as _date
                    enrollment = LearningPathEnrollment.objects.create(
                        user=request.user,
                        learning_path=learning_path,
                        assigned_by=None,
                        start_date=_date.today(),
                        status='active'
                    )
                except Exception:
                    enrollment = None
        elif enrollment and enrollment.start_date:
            days = (date.today() - enrollment.start_date).days
            week = days // 7 + 1
            current_week = max(1, min(learning_path.total_weeks, week))
        else:
            current_week = 1

    return render(request, 'courses/learning_path.html', {
        'course': course,
        'learning_path': learning_path,
        'weekly_schedules': weekly_schedules,
        'progress': progress,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'current_week': current_week,
        'enrollment': enrollment,
    })

@login_required
def toggle_task_completion(request, task_id):
    task = get_object_or_404(DailyTask, id=task_id)
    
    # Kiểm tra quyền truy cập
    has_access = Payment.objects.filter(
        user=request.user, 
        course=task.weekly_schedule.learning_path.course, 
        status='completed'
    ).exists()
    
    if not has_access:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    task.is_completed = not task.is_completed
    task.save()
    
    return JsonResponse({
        'success': True, 
        'is_completed': task.is_completed,
        'task_id': task.id
    })


@staff_member_required
def admin_learning_path_assign(request):
    from django.contrib.auth.models import User
    enrollments = LearningPathEnrollment.objects.select_related('user', 'learning_path', 'assigned_by').all()
    users = User.objects.filter(is_active=True).order_by('username')
    learning_paths = LearningPath.objects.select_related('course').all()

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        lp_id = request.POST.get('learning_path_id')
        start_date = request.POST.get('start_date') or None
        end_date = request.POST.get('end_date') or None

        try:
            user = User.objects.get(id=user_id)
            lp = LearningPath.objects.get(id=lp_id)
        except Exception:
            messages.error(request, 'Dữ liệu không hợp lệ.')
            return redirect('admin_learning_path_assign')

        enrollment, created = LearningPathEnrollment.objects.get_or_create(
            user=user,
            learning_path=lp,
            defaults={
                'assigned_by': request.user,
                'start_date': start_date,
                'end_date': end_date,
            }
        )

        if not created:
            messages.info(request, 'Học viên đã được gán lộ trình này.')
        else:
            messages.success(request, 'Đã gán lộ trình cho học viên.')

        return redirect('admin_learning_path_assign')

    return render(request, 'courses/admin_learning_path_assign.html', {
        'enrollments': enrollments,
        'users': users,
        'learning_paths': learning_paths,
    })