from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Course, Module, Enrollment, UserProgress, Review

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'user', 'role', 'bio', 'profile_image']
        read_only_fields = ['id']

    def validate_role(self, value):
        valid_roles = ['student', 'instructor', 'admin']
        if value not in valid_roles:
            raise serializers.ValidationError(f"Role must be one of {valid_roles}")
        return value

    def create(self, validated_data):
        return Profile.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.role = validated_data.get('role', instance.role)
        instance.bio = validated_data.get('bio', instance.bio)
        instance.profile_image = validated_data.get('profile_image', instance.profile_image)
        instance.save()
        return instance

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'description', 'order_number']
        read_only_fields = ['id']

    def validate_order_number(self, value):
        course = self.initial_data.get('course')
        if Module.objects.filter(course=course, order_number=value).exists():
            raise serializers.ValidationError("This order number already exists for this course.")
        return value

    def create(self, validated_data):
        return Module.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.order_number = validated_data.get('order_number', instance.order_number)
        instance.save()
        return instance

class CourseSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    modules = ModuleSerializer(many=True, read_only=True)
    rating_avg = serializers.SerializerMethodField()
    students_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'thumbnail', 'created_at', 
                 'updated_at', 'instructor', 'modules', 'rating_avg', 'students_count']
        read_only_fields = ['id', 'created_at', 'updated_at'],
        extra_kwargs = {
            'title': {'required': True},
            'description': {'required': True},
        }



    def get_rating_avg(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0

    def get_students_count(self, obj):
        return obj.enrollments.filter(is_approved=True).count()

    def create(self, validated_data):
        return Course.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.thumbnail = validated_data.get('thumbnail', instance.thumbnail)
        instance.save()
        return instance

class EnrollmentSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'course', 'enrolled_at', 'completed', 'is_approved']
        read_only_fields = ['id', 'enrolled_at']

    def create(self, validated_data):
        return Enrollment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.completed = validated_data.get('completed', instance.completed)
        instance.is_approved = validated_data.get('is_approved', instance.is_approved)
        instance.save()
        return instance

class UserProgressSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    module = ModuleSerializer(read_only=True)

    class Meta:
        model = UserProgress
        fields = ['id', 'user', 'module', 'completed_at']
        read_only_fields = ['id', 'completed_at']

    def create(self, validated_data):
        return UserProgress.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.completed_at = validated_data.get('completed_at', instance.completed_at)
        instance.save()
        return instance

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'course', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def create(self, validated_data):
        return Review.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.rating = validated_data.get('rating', instance.rating)
        instance.comment = validated_data.get('comment', instance.comment)
        instance.save()
        return instance 