from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    # Legacy static path used in some templates/bookmarks — redirect to current list
    path('courses/course_list.html/', RedirectView.as_view(url='/', permanent=True)),
    path('', views.home, name='course_list'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('add-to-cart/<int:course_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('search/', views.search_courses, name='search'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('checkout-direct/<int:course_id>/', views.checkout_direct, name='checkout_direct'),
    path('generate-qr/<int:course_id>/', views.generate_qr_code, name='generate_qr'),
    path('payment-course/', views.payment_course_view, name='payment_course'),
    path('payment-confirm/', views.payment_confirm_view, name='payment_confirm'),
    path('activate-payment/<str:token>/', views.activate_payment, name='activate_payment'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    # Development helper login (use only in DEBUG; requires DEV_LOGIN_TOKEN in .env)
    path('dev-login/', views.dev_login, name='dev_login'),
    # Development helper confirm + login (dev-only)
    path('dev-confirm/<str:key>/', views.dev_confirm_and_login, name='dev_confirm'),
    path('my-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/payment/<int:payment_id>/approve/', views.admin_approve_payment, name='admin_approve_payment'),
    path('admin/payment/<int:payment_id>/reject/', views.admin_reject_payment, name='admin_reject_payment'),
    path('forum/', views.forum_list, name='forum_list'),
    path('forum/create/', views.forum_create, name='forum_create'),
    path('forum/<int:post_id>/', views.forum_detail, name='forum_detail'),
    path('forum/tag/<str:tag>/', views.forum_tag, name='forum_tag'),
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('forum/<int:post_id>/toggle-pin/', views.forum_toggle_pin, name='forum_toggle_pin'),
    path('forum/<int:post_id>/toggle-feature/', views.forum_toggle_feature, name='forum_toggle_feature'),
    path('forum/<int:post_id>/edit/', views.forum_edit, name='forum_edit'),
    path('forum/<int:post_id>/delete/', views.forum_delete, name='forum_delete'),
    path('forum/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('forum/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('recent-activity/', views.recent_activity, name='recent_activity'),
    path('remove-from-cart/<int:course_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('course/<int:course_id>/learning-path/', views.learning_path, name='learning_path'),
    path('toggle-task/<int:task_id>/', views.toggle_task_completion, name='toggle_task_completion'),
    path('admin/learning-path-assign/', views.admin_learning_path_assign, name='admin_learning_path_assign'),
    path('my-schedule/<int:enrollment_id>/', views.my_schedule, name='my_schedule'),

     # URLs reset password
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    # THÊM URL CHO LOGIN
    # Redirect plain /login/ to allauth's login to ensure the expected
    # `login` field in the template is handled correctly by allauth.
    path('login/', RedirectView.as_view(url='/accounts/login/'), name='login'),
]
