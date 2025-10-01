# Quiz App - User Registration & Role-Based Access Guide

## Overview
This guide explains the role-based registration system implemented in the Quiz App with separate student and teacher registration.

## User Roles

### 1. Students
- **Purpose**: Take quizzes, view results, track progress
- **Registration URL**: `/quiz/register/student/`
- **Access Level**: No admin panel access
- **Permissions**: 
  - View and take quizzes
  - View own dashboard and results
  - Cannot access `/admin/` panel
- **Characteristics**:
  - `is_staff = False`
  - Member of "Students" group
  - Has StudentProfile with enrollment details

### 2. Teachers
- **Purpose**: Create and manage quizzes, view analytics
- **Registration URL**: `/quiz/register/teacher/`
- **Access Level**: Full admin panel access
- **Permissions**:
  - All student permissions
  - Access to Wagtail admin panel (`/admin/`)
  - Create, edit, delete quizzes
  - View quiz analytics and student performance
- **Characteristics**:
  - `is_staff = True`
  - Member of "Teachers" group
  - Has Wagtail page permissions

## Registration Process

### Student Registration
1. Navigate to `/quiz/register/student/`
2. Fill in the form:
   - Username (required)
   - Email (required)
   - First Name (required)
   - Last Name (required)
   - Enrollment Number (required)
   - Phone Number (required)
   - Date of Birth (required, format: YYYY-MM-DD)
   - Password (required)
   - Confirm Password (required)
3. Click "Register as Student"
4. Upon success, redirected to login page
5. After login, can access quizzes and dashboard (NO admin link visible)

### Teacher Registration
1. Navigate to `/quiz/register/teacher/`
2. Fill in the form:
   - Username (required)
   - Email (required)
   - First Name (required)
   - Last Name (required)
   - Employee ID (required)
   - Department (optional)
   - Phone Number (optional)
   - Password (required)
   - Confirm Password (required)
3. Click "Register as Teacher"
4. Upon success, redirected to login page
5. After login, can access quizzes, dashboard, AND admin panel (admin link visible in header)

## Header Navigation

The header navigation now dynamically displays based on user role:

### For Students:
```
Home | Quizzes | Dashboard | Welcome, [username]
```
**No Admin Link**

### For Teachers:
```
Home | Quizzes | Dashboard | Welcome, [username] | Admin
```
**Admin Link Visible**

### For Non-authenticated Users:
```
Home | Login
```

## Groups and Permissions

### Students Group
- Created automatically during setup
- Permissions: None (view-only access to quizzes)
- Cannot access Django admin or Wagtail admin

### Teachers Group
- Created automatically during setup
- Permissions:
  - `add_quiz`, `change_quiz`, `delete_quiz`, `view_quiz`
  - `add_page`, `change_page`, `delete_page`, `view_page`
  - `publish_page`, `lock_page`, `unlock_page`
  - Full Wagtail admin access

## Setup Commands

### First-time Setup
Run this command to set up groups and permissions:
```bash
python manage.py setup_permissions
```

This command will:
1. Create "Students" and "Teachers" groups
2. Assign appropriate permissions to each group
3. Configure Wagtail page permissions for teachers

## URLs

### Registration
- Student Registration: `/quiz/register/student/`
- Teacher Registration: `/quiz/register/teacher/`
- Login: `/quiz/login/`
- Logout: `/quiz/logout/`

### Quiz Interface
- Quiz List: `/quiz/`
- Quiz Detail: `/quiz/<id>/`
- Start Quiz: `/quiz/<id>/start/`
- Take Quiz: `/quiz/attempt/<attempt_id>/`
- Quiz Result: `/quiz/attempt/<attempt_id>/result/`
- Student Dashboard: `/quiz/dashboard/`

### Admin Interface (Teachers Only)
- Wagtail Admin: `/admin/`
- Django Admin: `/admin/` (same entry point)

## Testing the Role System

### Test Student Registration
1. Go to `/quiz/register/student/`
2. Register a new student account
3. Log in at `/quiz/login/`
4. Verify:
   - ✓ Can see quizzes
   - ✓ Can take quizzes
   - ✓ Can view dashboard
   - ✗ NO "Admin" link in header
   - ✗ Cannot access `/admin/` (redirects to login)

### Test Teacher Registration
1. Go to `/quiz/register/teacher/`
2. Register a new teacher account
3. Log in at `/quiz/login/`
4. Verify:
   - ✓ Can see quizzes
   - ✓ Can take quizzes (for testing)
   - ✓ Can view dashboard
   - ✓ CAN see "Admin" link in header
   - ✓ Can access `/admin/`
   - ✓ Can create/edit quizzes in Wagtail admin

## Forms

### StudentRegistrationForm
- Extends Django's `UserCreationForm`
- Additional fields: `enrollment_number`, `phone`, `date_of_birth`
- Creates `StudentProfile` automatically
- Sets `is_staff = False`
- Adds user to "Students" group

### TeacherRegistrationForm
- Extends Django's `UserCreationForm`
- Additional fields: `employee_id`, `department`, `phone`
- Sets `is_staff = True`
- Adds user to "Teachers" group
- Grants Wagtail page permissions

## Security Features

1. **Role Separation**: Students cannot access admin panel
2. **Group-Based Permissions**: Permissions managed through Django groups
3. **Password Validation**: Django's built-in password validators
4. **Login Required**: Quiz access requires authentication
5. **CSRF Protection**: All forms protected with CSRF tokens

## Troubleshooting

### "Admin" link shows for students
- Check if user's `is_staff` is correctly set to `False`
- Run: `python manage.py shell`
```python
from django.contrib.auth.models import User
user = User.objects.get(username='student_username')
print(user.is_staff)  # Should be False
```

### Teacher cannot access admin
- Check if user's `is_staff` is set to `True`
- Verify user is in "Teachers" group
- Run permissions setup: `python manage.py setup_permissions`

### Permission errors
- Re-run: `python manage.py setup_permissions`
- Check group membership in Django admin

## Files Modified

1. **quiz/forms.py** - Registration forms
2. **quiz/views.py** - Registration view functions
3. **quiz/urls.py** - Registration URL patterns
4. **quiz/templates/quiz/student_register.html** - Student registration template
5. **quiz/templates/quiz/teacher_register.html** - Teacher registration template
6. **quiz/templates/quiz/login.html** - Updated with registration links
7. **quiz/templates/quiz/*.html** - All quiz templates updated with role-based header
8. **quiz/management/commands/setup_permissions.py** - Permission setup command
9. **quizapp/static/css/quizapp.css** - Form styling

## Best Practices

1. Always run `setup_permissions` after initial migration
2. Use separate registration URLs for clarity
3. Test both roles thoroughly
4. Monitor user registrations
5. Keep group permissions updated
6. Use superuser for initial admin tasks

## Next Steps

1. ✅ Student registration implemented
2. ✅ Teacher registration implemented
3. ✅ Role-based header navigation
4. ✅ Groups and permissions configured
5. Consider: Email verification
6. Consider: Teacher approval workflow
7. Consider: Password reset functionality
8. Consider: User profile editing

---

For questions or issues, refer to the TROUBLESHOOTING.md file or create an issue in the project repository.
