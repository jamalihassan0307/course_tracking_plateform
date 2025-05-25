from django.contrib import admin
from .models import Profile, Course, Module, Enrollment, UserProgress, Review

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'description', 'instructor__username')

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order_number')
    list_filter = ('course',)
    search_fields = ('title', 'description')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'completed', 'is_approved')
    list_filter = ('completed', 'is_approved', 'enrolled_at')
    search_fields = ('student__username', 'course__title')
    actions = ['approve_enrollments']
    
    def approve_enrollments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_enrollments.short_description = "Approve selected enrollments"

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'completed_at')
    list_filter = ('completed_at',)
    search_fields = ('user__username', 'module__title')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'course__title', 'comment')
