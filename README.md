# Course Tracking Platform

A modern course management and tracking platform built with Django.

## Features

- **User Authentication**: Register, login, and manage user profiles
- **Role-Based Access**: Different functionalities for students and instructors
- **Course Management**: Create, browse, and manage courses
- **Module System**: Organize course content into modules
- **Progress Tracking**: Track student progress through courses
- **Enrollment System**: Request and approve course enrollments
- **Review System**: Review and rate courses
- **Instructor Dashboard**: Monitor enrollments and student progress

## Tech Stack

- **Backend**: Django
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript
- **UI Framework**: Bootstrap 5
- **Icons**: Font Awesome
- **Styling**: Custom CSS

## Installation

1. Clone the repository:

   ```
   git clone <repository-url>
   cd course_tracking_platform
   ```

2. Create a virtual environment and activate it:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install required packages:

   ```
   pip install -r requirements.txt
   ```

4. Set up PostgreSQL database:

   - Create a PostgreSQL database named `course_tracking_db`
   - Update database credentials in `settings.py` if needed

5. Apply migrations:

   ```
   python manage.py migrate
   ```

6. Create a superuser:

   ```
   python manage.py createsuperuser
   ```

7. Run the development server:

   ```
   python manage.py runserver
   ```

8. Access the application at `http://127.0.0.1:8000/`

## Usage

### Admin Users

- Log in to the admin panel at `http://127.0.0.1:8000/admin/`
- Manage users, courses, enrollments, and all other data

### Instructors

- Create and manage courses
- Add modules to courses
- Approve or reject enrollment requests
- View student progress

### Students

- Browse available courses
- Request enrollment in courses
- Track progress on enrolled courses
- Complete modules
- Review courses

## Project Structure

- `courses/` - Main application
  - `models.py` - Database models
  - `views.py` - Application views
  - `forms.py` - Form definitions
  - `urls.py` - URL routing
  - `admin.py` - Admin panel configuration
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS, images)
- `media/` - User-uploaded files

## Default User Roles

When registering, users are assigned the "student" role by default. To become an instructor:

1. Log in as admin
2. Go to the user's profile in the admin panel
3. Change their role to "instructor"

## License

This project is licensed under the MIT License - see the LICENSE file for details.
