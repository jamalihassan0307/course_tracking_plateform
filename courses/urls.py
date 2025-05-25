from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('my-activity/', views.my_activity, name='my_activity'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/modules/<int:module_id>/', views.module_detail, name='module_detail'),
    path('courses/create/', views.create_course, name='create_course'),
    path('courses/<int:course_id>/update/', views.update_course, name='update_course'),
    path('courses/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    path('courses/<int:course_id>/modules/create/', views.create_module, name='create_module'),
    path('courses/<int:course_id>/modules/<int:module_id>/update/', views.update_module, name='update_module'),
    path('courses/<int:course_id>/users-progress/', views.course_users_progress, name='course_users_progress'),
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('enrollments/<int:enrollment_id>/approve/', views.approve_enrollment, name='approve_enrollment'),
    path('enrollments/<int:enrollment_id>/reject/', views.reject_enrollment, name='reject_enrollment'),
    path('social-auth/', include('social_django.urls', namespace='social')),
] 