from django.shortcuts import render, get_object_or_404
from .models import Course
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import Cart
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Course, Cart, Payment, Review
from django.shortcuts import redirect, get_object_or_404
import qrcode
import io
import base64
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Sum, Avg
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Contact

def home(request):
    category = request.GET.get('category', '')
    
    # Lấy danh sách khóa học
    if category:
        courses = Course.objects.filter(category=category)
    else:
        courses = Course.objects.all()
    
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
        **category_counts  # Truyền tất cả counts vào template
    })

def course_detail(request, course_id):
    # Lấy khóa học theo id, nếu không có thì show lỗi 404
    course = get_object_or_404(Course, id=course_id)
    
    # Kiểm tra user đã mua khóa học chưa
    user_has_purchased = False
    if request.user.is_authenticated:
        user_has_purchased = Payment.objects.filter(
            user=request.user, 
            course=course, 
            status='completed'
        ).exists()
    
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'courses/course_detail.html', {'course': course})


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Course, Cart

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
        
        # Tạo các bản ghi thanh toán
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

@login_required
# Trang tổng quan admin
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')
    
    stats = {
        'total_courses': Course.objects.count(),
        'total_users': User.objects.count(),
        'total_sales': Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_orders': Payment.objects.count(),
    }
    
    return render(request, 'courses/admin_dashboard.html', {'stats': stats})

# Trang About
def about(request):
    return render(request, 'courses/about.html')
# Trang Contact
def contact(request):
    if request.method == 'POST':
        # Xử lý form liên hệ (có thể lưu vào database hoặc gửi email)
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # Hiển thị thông báo thành công
        messages.success(request, 'Cảm ơn bạn đã liên hệ! Chúng tôi sẽ phản hồi sớm nhất.')
        return redirect('contact')
    
    return render(request, 'courses/contact.html')

def handler404(request, exception):
    return render(request, 'courses/404.html', status=404)

def handler500(request):
    return render(request, 'courses/500.html', status=500)

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
    
    return render(request, 'courses/user_dashboard.html', {
        'purchased_courses': purchased_courses,
        'cart_courses': cart_courses,
        'payment_history': payment_history,
        'user_posts': user_posts,
        'user_reviews': user_reviews,
        'user_stats': user_stats,
    })


@login_required
def my_courses(request):
    # Lấy các khóa học đã thanh toán thành công
    paid_courses = Course.objects.filter(
        payment__user=request.user, 
        payment__status='completed'
    ).distinct()
    
    return render(request, 'courses/my_courses.html', {'courses': paid_courses})


from django.contrib.auth import logout
from django.shortcuts import redirect

# Đăng xuất người dùng
def custom_logout(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Đã đăng xuất thành công!')
        return redirect('course_list')
    return redirect('course_list')



from .forms import ReviewForm
from .models import Review
from django.http import JsonResponse
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


from .models import ForumPost, PostLike, PostComment
from django.http import JsonResponse
from django.db.models import Count, Q
# Danh sách bài viết diễn đàn với tìm kiếm và lọc tags
def forum_list(request):
    search_query = request.GET.get('q', '')
    tag_filter = request.GET.get('tag', '')
    
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
    
    # Lấy danh sách tags phổ biến
    popular_tags = ForumPost.objects.exclude(tags__isnull=True).exclude(tags__exact='')\
        .values_list('tags', flat=True)
    
    return render(request, 'courses/forum_list.html', {
        'posts': posts,
        'search_query': search_query,
        'tag_filter': tag_filter,
        'popular_tags': popular_tags
    })

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
    
    return render(request, 'courses/forum_detail.html', {
        'post': post,
        'comments': post.comments.all(),
        'user_has_liked': user_has_liked,
        'like_count': post.like_count
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
    
    messages.success(request, f'Đã xóa "{course.title}" khỏi giỏ hàng!')
    return redirect('view_cart')


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Count, Sum
from .models import Course, Payment, Review, LearningPath, WeeklySchedule, DailyTask

@login_required
def learning_path(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Kiểm tra user đã mua khóa học chưa
    has_access = Payment.objects.filter(
        user=request.user, 
        course=course, 
        status='completed'
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
    
    return render(request, 'courses/learning_path.html', {
        'course': course,
        'learning_path': learning_path,
        'weekly_schedules': weekly_schedules,
        'progress': progress,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks
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