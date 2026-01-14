from django.db import models
from django.contrib.auth.models import User

# Tạo model Khóa học
class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name="Tên khóa học")
    description = models.TextField(verbose_name="Mô tả")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    CATEGORY_CHOICES = [
        ('python', 'Python'),
        ('django', 'Django'),
        ('web', 'Web Development'),
        ('data', 'Data Science'),
        ('other', 'Khác'),
    ]
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other',
        verbose_name="Danh mục"
    )
    
    def __str__(self):
        return self.title

# Tạo model Bài học
class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="Khóa học")
    title = models.CharField(max_length=200, verbose_name="Tên bài học")
    video_url = models.URLField(verbose_name="Link video")
    order = models.IntegerField(verbose_name="Thứ tự")
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
 # Tạo model Giỏ hàng   
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')

# Tạo model Thanh toán
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Đang chờ'),
        ('completed', 'Thành công'),
        ('failed', 'Thất bại')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=[
        ('momo', 'MoMo'),
        ('banking', 'Chuyển khoản'),
        ('cod', 'Thanh toán khi nhận khóa học')
    ])
    transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Mã giao dịch")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian xác nhận")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payments', verbose_name="Người xác nhận")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Thanh toán"
        verbose_name_plural = "Thanh toán"
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} - {self.get_status_display()}"

    
# Tạo model Liên hệ
class Contact(models.Model):
    name = models.CharField(max_length=100, verbose_name="Họ tên")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Số điện thoại")
    message = models.TextField(verbose_name="Nội dung")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày gửi")
    is_read = models.BooleanField(default=False, verbose_name="Đã đọc")
    is_replied = models.BooleanField(default=False, verbose_name="Đã phản hồi")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Liên hệ"
        verbose_name_plural = "Liên hệ"
    
    def __str__(self):
        return f"{self.name} - {self.email} - {self.created_at.strftime('%d/%m/%Y')}"

# Tạo model Đánh giá khóa học
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Người dùng")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="Khóa học")
    rating = models.IntegerField(
        choices=[(1, '1 sao'), (2, '2 sao'), (3, '3 sao'), (4, '4 sao'), (5, '5 sao')],
        verbose_name="Đánh giá"
    )
    comment = models.TextField(verbose_name="Bình luận")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    
    class Meta:
        unique_together = ('user', 'course')  # Mỗi user chỉ review 1 lần
        ordering = ['-created_at']
        verbose_name = "Đánh giá"
        verbose_name_plural = "Đánh giá"
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} - {self.rating} sao"

# Tạo model Yêu thích khóa học
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'course')


# Tạo model Bài viết diễn đàn
class ForumPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Tác giả")
    title = models.CharField(max_length=200, verbose_name="Tiêu đề")
    content = models.TextField(verbose_name="Nội dung")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    tags = models.CharField(max_length=100, blank=True, verbose_name="Tags")
    is_pinned = models.BooleanField(default=False, verbose_name="Ghim bài")
    is_featured = models.BooleanField(default=False, verbose_name="Nổi bật")
    views = models.PositiveIntegerField(default=0, verbose_name="Lượt xem")
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = "Bài viết diễn đàn"
        verbose_name_plural = "Bài viết diễn đàn"
    
    def __str__(self):
        return f"{self.title} - {self.author.username}"

class PostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')
        verbose_name = "Like bài viết"
        verbose_name_plural = "Likes bài viết"

class PostComment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Tác giả")
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='comments', verbose_name="Bài viết")
    content = models.TextField(verbose_name="Nội dung")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Bình luận"
        verbose_name_plural = "Bình luận"
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"
    
# Tạo model Lộ trình học tập
class LearningPath(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='learning_path')
    total_weeks = models.IntegerField(default=4, verbose_name="Tổng số tuần")
    hours_per_week = models.IntegerField(default=5, verbose_name="Số giờ/tuần")
    difficulty = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ], default='beginner')
    
    def __str__(self):
        return f"Lộ trình: {self.course.title}"

class WeeklySchedule(models.Model):
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='weeks')
    week_number = models.IntegerField(verbose_name="Tuần thứ")
    title = models.CharField(max_length=200, verbose_name="Tiêu đề tuần")
    objectives = models.TextField(verbose_name="Mục tiêu học tập")
    total_hours = models.IntegerField(default=5, verbose_name="Tổng giờ học")
    
    class Meta:
        ordering = ['week_number']
    
    def __str__(self):
        return f"Week {self.week_number}: {self.title}"

class DailyTask(models.Model):
    weekly_schedule = models.ForeignKey(WeeklySchedule, on_delete=models.CASCADE, related_name='days')
    day_number = models.IntegerField(verbose_name="Ngày thứ")
    title = models.CharField(max_length=200, verbose_name="Tiêu đề")
    description = models.TextField(verbose_name="Mô tả công việc")
    duration_minutes = models.IntegerField(default=60, verbose_name="Thời gian (phút)")
    resources = models.TextField(blank=True, verbose_name="Tài liệu tham khảo")
    attachment = models.FileField(upload_to='resources/', blank=True, null=True, verbose_name="Tập tin đính kèm")
    is_completed = models.BooleanField(default=False, verbose_name="Hoàn thành")
    
    class Meta:
        ordering = ['day_number']
    
    def __str__(self):
        return f"Day {self.day_number}: {self.title}"


# Model để gán lộ trình cho học viên (admin có thể thêm)
class LearningPathEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_path_enrollments')
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='enrollments')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_learning_paths')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('inactive', 'Inactive')
    ], default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'learning_path')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} -> {self.learning_path.course.title} ({self.status})"