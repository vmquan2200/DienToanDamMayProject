from django.core.management.base import BaseCommand
from courses.models import Course, Lesson, LearningPath, WeeklySchedule, DailyTask
from decimal import Decimal


class Command(BaseCommand):
    help = 'Tạo các khóa học mẫu để test tính năng mua và thanh toán'

    def handle(self, *args, **options):
        courses_data = [
            {
                'title': 'Python Cơ Bản - Từ Zero đến Hero',
                'description': '''
Khóa học Python cơ bản dành cho người mới bắt đầu. Bạn sẽ học:
- Cú pháp Python cơ bản
- Biến, kiểu dữ liệu, toán tử
- Cấu trúc điều khiển (if/else, vòng lặp)
- Hàm và module
- Xử lý file và exception
- Lập trình hướng đối tượng cơ bản

Sau khóa học, bạn sẽ có nền tảng vững chắc để tiếp tục học các framework như Django, Flask.
                ''',
                'price': Decimal('299000'),
                'category': 'python',
            },
            {
                'title': 'Django Web Development - Xây Dựng Website Chuyên Nghiệp',
                'description': '''
Khóa học Django toàn diện giúp bạn xây dựng website chuyên nghiệp:
- Tìm hiểu về Django Framework
- Models, Views, Templates
- Authentication và Authorization
- RESTful API với Django REST Framework
- Deploy ứng dụng lên server
- Best practices và security

Phù hợp cho những ai đã có kiến thức Python cơ bản.
                ''',
                'price': Decimal('599000'),
                'category': 'django',
            },
            {
                'title': 'HTML, CSS & JavaScript - Frontend Development',
                'description': '''
Khóa học Frontend Development đầy đủ:
- HTML5 và Semantic HTML
- CSS3, Flexbox, Grid Layout
- JavaScript ES6+
- DOM Manipulation
- Responsive Design
- Build tools và frameworks

Tạo ra những website đẹp mắt và tương tác tốt.
                ''',
                'price': Decimal('399000'),
                'category': 'web',
            },
            {
                'title': 'Data Science với Python - Phân Tích Dữ Liệu',
                'description': '''
Khóa học Data Science thực tế:
- NumPy và Pandas
- Data Visualization với Matplotlib, Seaborn
- Machine Learning cơ bản với Scikit-learn
- Xử lý và làm sạch dữ liệu
- Phân tích dữ liệu thực tế
- Jupyter Notebook

Phù hợp cho người muốn làm việc với dữ liệu và AI.
                ''',
                'price': Decimal('699000'),
                'category': 'data',
            },
            {
                'title': 'Python Nâng Cao - Advanced Programming',
                'description': '''
Khóa học Python nâng cao:
- Decorators và Generators
- Context Managers
- Metaclasses
- Concurrency và Parallelism
- Design Patterns
- Testing và Debugging
- Performance Optimization

Dành cho những ai đã nắm vững Python cơ bản.
                ''',
                'price': Decimal('499000'),
                'category': 'python',
            },
            {
                'title': 'Full Stack Development - Django + React',
                'description': '''
Khóa học Full Stack Development:
- Backend với Django REST Framework
- Frontend với React.js
- Kết nối Frontend và Backend
- Authentication với JWT
- State Management với Redux
- Deploy full stack application

Xây dựng ứng dụng web hoàn chỉnh từ đầu đến cuối.
                ''',
                'price': Decimal('899000'),
                'category': 'web',
            },
        ]

        created_count = 0
        for course_data in courses_data:
            course, created = Course.objects.get_or_create(
                title=course_data['title'],
                defaults={
                    'description': course_data['description'].strip(),
                    'price': course_data['price'],
                    'category': course_data['category'],
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Đã tạo khóa học: {course.title} - {course.get_category_display()} - {course.price:,.0f} VNĐ'
                    )
                )
                
                # Tạo một số bài học mẫu cho khóa học
                for i in range(1, 6):
                    Lesson.objects.get_or_create(
                        course=course,
                        title=f'Bài {i}: Nội dung bài học {i}',
                        defaults={
                            'video_url': f'https://www.youtube.com/watch?v=example{i}',
                            'order': i,
                        }
                    )
                
                # Tạo Learning Path mặc định
                learning_path, lp_created = LearningPath.objects.get_or_create(
                    course=course,
                    defaults={
                        'total_weeks': 4,
                        'hours_per_week': 5,
                        'difficulty': 'beginner' if course.price < Decimal('500000') else 'intermediate',
                    }
                )
                
                if lp_created:
                    # Tạo WeeklySchedule và DailyTask
                    for week_num in range(1, 5):
                        weekly, _ = WeeklySchedule.objects.get_or_create(
                            learning_path=learning_path,
                            week_number=week_num,
                            defaults={
                                'title': f'Tuần {week_num}',
                                'objectives': f'Mục tiêu học tập tuần {week_num}',
                                'total_hours': 5,
                            }
                        )
                        
                        # Tạo DailyTask cho mỗi tuần
                        for day_num in range(1, 6):
                            DailyTask.objects.get_or_create(
                                weekly_schedule=weekly,
                                day_number=day_num,
                                defaults={
                                    'title': f'Bài học ngày {day_num} - Tuần {week_num}',
                                    'description': f'Nội dung và bài tập cho ngày {day_num}',
                                    'duration_minutes': 60,
                                    'resources': '',
                                }
                            )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Khóa học đã tồn tại: {course.title}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Hoàn thành! Đã tạo {created_count} khóa học mới.'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Tổng số khóa học hiện có: {Course.objects.count()}'
            )
        )
