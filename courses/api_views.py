from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Profile, Course, Module, Enrollment, UserProgress, Review
from .serializers import (
    UserSerializer, ProfileSerializer, CourseSerializer, ModuleSerializer,
    EnrollmentSerializer, UserProgressSerializer, ReviewSerializer
)

# Utility Functions
def get_user_token(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    try:
        token = auth_header.split(' ')[1]
        user = Token.objects.get(key=token).user
        return user
    except (IndexError, Token.DoesNotExist):
        return None

def is_valid_token(request):
    user = get_user_token(request)
    return user is not None

def is_admin(user):
    return user.is_staff if user else False

def get_user_or_error(request):
    user = get_user_token(request)
    if not user:
        return Response({'error': 'Invalid or missing token'}, status=status.HTTP_401_UNAUTHORIZED)
    return user

# Authentication Views
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    if request.method == 'GET':
        return Response({'message': 'Please send a POST request with username and password'})
        
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Please provide both username and password'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
    else:   
        return Response({'error': 'Invalid credentials'}, 
                       status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def register_view(request):
    if request.method == 'GET':
        return Response({'message': 'Please send a POST request with user details'})
        
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# User Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_user(request):
    if not is_admin(request.user):
        return Response({'error': 'Only admins can create users'}, status=status.HTTP_403_FORBIDDEN)
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_users(request):
    if not is_admin(request.user):
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_user_by_token(request):
    user = get_user_or_error(request)
    if isinstance(user, Response):
        return user
    serializer = UserSerializer(user)
    return Response(serializer.data)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    if not is_admin(request.user) and request.user != user:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Profile Views
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([permissions.IsAuthenticated])
def create_profile(request):
    serializer = ProfileSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_profiles(request):
    if request.user.is_staff:
        profiles = Profile.objects.all()
    else:
        profiles = Profile.objects.filter(user=request.user)
    serializer = ProfileSerializer(profiles, many=True)
    return Response(serializer.data)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def profile_detail(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    if not request.user.is_staff and profile.user != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Course Views
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([permissions.IsAuthenticated])
def create_course(request):
    if not is_admin(request.user):
        return Response({'error': 'Only admins can create courses'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = CourseSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(instructor=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_courses(request):
    if request.user.is_authenticated and is_admin(request.user):
        courses = Course.objects.all()
    elif request.user.is_authenticated:
        courses = Course.objects.filter(instructor=request.user)
    else:
        courses = Course.objects.all()[:6]
    serializer = CourseSerializer(courses, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    serializer = CourseSerializer(course)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def enroll_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        return Response({'error': 'Already enrolled'}, status=status.HTTP_400_BAD_REQUEST)
    
    enrollment = Enrollment.objects.create(
        student=request.user,
        course=course,
        is_approved=False
    )
    serializer = EnrollmentSerializer(enrollment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

# Module Views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_module(request):
    if not is_admin(request.user):
        return Response({'error': 'Only admins can create modules'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = ModuleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_modules(request):
    if is_admin(request.user):
        modules = Module.objects.all()
    else:
        modules = Module.objects.filter(course__instructor=request.user)
    serializer = ModuleSerializer(modules, many=True)
    return Response(serializer.data)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def module_detail(request, pk):
    module = get_object_or_404(Module, pk=pk)
    if not is_admin(request.user) and module.course.instructor != request.user:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = ModuleSerializer(module)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ModuleSerializer(module, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        module.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Enrollment Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_enrollments(request):
    if is_admin(request.user):
        enrollments = Enrollment.objects.all()
    else:
        enrollments = Enrollment.objects.filter(student=request.user)
    serializer = EnrollmentSerializer(enrollments, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_enrollment(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if not is_admin(request.user) and request.user != enrollment.course.instructor:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
    
    enrollment.is_approved = True
    enrollment.save()
    serializer = EnrollmentSerializer(enrollment)
    return Response(serializer.data)

# Progress Views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_module_completed(request):
    module_id = request.data.get('module_id')
    if not module_id:
        return Response({'error': 'Module ID required'}, status=status.HTTP_400_BAD_REQUEST)
    
    module = get_object_or_404(Module, id=module_id)
    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        module=module
    )
    serializer = UserProgressSerializer(progress)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_progress(request):
    if is_admin(request.user):
        progress = UserProgress.objects.all()
    else:
        progress = UserProgress.objects.filter(user=request.user)
    serializer = UserProgressSerializer(progress, many=True)
    return Response(serializer.data)

# Review Views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_review(request):
    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_reviews(request):
    reviews = Review.objects.all()
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def review_detail(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if not is_admin(request.user) and review.user != request.user:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = ReviewSerializer(review)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ReviewSerializer(review, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 