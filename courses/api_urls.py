from django.urls import path
from .api_views import (
    # Auth views
    login_view, register_view,
    # User views
    create_user, get_users, user_detail,get_user_by_token,
    # Profile views
    create_profile, get_profiles, profile_detail,
    # Course views
    create_course, get_courses, course_detail, enroll_course,
    # Module views
    create_module, get_modules, module_detail,
    # Enrollment views
    get_enrollments, approve_enrollment,
    # Progress views
    mark_module_completed, get_user_progress,
    # Review views
    create_review, get_reviews, review_detail
)

urlpatterns = [
    # Auth URLs
    path('auth/login/', login_view, name='api-login'),
    path('auth/register/', register_view, name='api-register'),
    
    # User URLs
    path('users/', get_users, name='user-list'),
    path('users/getuserbytoken/', get_user_by_token, name='user-getuserbytoken'),
    path('users/create/', create_user, name='user-create'),
    path('users/<int:pk>/', user_detail, name='user-detail'),
    
    # Profile URLs
    path('profiles/', get_profiles, name='profile-list'),
    path('profiles/create/', create_profile, name='profile-create'),
    path('profiles/<int:pk>/', profile_detail, name='profile-detail'),
    
    # Course URLs
    path('courses/', get_courses, name='course-list'),
    path('courses/create/', create_course, name='course-create'),
    path('courses/<int:pk>/', course_detail, name='course-detail'),
    path('courses/<int:pk>/enroll/', enroll_course, name='course-enroll'),
    
    # Module URLs
    path('modules/', get_modules, name='module-list'),
    path('modules/create/', create_module, name='module-create'),
    path('modules/<int:pk>/', module_detail, name='module-detail'),
    
    # Enrollment URLs
    path('enrollments/', get_enrollments, name='enrollment-list'),
    path('enrollments/<int:pk>/approve/', approve_enrollment, name='enrollment-approve'),
    
    # Progress URLs
    path('progress/', get_user_progress, name='progress-list'),
    path('progress/mark-completed/', mark_module_completed, name='progress-mark-completed'),
    
    # Review URLs
    path('reviews/', get_reviews, name='review-list'),
    path('courses/<int:course_id>/reviews/create/', create_review),
    path('reviews/<int:pk>/', review_detail, name='review-detail'),
] 