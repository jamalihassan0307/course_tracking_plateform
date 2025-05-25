from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from .models import Course, Module, Enrollment, UserProgress, Profile, Review, User
from .forms import (UserRegisterForm, UserLoginForm, ProfileUpdateForm, UserUpdateForm,
                   CourseForm, ModuleForm, ReviewForm, EnrollmentRequestForm, PasswordChangeForm)
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect
from urllib.parse import urlparse

def is_safe_url_custom(url, allowed_hosts):
    """
    Custom function to validate if a URL is safe to redirect to.
    """
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.netloc in allowed_hosts or not parsed.netloc

def home(request):
    top_courses = Course.objects.annotate(
        rating_avg=Avg('reviews__rating'),
        students_count=Count('enrollments', distinct=True)
    ).order_by('-students_count')[:4]
    
    context = {
        'top_courses': top_courses,
    }
    return render(request, 'courses/home.html', context)

def about(request):
    return render(request, 'courses/about.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a profile for the user - always as student
            Profile.objects.create(user=user, role='student')
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = UserRegisterForm()
    
    return render(request, 'courses/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    # Get the next URL if provided
    next_url = request.GET.get('next', '')
    
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                if not user.is_active:
                    messages.error(request, 'Your account is disabled.')
                    return redirect('login')
                
                # Create profile if it doesn't exist
                try:
                    profile = user.profile
                except Profile.DoesNotExist:
                    Profile.objects.create(user=user, role='student')
                
                # Set session expiry to 2 weeks
                request.session.set_expiry(1209600)
                
                # Login the user
                login(request, user)
                
                # Get list of allowed hosts
                allowed_hosts = request.get_host()
                allowed_hosts = {allowed_hosts} if isinstance(allowed_hosts, str) else set(allowed_hosts)
                
                # Redirect to next URL if provided and safe
                if next_url and is_safe_url_custom(next_url, allowed_hosts):
                    return HttpResponseRedirect(next_url)
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    # Add next parameter to Google login URL if provided
    google_login_url = reverse('social:begin', args=['google-oauth2'])
    if next_url:
        google_login_url = f"{google_login_url}?next={next_url}"
    
    context = {
        'form': form,
        'google_login_url': google_login_url,
    }
    return render(request, 'courses/login.html', context)

@login_required
def logout_view(request):
    # Get the user's session key before logout
    session_key = request.session.session_key
    
    # Clear session data
    request.session.flush()
    
    # Delete the session from the database
    from django.contrib.sessions.models import Session
    Session.objects.filter(session_key=session_key).delete()
    
    # Logout the user
    logout(request)
    
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

@login_required
def profile(request):
    # Ensure user has a profile
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user, role='student')

    if request.method == 'POST':
        # Check which form is being submitted
        if 'update_profile' in request.POST:
            # Update user and profile information
            u_form = UserUpdateForm(request.POST, instance=request.user)
            p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
            
            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
                messages.success(request, 'Your account has been updated!')
                return redirect('profile')
        elif 'update_password' in request.POST:
            # Handle password change
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important to keep the user logged in
                messages.success(request, 'Your password was successfully updated!')
                return redirect('profile')
            else:
                messages.error(request, 'Please correct the errors below.')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)
        password_form = PasswordChangeForm(request.user)
    
    # Get courses the user is enrolled in
    enrolled_courses = Course.objects.filter(enrollments__student=request.user, enrollments__is_approved=True)
    
    # Get courses the user created (if instructor)
    created_courses = Course.objects.filter(instructor=request.user)
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'password_form': password_form,
        'enrolled_courses': enrolled_courses,
        'created_courses': created_courses,
    }
    return render(request, 'courses/profile.html', context)

def course_list(request):
    courses = Course.objects.annotate(
        rating_avg=Avg('reviews__rating'),
        students_count=Count('enrollments', distinct=True)
    ).all()
    
    # For guest users, limit the number of courses shown
    if not request.user.is_authenticated:
        courses = courses[:6]  # Show only the first 6 courses
    
    context = {
        'courses': courses,
        'is_guest': not request.user.is_authenticated
    }
    return render(request, 'courses/course_list.html', context)

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    modules = course.modules.order_by('order_number')
    reviews = course.reviews.order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    
    # Check if user is authenticated
    if not request.user.is_authenticated:
        # For guest users, show limited information
        context = {
            'course': course,
            'modules': modules[:1] if modules.exists() else [],  # Show only first module
            'reviews': reviews[:2],  # Show only first 2 reviews
            'avg_rating': avg_rating,
            'is_guest': True,
            'restricted_content': True
        }
        return render(request, 'courses/course_detail.html', context)
    
    # For authenticated users, proceed as normal
    is_enrolled = False
    has_requested_enrollment = False
    can_enroll = False
    
    # Check if user has student role (not admin or instructor)
    is_student = request.user.profile.role == 'student'
    can_enroll = is_student and request.user != course.instructor

    is_enrolled = Enrollment.objects.filter(
        student=request.user, 
        course=course,
        is_approved=True
    ).exists()
    
    has_requested_enrollment = Enrollment.objects.filter(
        student=request.user, 
        course=course,
        is_approved=False
    ).exists()
    
    # For enrollment request
    enrollment_form = EnrollmentRequestForm()
    if request.method == 'POST' and 'enrollment_request' in request.POST:
        # Check if user has appropriate role to enroll
        if can_enroll:
            Enrollment.objects.get_or_create(
                student=request.user,
                course=course,
                defaults={'is_approved': False}
            )
            messages.success(request, 'Enrollment request sent! Waiting for approval.')
            return redirect('course_detail', course_id=course.id)
        else:
            if request.user.profile.role != 'student':
                messages.warning(request, 'Only students can enroll in courses.')
            else:
                messages.warning(request, 'You cannot enroll in your own course.')
            return redirect('course_detail', course_id=course.id)
    
    # For reviews
    review_form = None
    user_review = None
    if is_enrolled:
        user_review = Review.objects.filter(user=request.user, course=course).first()
        if request.method == 'POST' and 'review_submit' in request.POST:
            if user_review:
                review_form = ReviewForm(request.POST, instance=user_review)
            else:
                review_form = ReviewForm(request.POST)
            
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.user = request.user
                review.course = course
                review.save()
                messages.success(request, 'Your review has been submitted!')
                return redirect('course_detail', course_id=course.id)
        else:
            if user_review:
                review_form = ReviewForm(instance=user_review)
            else:
                review_form = ReviewForm()
    
    context = {
        'course': course,
        'modules': modules,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'is_enrolled': is_enrolled,
        'has_requested_enrollment': has_requested_enrollment,
        'can_enroll': can_enroll,
        'enrollment_form': enrollment_form,
        'review_form': review_form,
        'user_review': user_review,
        'is_guest': False,
    }
    return render(request, 'courses/course_detail.html', context)

@login_required
def module_detail(request, course_id, module_id):
    course = get_object_or_404(Course, id=course_id)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    # Get all modules for navigation
    all_modules = course.modules.order_by('order_number')
    
    # Check if user is enrolled and approved
    is_enrolled = Enrollment.objects.filter(
        student=request.user, 
        course=course,
        is_approved=True
    ).exists()
    
    if not is_enrolled and not request.user.is_superuser and request.user != course.instructor:
        messages.warning(request, 'You must be enrolled in this course to access modules.')
        return redirect('course_detail', course_id=course.id)
    
    # Get user progress
    user_progress = {}
    progress_entries = UserProgress.objects.filter(
        user=request.user,
        module__course=course
    )
    
    for progress in progress_entries:
        user_progress[progress.module.id] = True
    
    # Mark module as completed
    is_completed = UserProgress.objects.filter(
        user=request.user,
        module=module
    ).exists()
    
    if request.method == 'POST' and 'mark_completed' in request.POST:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            module=module
        )
        
        if not created:
            progress.completed_at = timezone.now()
            progress.save()
        
        # Check if all modules are completed
        all_modules_completed = True
        for m in all_modules:
            module_completed = UserProgress.objects.filter(
                user=request.user,
                module=m
            ).exists()
            
            if not module_completed:
                all_modules_completed = False
                break
        
        # If all modules are completed, mark course as completed
        if all_modules_completed:
            enrollment.completed = True
            enrollment.save()
            messages.success(request, 'Congratulations! You have completed the course.')
        
        messages.success(request, f'Module "{module.title}" marked as completed!')
        return redirect('module_detail', course_id=course.id, module_id=module.id)
    
    context = {
        'course': course,
        'module': module,
        'all_modules': all_modules,
        'user_progress': user_progress,
        'is_completed': is_completed,
    }
    return render(request, 'courses/module_detail.html', context)

@login_required
def create_course(request):
    # Check if user is admin
    if not request.user.is_superuser and request.user.profile.role != 'admin':
        messages.warning(request, 'Only administrators can create courses.')
        return redirect('home')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            # Admin can assign course to any instructor
            instructor_id = request.POST.get('instructor')
            if instructor_id:
                try:
                    instructor = User.objects.get(id=instructor_id, profile__role='instructor')
                    course.instructor = instructor
                    course.save()
                    messages.success(request, f'Course created and assigned to {instructor.username}!')
                    return redirect('course_detail', course_id=course.id)
                except User.DoesNotExist:
                    messages.error(request, 'Selected instructor does not exist.')
            else:
                messages.error(request, 'Please select an instructor for this course.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseForm()
    
    # Get all instructors for the dropdown
    instructors = User.objects.filter(profile__role='instructor')
    
    context = {
        'form': form,
        'title': 'Create Course',
        'instructors': instructors,
    }
    return render(request, 'courses/course_form.html', context)

@login_required
def update_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is admin
    if not request.user.is_superuser and request.user.profile.role != 'admin':
        messages.warning(request, 'Only administrators can update courses.')
        return redirect('course_detail', course_id=course.id)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            updated_course = form.save(commit=False)
            # Admin can reassign course to different instructor
            instructor_id = request.POST.get('instructor')
            if instructor_id:
                try:
                    instructor = User.objects.get(id=instructor_id, profile__role='instructor')
                    updated_course.instructor = instructor
                    updated_course.save()
                    messages.success(request, f'Course updated and assigned to {instructor.username}!')
                    return redirect('course_detail', course_id=course.id)
                except User.DoesNotExist:
                    messages.error(request, 'Selected instructor does not exist.')
            else:
                messages.error(request, 'Please select an instructor for this course.')
    else:
        form = CourseForm(instance=course)
    
    # Get all instructors for the dropdown
    instructors = User.objects.filter(profile__role='instructor')
    
    context = {
        'form': form,
        'course': course,
        'title': 'Update Course',
        'instructors': instructors,
    }
    return render(request, 'courses/course_form.html', context)

@login_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is admin
    if not request.user.is_superuser and request.user.profile.role != 'admin':
        messages.warning(request, 'Only administrators can delete courses.')
        return redirect('course_detail', course_id=course.id)
    
    if request.method == 'POST':
        course_title = course.title
        course.delete()
        messages.success(request, f'Course "{course_title}" has been deleted.')
        return redirect('course_list')
    
    context = {
        'course': course,
    }
    return render(request, 'courses/course_confirm_delete.html', context)

@login_required
def create_module(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is admin
    if not request.user.is_superuser and request.user.profile.role != 'admin':
        messages.warning(request, 'Only administrators can add modules.')
        return redirect('course_detail', course_id=course.id)
    
    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            messages.success(request, 'Module added successfully!')
            return redirect('course_detail', course_id=course.id)
    else:
        # Auto-calculate the next order number
        next_order = course.modules.count() + 1
        form = ModuleForm(initial={'order_number': next_order})
    
    context = {
        'form': form,
        'course': course,
        'title': 'Add Module',
    }
    return render(request, 'courses/module_form.html', context)

@login_required
def update_module(request, course_id, module_id):
    course = get_object_or_404(Course, id=course_id)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    # Check if user is admin
    if not request.user.is_superuser and request.user.profile.role != 'admin':
        messages.warning(request, 'Only administrators can edit modules.')
        return redirect('module_detail', course_id=course.id, module_id=module.id)
    
    if request.method == 'POST':
        form = ModuleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            messages.success(request, 'Module updated successfully!')
            return redirect('module_detail', course_id=course.id, module_id=module.id)
    else:
        form = ModuleForm(instance=module)
    
    context = {
        'form': form,
        'course': course,
        'module': module,
        'title': 'Update Module',
    }
    return render(request, 'courses/module_form.html', context)

@login_required
def instructor_dashboard(request):
    # Check if user is instructor
    try:
        if request.user.profile.role != 'instructor':
            messages.warning(request, 'Only instructors can access this page.')
            return redirect('home')
    except Profile.DoesNotExist:
        messages.warning(request, 'Profile not found.')
        return redirect('home')
    
    # Get courses created by the instructor
    courses = Course.objects.filter(instructor=request.user)
    
    # Get enrollment requests for instructor's courses
    enrollment_requests = Enrollment.objects.filter(
        course__instructor=request.user,
        is_approved=False
    ).select_related('student', 'course')
    
    # Calculate total students
    total_students = 0
    for course in courses:
        total_students += course.enrollments.filter(is_approved=True).count()
    
    context = {
        'courses': courses,
        'enrollment_requests': enrollment_requests,
        'total_students': total_students
    }
    return render(request, 'courses/instructor_dashboard.html', context)

@login_required
def approve_enrollment(request, enrollment_id):
    # Check if user is instructor
    try:
        if request.user.profile.role != 'instructor':
            messages.warning(request, 'Only instructors can approve enrollments.')
            return redirect('home')
    except Profile.DoesNotExist:
        messages.warning(request, 'Profile not found.')
        return redirect('home')
    
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    
    # Check if the user is the instructor of the course
    if request.user != enrollment.course.instructor:
        messages.warning(request, 'You can only approve enrollments for your own courses.')
        return redirect('instructor_dashboard')
    
    enrollment.is_approved = True
    enrollment.save()
    messages.success(request, f'Enrollment for {enrollment.student.username} has been approved.')
    return redirect('instructor_dashboard')

@login_required
def reject_enrollment(request, enrollment_id):
    # Check if user is instructor
    try:
        if request.user.profile.role != 'instructor':
            messages.warning(request, 'Only instructors can reject enrollments.')
            return redirect('home')
    except Profile.DoesNotExist:
        messages.warning(request, 'Profile not found.')
        return redirect('home')
    
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    
    # Check if the user is the instructor of the course
    if request.user != enrollment.course.instructor:
        messages.warning(request, 'You can only reject enrollments for your own courses.')
        return redirect('instructor_dashboard')
    
    student_name = enrollment.student.username
    enrollment.delete()
    messages.success(request, f'Enrollment request from {student_name} has been rejected.')
    return redirect('instructor_dashboard')

@login_required
def my_activity(request):
    """
    Show the user's activity across all enrolled courses including:
    - Enrolled courses with progress percentage
    - Recently completed modules
    - Upcoming modules
    """
    # Get courses the user is enrolled in
    enrollments = Enrollment.objects.filter(
        student=request.user,
        is_approved=True
    ).select_related('course').order_by('-enrolled_at')
    
    # Calculate progress for each enrolled course
    course_progress = {}
    recent_completions = []
    
    for enrollment in enrollments:
        course = enrollment.course
        total_modules = course.modules.count()
        
        if total_modules > 0:
            # Get completed modules
            completed_modules = UserProgress.objects.filter(
                user=request.user,
                module__course=course
            ).select_related('module')
            
            completed_count = completed_modules.count()
            progress_percent = (completed_count / total_modules) * 100
            
            # Store progress data
            course_progress[course.id] = {
                'course': course,
                'total_modules': total_modules,
                'completed_modules': completed_count,
                'progress_percent': progress_percent,
                'is_completed': enrollment.completed
            }
            
            # Get 5 most recently completed modules
            for completion in completed_modules.order_by('-completed_at')[:5]:
                recent_completions.append({
                    'module': completion.module,
                    'course': course,
                    'completed_at': completion.completed_at
                })
    
    # Get next modules to complete
    upcoming_modules = []
    
    for enrollment in enrollments:
        course = enrollment.course
        
        # Only look at courses that aren't completed
        if not enrollment.completed:
            # Get completed module IDs
            completed_module_ids = UserProgress.objects.filter(
                user=request.user,
                module__course=course
            ).values_list('module_id', flat=True)
            
            # Find modules that aren't completed yet
            incomplete_modules = Module.objects.filter(
                course=course
            ).exclude(id__in=completed_module_ids).order_by('order_number')
            
            # Add the first incomplete module to the upcoming list
            if incomplete_modules.exists():
                upcoming_modules.append({
                    'module': incomplete_modules.first(),
                    'course': course
                })
    
    context = {
        'enrollments': enrollments,
        'course_progress': course_progress,
        'recent_completions': recent_completions,
        'upcoming_modules': upcoming_modules
    }
    
    return render(request, 'courses/my_activity.html', context)

@login_required
def course_users_progress(request, course_id):
    """
    Show the progress of all students enrolled in a specific course.
    Allow instructors to update student progress.
    """
    course = get_object_or_404(Course, id=course_id)
    
    # Check if the user is the instructor of this course or an admin
    if request.user != course.instructor and not request.user.is_superuser and request.user.profile.role != 'admin':
        messages.warning(request, 'You can only view progress for courses you instruct.')
        return redirect('instructor_dashboard')
    
    # Get all approved enrollments for this course
    enrollments = Enrollment.objects.filter(
        course=course,
        is_approved=True
    ).select_related('student', 'student__profile')
    
    # Get all modules for this course
    modules = Module.objects.filter(course=course).order_by('order_number')
    
    # Get progress data for all students
    student_progress = {}
    
    for enrollment in enrollments:
        student = enrollment.student
        
        # Get progress entries for this student
        completed_modules = UserProgress.objects.filter(
            user=student,
            module__course=course
        ).values_list('module_id', flat=True)
        
        # Calculate progress percentage
        total_modules = modules.count()
        if total_modules > 0:
            progress_percent = (len(completed_modules) / total_modules) * 100
        else:
            progress_percent = 0
        
        # Store student progress data
        student_progress[student.id] = {
            'student': student,
            'completed_modules': completed_modules,
            'progress_percent': progress_percent,
            'enrollment_date': enrollment.enrolled_at,
            'is_completed': enrollment.completed
        }
    
    # Handle form submission to update student progress
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        module_id = request.POST.get('module_id')
        action = request.POST.get('action')
        
        if student_id and module_id and action:
            student = get_object_or_404(User, id=student_id)
            module = get_object_or_404(Module, id=module_id)
            
            # Ensure the module belongs to the correct course
            if module.course != course:
                messages.error(request, 'Invalid module selection.')
                return redirect('course_users_progress', course_id=course.id)
            
            if action == 'mark_completed':
                # Mark module as completed for the student
                UserProgress.objects.get_or_create(
                    user=student,
                    module=module
                )
                messages.success(request, f'Module "{module.title}" marked as completed for {student.username}.')
            
            elif action == 'mark_incomplete':
                # Mark module as incomplete by removing the progress entry
                UserProgress.objects.filter(user=student, module=module).delete()
                messages.success(request, f'Module "{module.title}" marked as incomplete for {student.username}.')
            
            # Check if all modules are now completed
            student_enrolled = Enrollment.objects.get(student=student, course=course)
            completed_count = UserProgress.objects.filter(user=student, module__course=course).count()
            
            if completed_count == modules.count():
                student_enrolled.completed = True
                student_enrolled.save()
                messages.success(request, f'{student.username} has completed the entire course!')
            else:
                student_enrolled.completed = False
                student_enrolled.save()
            
            # Redirect to avoid form resubmission
            return redirect('course_users_progress', course_id=course.id)
    
    context = {
        'course': course,
        'modules': modules,
        'enrollments': enrollments,
        'student_progress': student_progress
    }
    
    return render(request, 'courses/course_users_progress.html', context)
