from django.apps import AppConfig


class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'
    
    def ready(self):
        # This will ensure templatetags are properly loaded
        import courses.templatetags.course_tags
        import courses.signals  # Import signals when app is ready
