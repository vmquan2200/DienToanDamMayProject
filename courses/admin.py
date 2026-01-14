from django.contrib import admin
from .models import Course, Lesson  # ← Import models từ app courses
from .models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'created_at', 'is_read', 'is_replied']
    list_filter = ['created_at', 'is_read', 'is_replied']
    search_fields = ['name', 'email', 'message']
    readonly_fields = ['created_at']
    list_editable = ['is_read', 'is_replied']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Thông tin liên hệ', {
            'fields': ('name', 'email', 'phone', 'message')
        }),
        ('Trạng thái', {
            'fields': ('is_read', 'is_replied', 'created_at')
        }),
    )

from .models import Review
# Đăng ký model Review với admin
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'course__title', 'comment']
    readonly_fields = ['created_at']


from .models import ForumPost, PostLike, PostComment
# Đăng ký model ForumPost với admin
@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at', 'is_pinned', 'like_count']
    list_filter = ['created_at', 'is_pinned', 'author']
    search_fields = ['title', 'content', 'author__username']
    list_editable = ['is_pinned']
    
    def like_count(self, obj):
        return obj.postlike_set.count()
# Đăng ký model PostLike với admin
@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'created_at', 'short_content']
    list_filter = ['created_at', 'author']
    search_fields = ['content', 'author__username', 'post__title']
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content


from .models import LearningPath, WeeklySchedule, DailyTask
from .models import LearningPathEnrollment
# Đăng ký model LearningPath, WeeklySchedule, DailyTask với admin
class DailyTaskInline(admin.TabularInline):
    model = DailyTask
    extra = 1

class WeeklyScheduleInline(admin.TabularInline):
    model = WeeklySchedule
    extra = 1
    inlines = [DailyTaskInline]

@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ['course', 'total_weeks', 'hours_per_week', 'difficulty']
    inlines = [WeeklyScheduleInline]
    list_filter = ['difficulty', 'total_weeks']

@admin.register(WeeklySchedule)
class WeeklyScheduleAdmin(admin.ModelAdmin):
    list_display = ['learning_path', 'week_number', 'title', 'total_hours']
    list_filter = ['learning_path']
    inlines = [DailyTaskInline]

@admin.register(DailyTask)
class DailyTaskAdmin(admin.ModelAdmin):
    list_display = ['weekly_schedule', 'day_number', 'title', 'duration_minutes', 'is_completed', 'attachment_link']
    list_filter = ['weekly_schedule', 'is_completed']
    list_editable = ['is_completed']
    readonly_fields = ['attachment_preview']
    fields = ('weekly_schedule', 'day_number', 'title', 'description', 'duration_minutes', 'resources', 'attachment', 'attachment_preview', 'is_completed')

    def attachment_link(self, obj):
        if obj.attachment:
            return f"<a href='{obj.attachment.url}' target='_blank'>Tải</a>"
        return ''
    attachment_link.allow_tags = True
    attachment_link.short_description = 'Tệp'

    def attachment_preview(self, obj):
        if obj.attachment:
            return f"<a href='{obj.attachment.url}' target='_blank'>{obj.attachment.name}</a>"
        return '(Không có)'
    attachment_preview.allow_tags = True
    attachment_preview.short_description = 'Tệp đính kèm'


@admin.register(LearningPathEnrollment)
class LearningPathEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'learning_path', 'status', 'start_date', 'end_date', 'assigned_by', 'created_at']
    list_filter = ['status', 'start_date']
    search_fields = ['user__username', 'learning_path__course__title', 'assigned_by__username']
    readonly_fields = ['created_at']


from .models import Payment, Cart
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from datetime import date

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'course', 'amount', 'status', 'payment_method', 'transaction_id', 'created_at', 'approved_info']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__username', 'user__email', 'course__title', 'transaction_id']
    readonly_fields = ['created_at', 'approved_at', 'approved_by']
    date_hierarchy = 'created_at'
    actions = ['approve_payments', 'reject_payments']
    list_per_page = 25
    
    def approved_info(self, obj):
        if obj.approved_at:
            approved_by_name = obj.approved_by.username if obj.approved_by else 'N/A'
            return f"{obj.approved_at.strftime('%d/%m/%Y %H:%M')} by {approved_by_name}"
        return '-'
    approved_info.short_description = 'Xác nhận bởi'
    
    fieldsets = (
        ('Thông tin thanh toán', {
            'fields': ('user', 'course', 'amount', 'payment_method', 'transaction_id', 'status')
        }),
        ('Xác nhận', {
            'fields': ('approved_at', 'approved_by'),
            'classes': ('collapse',)
        }),
        ('Thời gian', {
            'fields': ('created_at',)
        }),
    )
    
    def approve_payments(self, request, queryset):
        """Approve selected payments and grant course access to users"""
        approved_count = 0
        failed_count = 0
        
        for payment in queryset.filter(status='pending'):
            try:
                # Update payment status
                payment.status = 'completed'
                payment.approved_at = timezone.now()
                payment.approved_by = request.user
                payment.save()
                
                # Create LearningPathEnrollment
                from .models import LearningPath, WeeklySchedule, DailyTask, Lesson, LearningPathEnrollment
                
                course = payment.course
                user = payment.user
                
                # Ensure LearningPath exists
                learning_path, lp_created = LearningPath.objects.get_or_create(
                    course=course,
                    defaults={
                        'total_weeks': 4,
                        'hours_per_week': 5,
                        'difficulty': 'beginner'
                    }
                )
                
                # Create weekly schedules if they don't exist
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
                    
                    # Distribute lessons across weeks
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
                        # No lessons: create placeholder tasks
                        for ws in weekly_objs:
                            DailyTask.objects.create(
                                weekly_schedule=ws,
                                day_number=1,
                                title=f'Bài học tuần {ws.week_number}',
                                description='Nội dung học tập và video hướng dẫn',
                                duration_minutes=60,
                                resources=''
                            )
                
                # Create or update enrollment
                enrollment, created_en = LearningPathEnrollment.objects.get_or_create(
                    user=user,
                    learning_path=learning_path,
                    defaults={
                        'assigned_by': request.user,
                        'start_date': date.today(),
                        'status': 'active'
                    }
                )
                if not created_en:
                    if enrollment.status != 'active':
                        enrollment.status = 'active'
                    if not enrollment.start_date:
                        enrollment.start_date = date.today()
                    enrollment.assigned_by = request.user
                    enrollment.save()
                
                # Remove from cart if exists
                Cart.objects.filter(user=user, course=course).delete()
                
                # Send email to user
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
                    # Log error but don't fail the approval
                    print(f"Error sending email to {user.email}: {e}")
                
                approved_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Error approving payment {payment.id}: {e}")
        
        if approved_count > 0:
            self.message_user(
                request,
                f'Đã xác nhận {approved_count} thanh toán thành công. Khóa học đã được cấp cho học viên.',
                messages.SUCCESS
            )
        if failed_count > 0:
            self.message_user(
                request,
                f'Có {failed_count} thanh toán không thể xác nhận. Vui lòng kiểm tra lại.',
                messages.ERROR
            )
    
    approve_payments.short_description = 'Xác nhận thanh toán đã chọn'
    
    def reject_payments(self, request, queryset):
        """Reject selected payments"""
        updated = queryset.filter(status='pending').update(
            status='failed',
            approved_at=timezone.now(),
            approved_by=request.user
        )
        self.message_user(
            request,
            f'Đã từ chối {updated} thanh toán.',
            messages.WARNING
        )
    
    reject_payments.short_description = 'Từ chối thanh toán đã chọn'

# Đăng ký model Course với admin
admin.site.register(Course)

# Đăng ký model Lesson với admin  
admin.site.register(Lesson)
