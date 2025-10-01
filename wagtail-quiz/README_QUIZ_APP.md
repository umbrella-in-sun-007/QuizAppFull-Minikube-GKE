# Quiz Application - Complete Guide

## Overview
A complete quiz management system built with Wagtail CMS and Django. Teachers manage quizzes through the Wagtail admin panel, and students take quizzes through a simple wireframe-style interface.

## Features

### For Teachers (via Wagtail Admin)
- Create and manage quizzes from CMS dashboard
- Add multiple types of questions:
  - Single Choice (radio buttons)
  - Multiple Choice (checkboxes)
  - True/False
  - Short Answer
- Configure quiz settings:
  - Duration (time limit)
  - Pass percentage
  - Maximum attempts allowed
  - Start/End dates
  - Question randomization
  - Show answers immediately or not
- View detailed analytics:
  - Overall statistics (attempts, pass rate, avg score)
  - Question-wise analysis
  - Student performance tracking
  - Score distribution charts
  - Top performers list

### For Students (via Frontend)
- Simple login system
- Browse available quizzes
- View quiz details before starting
- Take timed quizzes
- Multiple question types support
- See results immediately (if enabled)
- View answer explanations
- Track personal performance
- Dashboard with statistics

## Installation & Setup

### 1. Database Migration
```bash
cd /home/super/Documents/QuizAppFull/wagtail-quiz
source .venv/bin/activate
python manage.py makemigrations
python manage.py migrate
```

### 2. Create Superuser (Teacher/Admin)
```bash
python manage.py createsuperuser
```

### 3. Run Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```

## Usage Guide

### For Teachers

#### 1. Access Admin Panel
- Go to: `http://localhost:8000/admin/`
- Login with superuser credentials

#### 2. Create a Quiz
1. In the admin sidebar, go to **Pages**
2. Click on **Home** page
3. Click **Add child page**
4. Select **Quiz** from page types
5. Fill in quiz details:
   - Title
   - Description
   - Duration (minutes)
   - Pass percentage
   - Max attempts
   - Start/End dates (optional)
   - Display options

#### 3. Add Questions
1. In the quiz edit page, scroll to **Questions** section
2. Click **Add question**
3. Enter question text
4. Select question type
5. Set marks for the question
6. Add answer options:
   - For Single/Multiple Choice: Add options and mark correct ones
   - For True/False: Add "True" and "False" options, mark correct one
   - For Short Answer: No options needed (manual grading required)
7. Add explanation (optional) - shown after quiz submission
8. Repeat for all questions

#### 4. Publish Quiz
1. Click **Publish** button at the bottom
2. Quiz is now live and visible to students

#### 5. View Analytics
1. Go to quiz page in admin
2. Visit: `http://localhost:8000/quiz/{quiz_id}/analytics/`
3. View comprehensive statistics and student performance

#### 6. Manage Students
1. In admin panel, go to **Snippets** → **Student Profiles**
2. Add/Edit student information
3. View student statistics

#### 7. View Quiz Attempts
1. In admin panel, go to **Django Admin** → **Quiz Attempts**
2. Filter by quiz, status, or student
3. View detailed attempt information

### For Students

#### 1. Create Student Account
Ask admin to create account, or use Django admin to self-register

#### 2. Login
- Go to: `http://localhost:8000/quiz/login/`
- Enter username and password

#### 3. Browse Quizzes
- After login, you'll see all available quizzes
- View quiz details, duration, and pass marks
- See your previous attempts

#### 4. Take a Quiz
1. Click **Start Quiz** button
2. Timer starts automatically
3. Answer all questions
4. Click **Submit Quiz** before time runs out
5. View results immediately (if enabled by teacher)

#### 5. View Dashboard
- Go to: `http://localhost:8000/quiz/dashboard/`
- See your statistics:
  - Total attempts
  - Passed/Failed count
  - Average score
- View recent attempts
- Check performance per quiz

## URL Structure

### Student URLs
- `/` - Home page
- `/quiz/` - Quiz list
- `/quiz/login/` - Student login
- `/quiz/logout/` - Student logout
- `/quiz/dashboard/` - Student dashboard
- `/quiz/<id>/` - Quiz details
- `/quiz/<id>/start/` - Start quiz
- `/quiz/attempt/<id>/` - Take quiz
- `/quiz/attempt/<id>/result/` - Quiz results

### Admin URLs
- `/admin/` - Wagtail admin dashboard
- `/django-admin/` - Django admin panel
- `/quiz/<id>/analytics/` - Quiz analytics (staff only)

## Database Models

### Quiz (Page Model)
- Extends Wagtail Page
- Fields: description, duration, pass_percentage, max_attempts, settings
- Methods: is_available(), can_attempt(), get_total_marks()

### Question (Orderable)
- Linked to Quiz via ParentalKey
- Fields: question_text, question_type, marks, explanation
- Supports ordering/reordering

### AnswerOption (Orderable)
- Linked to Question via ParentalKey
- Fields: option_text, is_correct
- Supports ordering

### QuizAttempt
- Records student quiz attempts
- Fields: quiz, student, start_time, end_time, score, percentage
- Methods: calculate_score(), get_attempt_number()

### StudentAnswer
- Stores student's answers
- Links to QuizAttempt and Question
- Supports both option selection and text answers

### StudentProfile (Snippet)
- Extended user profile
- Fields: enrollment_number, phone, date_of_birth
- Methods: get_quiz_statistics()

## Styling

The application uses a minimal, wireframe-style design with:
- Simple borders and boxes
- Basic color scheme (blue, green, red for statuses)
- Clean typography
- Responsive layout
- No heavy frameworks (pure CSS)

## Configuration

### Settings (in base.py)
```python
INSTALLED_APPS = [
    ...
    "quiz",
    ...
]

LOGIN_URL = '/quiz/login/'
LOGIN_REDIRECT_URL = '/quiz/'
LOGOUT_REDIRECT_URL = '/quiz/login/'
```

## Features in Detail

### Question Types
1. **Single Choice**: Student selects one option (radio buttons)
2. **Multiple Choice**: Student selects multiple options (checkboxes)
3. **True/False**: Special case of single choice
4. **Short Answer**: Text input (requires manual evaluation)

### Scoring System
- Automatic scoring for objective questions
- All or nothing for multiple choice (all correct options must be selected)
- Percentage calculation based on total marks
- Pass/Fail based on configured pass percentage

### Timer Functionality
- Countdown timer displayed during quiz
- Warning when time is running low
- Auto-submit when time expires
- Time tracked per attempt

### Analytics Dashboard
Teachers can view:
- Total attempts and unique students
- Average score and pass rate
- Question-wise accuracy
- Score distribution chart
- Top performers list
- Recent attempts with details

## Tips & Best Practices

### For Teachers
1. **Test Quizzes**: Take your own quiz before publishing
2. **Clear Questions**: Write unambiguous questions
3. **Balanced Difficulty**: Mix easy and hard questions
4. **Explanations**: Always add explanations for learning
5. **Reasonable Time**: Allow sufficient time for students
6. **Multiple Attempts**: Consider allowing 2-3 attempts for practice

### For Students
1. **Read Carefully**: Read all questions thoroughly
2. **Time Management**: Keep an eye on the timer
3. **Review Answers**: Use available time to review
4. **Learn from Mistakes**: Read explanations after submission
5. **Practice**: Use multiple attempts to improve

## Troubleshooting

### Server Issues
```bash
# Restart server
python manage.py runserver

# Clear cache
python manage.py collectstatic --noinput
```

### Database Issues
```bash
# Reset migrations (careful - loses data)
python manage.py migrate quiz zero
python manage.py migrate
```

### Login Issues
- Ensure LOGIN_URL is set correctly
- Check user credentials
- Verify user is active

## Future Enhancements
- Email notifications
- Question banks
- Random question selection from pool
- PDF export of results
- Certificate generation
- Question categories/tags
- Image support in questions
- File upload questions
- Peer review system

## Support
For issues or questions, contact the admin or check the Django/Wagtail documentation.

## Version
- Django: 5.2.6
- Wagtail: 7.1
- Python: 3.13

Last Updated: October 1, 2025
