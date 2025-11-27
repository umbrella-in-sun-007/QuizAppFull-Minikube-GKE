from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Avg, Count, Q
from .models import Quiz, QuizAttempt, StudentAnswer, Question, AnswerOption
from .forms import StudentRegistrationForm, TeacherRegistrationForm, LoginForm
import random
import csv
from django.views.decorators.http import require_POST, require_GET
from django.forms.models import model_to_dict
from django.db import transaction


def student_register(request):
    """Student registration view"""
    if request.user.is_authenticated:
        return redirect('quiz_list')
    
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! You can now login.')
            return redirect('student_login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'quiz/student_register.html', {'form': form})


def teacher_register(request):
    """Teacher registration view"""
    if request.user.is_authenticated:
        return redirect('quiz_list')
    
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! You can now login to access the admin panel.')
            return redirect('student_login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = TeacherRegistrationForm()
    
    return render(request, 'quiz/teacher_register.html', {'form': form})


def student_login(request):
    """Student login view"""
    if request.user.is_authenticated:
        return redirect('quiz_list')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Try to get user by email
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.email}!')
            
            # Redirect based on user role
            if user.is_staff:
                return redirect('/admin/')
            else:
                return redirect('quiz_list')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'quiz/login.html')


def student_logout(request):
    """Student logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('student_login')


@login_required
def quiz_list(request):
    """Display all available quizzes for students"""
    quizzes = Quiz.objects.live().filter(is_active=True)
    
    quiz_data = []
    for quiz in quizzes:
        can_attempt, message = quiz.can_attempt(request.user)
        attempts = QuizAttempt.objects.filter(
            quiz=quiz,
            student=request.user
        ).order_by('-start_time')
        
        best_attempt = attempts.filter(is_completed=True).order_by('-percentage').first()
        
        # Check if user can view analytics for this quiz
        can_view_analytics = request.user.is_staff and (request.user.is_superuser or quiz.is_owner(request.user))
        
        quiz_data.append({
            'quiz': quiz,
            'can_attempt': can_attempt,
            'message': message,
            'attempts_count': attempts.count(),
            'best_score': best_attempt.percentage if best_attempt else None,
            'last_attempt': attempts.first(),
            'can_view_analytics': can_view_analytics
        })
    
    context = {
        'quiz_data': quiz_data
    }
    return render(request, 'quiz/quiz_list.html', context)


@login_required
def quiz_detail(request, quiz_id):
    """Display quiz details before starting"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    can_attempt, message = quiz.can_attempt(request.user)
    
    attempts = QuizAttempt.objects.filter(
        quiz=quiz,
        student=request.user
    ).order_by('-start_time')
    
    # Check if user can view analytics (staff and owner)
    can_view_analytics = request.user.is_staff and (request.user.is_superuser or quiz.is_owner(request.user))
    
    context = {
        'quiz': quiz,
        'can_attempt': can_attempt,
        'message': message,
        'attempts': attempts,
        'total_marks': quiz.get_total_marks(),
        'can_view_analytics': can_view_analytics
    }
    return render(request, 'quiz/quiz_detail.html', context)


@login_required
def start_quiz(request, quiz_id):
    """Start a new quiz attempt"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    can_attempt, message = quiz.can_attempt(request.user)
    
    if not can_attempt:
        messages.error(request, message)
        return redirect('quiz_detail', quiz_id=quiz_id)
    
    # Create new attempt
    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        student=request.user
    )
    
    return redirect('take_quiz', attempt_id=attempt.id)


@login_required
def take_quiz(request, attempt_id):
    """Take the quiz - show questions and handle submissions"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    
    if attempt.is_completed:
        messages.warning(request, 'This quiz attempt is already completed.')
        return redirect('quiz_result', attempt_id=attempt_id)
    
    quiz = attempt.quiz
    
    # Check if time has expired (backend validation)
    time_elapsed = (timezone.now() - attempt.start_time).total_seconds()
    time_limit = quiz.duration_minutes * 60
    time_remaining = time_limit - time_elapsed
    
    if time_remaining <= 0:
        # Time expired - auto-submit the quiz
        messages.warning(request, 'Time expired! Your quiz has been auto-submitted.')
        # Process any answers that were saved
        attempt.calculate_score()
        return redirect('quiz_result', attempt_id=attempt_id)
    
    questions = list(quiz.questions.all())
    
    # Randomize questions if enabled
    if quiz.randomize_questions:
        random.shuffle(questions)
    
    if request.method == 'POST':
        # Check time again before processing submission
        time_elapsed = (timezone.now() - attempt.start_time).total_seconds()
        time_remaining = time_limit - time_elapsed
        
        if time_remaining <= 0:
            messages.warning(request, 'Time expired! Your quiz has been auto-submitted.')
            attempt.calculate_score()
            return redirect('quiz_result', attempt_id=attempt_id)
        # Process quiz submission
        for question in questions:
            # Get selected answers
            if question.question_type == 'short_answer':
                text_answer = request.POST.get(f'question_{question.id}', '')
                answer, created = StudentAnswer.objects.get_or_create(
                    attempt=attempt,
                    question=question
                )
                answer.text_answer = text_answer
                answer.save()
            else:
                # Accept both legacy name 'question_<id>' and new 'question_<id>[]'
                selected_option_ids = request.POST.getlist(f'question_{question.id}[]') or request.POST.getlist(f'question_{question.id}')
                print(f"DEBUG: Form submission - Question {question.id} received option_ids: {selected_option_ids}")
                
                answer, created = StudentAnswer.objects.get_or_create(
                    attempt=attempt,
                    question=question
                )
                answer.selected_options.clear()
                
                valid_options = []
                for option_id in selected_option_ids:
                    try:
                        option = AnswerOption.objects.get(id=option_id, question=question)
                        answer.selected_options.add(option)
                        valid_options.append(option.option_text)
                    except AnswerOption.DoesNotExist:
                        print(f"DEBUG: Form submission - Invalid option ID {option_id} for question {question.id}")
                        pass
                
                answer.save()
                print(f"DEBUG: Form submission - Question {question.id} saved with options: {valid_options}")
        
        # Calculate score
        result = attempt.calculate_score()
        
        messages.success(request, f'Quiz submitted! You scored {result["percentage"]:.1f}%')
        return redirect('quiz_result', attempt_id=attempt_id)
    
    # Calculate time remaining to pass to template
    context = {
        'attempt': attempt,
        'quiz': quiz,
        'questions': questions,
        'time_remaining_seconds': int(time_remaining),
        # Security settings
        # Security settings - Always enforced
        'monitor_tab_switching': True,
        'max_tab_switches': quiz.max_tab_switches if quiz.max_tab_switches > 0 else 3,
        'auto_submit_on_violations': True,
        'enable_fullscreen': True,
        'disable_right_click': True,
        'disable_copy_paste': True,
        'prevent_browser_back': True,
    }
    return render(request, 'quiz/take_quiz.html', context)

# ================= AJAX Attempt API =================

def _serialize_option(option):
    return {
        'id': option.id,
        'text': option.option_text,
    }

def _serialize_question(question, include_options=True, shuffle_seed=None):
    data = {
        'id': question.id,
        'type': question.question_type,
        'marks': question.marks,
        'is_required': question.is_required,
        'html': question.question_text,  # rich text safe HTML
    }
    if include_options and question.question_type in ['single','multiple','true_false']:
        opts = list(question.options.all())
        if question.quiz.shuffle_options:
            if shuffle_seed is not None:
                random.Random(shuffle_seed).shuffle(opts)
            else:
                random.shuffle(opts)
        data['options'] = [_serialize_option(o) for o in opts]
    return data

def _ensure_question_order(session, attempt, questions, shuffle=False):
    key = f"attempt_{attempt.id}_order"
    if key not in session:
        q_ids = [q.id for q in questions]
        if shuffle:
            random.shuffle(q_ids)
        session[key] = q_ids
        session.modified = True
    return session[key]

@login_required
@require_GET
def api_attempt_questions(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    quiz = attempt.quiz
    base_qs = list(quiz.questions.all())
    if quiz.randomize_questions:
        # deterministic per session: shuffle copy only on first retrieval
        _ensure_question_order(request.session, attempt, base_qs, shuffle=True)
        ordered_ids = request.session.get(f"attempt_{attempt.id}_order")
        id_to_q = {q.id: q for q in base_qs}
        questions = [id_to_q[i] for i in ordered_ids if i in id_to_q]
    else:
        questions = base_qs
    data = [_serialize_question(q, include_options=False) for q in questions]
    return JsonResponse({'questions': data})

@login_required
@require_GET
def api_attempt_status(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    quiz = attempt.quiz
    time_elapsed = (timezone.now() - attempt.start_time).total_seconds()
    limit = quiz.duration_minutes * 60
    remaining = max(0, int(limit - time_elapsed))
    return JsonResponse({
        'completed': attempt.is_completed,
        'remaining_seconds': remaining,
        'score': float(attempt.score) if attempt.score is not None else None,
        'percentage': float(attempt.percentage) if attempt.percentage is not None else None,
    })

@login_required
@require_GET
def api_attempt_question(request, attempt_id, question_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    if attempt.is_completed:
        return JsonResponse({'error': 'Attempt completed'}, status=400)
    question = get_object_or_404(Question, id=question_id, quiz=attempt.quiz)
    answer = StudentAnswer.objects.filter(attempt=attempt, question=question).first()
    selected = []
    text_answer = ''
    if answer:
        selected = list(answer.selected_options.values_list('id', flat=True))
        text_answer = answer.text_answer
    return JsonResponse({
        'question': _serialize_question(question, include_options=True, shuffle_seed=f"{attempt.id}_{question.id}"),
        'selected_option_ids': selected,
        'text_answer': text_answer,
    })

@login_required
@require_POST
def api_save_answer(request, attempt_id, question_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    if attempt.is_completed:
        return JsonResponse({'error': 'Attempt completed'}, status=400)
    quiz = attempt.quiz
    # time check
    elapsed = (timezone.now() - attempt.start_time).total_seconds()
    if elapsed >= quiz.duration_minutes * 60:
        attempt.calculate_score()
        return JsonResponse({'error': 'Time expired', 'expired': True}, status=400)
    question = get_object_or_404(Question, id=question_id, quiz=quiz)
    answer, _ = StudentAnswer.objects.get_or_create(attempt=attempt, question=question)
    if question.question_type == 'short_answer':
        answer.text_answer = request.POST.get('text_answer', '')
        answer.save()
        return JsonResponse({'success': True})
    # options
    option_ids = request.POST.getlist('option_ids[]') or request.POST.getlist('option_ids')
    # de-duplicate while preserving order
    seen = set()
    filtered = []
    for oid in option_ids:
        if oid not in seen:
            seen.add(oid)
            filtered.append(oid)
    answer.selected_options.clear()
    valid_ids = []
    for oid in filtered:
        try:
            opt = AnswerOption.objects.get(id=oid, question=question)
            answer.selected_options.add(opt)
            valid_ids.append(opt.id)
        except AnswerOption.DoesNotExist:
            continue
    answer.save()
    return JsonResponse({'success': True, 'saved_option_ids': valid_ids})

@login_required
@require_POST
def api_finalize_attempt(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    if attempt.is_completed:
        return JsonResponse({
            'already_completed': True, 
            'score': float(attempt.score or 0), 
            'percentage': float(attempt.percentage or 0),
            'redirect_url': redirect('quiz_result', attempt_id=attempt.id).url
        })
    result = attempt.calculate_score()
    return JsonResponse({
        'completed': True,
        'score': float(result['score']),
        'total': float(result['total']),
        'percentage': float(result['percentage']),
        'passed': result['passed'],
        'redirect_url': redirect('quiz_result', attempt_id=attempt.id).url
    })


@login_required
def check_quiz_time(request, attempt_id):
    """API endpoint to check remaining time for a quiz attempt"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    
    if attempt.is_completed:
        return JsonResponse({
            'time_remaining': 0,
            'expired': True,
            'completed': True
        })
    
    quiz = attempt.quiz
    time_elapsed = (timezone.now() - attempt.start_time).total_seconds()
    time_limit = quiz.duration_minutes * 60
    time_remaining = max(0, time_limit - time_elapsed)
    
    # Auto-submit if time expired
    if time_remaining <= 0:
        attempt.calculate_score()
    
    return JsonResponse({
        'time_remaining': int(time_remaining),
        'expired': time_remaining <= 0,
        'completed': attempt.is_completed
    })


@login_required
def save_quiz_progress(request, attempt_id):
    """API endpoint to save quiz progress (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    
    if attempt.is_completed:
        return JsonResponse({'error': 'Quiz already completed'}, status=400)
    
    # Check time
    quiz = attempt.quiz
    time_elapsed = (timezone.now() - attempt.start_time).total_seconds()
    time_limit = quiz.duration_minutes * 60
    
    if time_elapsed >= time_limit:
        return JsonResponse({'error': 'Time expired', 'expired': True}, status=400)
    
    # Save the current answer
    question_id = request.POST.get('question_id')
    if not question_id:
        return JsonResponse({'error': 'Question ID required'}, status=400)
    
    try:
        question = Question.objects.get(id=question_id, quiz=quiz)
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Invalid question'}, status=400)
    
    # Save answer
    if question.question_type == 'short_answer':
        text_answer = request.POST.get('text_answer', '')
        answer, created = StudentAnswer.objects.get_or_create(
            attempt=attempt,
            question=question
        )
        answer.text_answer = text_answer
        answer.save()
    else:
        selected_option_ids = request.POST.getlist('option_ids')
        print(f"DEBUG: Question {question_id} received option_ids: {selected_option_ids}")
        
        answer, created = StudentAnswer.objects.get_or_create(
            attempt=attempt,
            question=question
        )
        answer.selected_options.clear()
        
        valid_options = []
        for option_id in selected_option_ids:
            try:
                option = AnswerOption.objects.get(id=option_id, question=question)
                answer.selected_options.add(option)
                valid_options.append(option.option_text)
            except AnswerOption.DoesNotExist:
                print(f"DEBUG: Invalid option ID {option_id} for question {question_id}")
                pass
        
        answer.save()
        print(f"DEBUG: Question {question_id} saved with options: {valid_options}")
    
    return JsonResponse({'success': True})


@login_required
def quiz_result(request, attempt_id):
    """Display quiz results"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    
    if not attempt.is_completed:
        messages.warning(request, 'Please complete the quiz first.')
        return redirect('take_quiz', attempt_id=attempt_id)
    
    # Get all answers with details
    answers = []
    for answer in attempt.answers.all():
        question = answer.question
        correct_options = question.options.filter(is_correct=True)
        selected_options = answer.selected_options.all()
        
        answers.append({
            'question': question,
            'selected_options': selected_options,
            'correct_options': correct_options,
            'is_correct': answer.is_correct,
            'text_answer': answer.text_answer
        })
    
    context = {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'answers': answers,
        'show_answers': attempt.quiz.show_results_immediately
    }
    return render(request, 'quiz/quiz_result.html', context)


@login_required
def student_dashboard(request):
    """Student dashboard with statistics and recent attempts"""
    user = request.user
    
    # Get all attempts
    attempts = QuizAttempt.objects.filter(student=user, is_completed=True)
    
    # Calculate statistics
    total_attempts = attempts.count()
    passed_attempts = attempts.filter(is_passed=True).count()
    failed_attempts = total_attempts - passed_attempts
    
    avg_percentage = attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0
    
    # Recent attempts
    recent_attempts = attempts.order_by('-start_time')[:10]
    
    # Quiz-wise performance
    quiz_performance = []
    quizzes = Quiz.objects.filter(attempts__student=user, attempts__is_completed=True).distinct()
    
    for quiz in quizzes:
        quiz_attempts = attempts.filter(quiz=quiz)
        best_attempt = quiz_attempts.order_by('-percentage').first()
        
        quiz_performance.append({
            'quiz': quiz,
            'attempts_count': quiz_attempts.count(),
            'best_percentage': best_attempt.percentage,
            'avg_percentage': quiz_attempts.aggregate(Avg('percentage'))['percentage__avg']
        })
    
    context = {
        'total_attempts': total_attempts,
        'passed_attempts': passed_attempts,
        'failed_attempts': failed_attempts,
        'avg_percentage': round(avg_percentage, 2),
        'recent_attempts': recent_attempts,
        'quiz_performance': quiz_performance
    }
    return render(request, 'quiz/student_dashboard.html', context)


# Analytics views for teachers (accessible from admin)
def format_duration_with_seconds(duration_minutes):
    """Helper function to format duration in minutes to h:m:s format"""
    total_seconds = duration_minutes * 60
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

@login_required
def quiz_analytics(request, quiz_id):
    """Analytics for a specific quiz - Enhanced with comprehensive statistics"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('quiz_list')
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if user can view analytics for this quiz
    # Only quiz owner or superuser can view analytics
    if not request.user.is_superuser and not quiz.is_owner(request.user):
        messages.error(request, 'You can only view analytics for quizzes you created.')
        return redirect('quiz_list')
    
    # Get all completed attempts
    attempts = QuizAttempt.objects.filter(quiz=quiz, is_completed=True).select_related('student')
    
    # Basic Statistics
    total_attempts = attempts.count()
    unique_students = attempts.values('student').distinct().count()
    avg_score = attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0
    pass_rate = (attempts.filter(is_passed=True).count() / total_attempts * 100) if total_attempts > 0 else 0
    
    # Get best attempt per student (for unique student analysis)
    from django.db.models import Max
    best_attempts_per_student = []
    # Use set to ensure unique student IDs, avoiding duplicates from default ordering
    student_ids = set(attempts.values_list('student_id', flat=True))
    
    for student_id in student_ids:
        student_attempts = attempts.filter(student_id=student_id)
        best_attempt = student_attempts.order_by('-percentage', 'end_time').first()
        if best_attempt:
            best_attempts_per_student.append(best_attempt)
    
    # Sort by percentage for ranking (Higher percentage first, then earlier submission time)
    best_attempts_per_student.sort(key=lambda x: (-x.percentage, x.end_time))
    
    # Top Performer (Highest Score)
    topper = best_attempts_per_student[0] if best_attempts_per_student else None
    
    # Top 10% Students
    top_10_percent_count = max(1, int(len(best_attempts_per_student) * 0.1))
    top_10_percent = best_attempts_per_student[:top_10_percent_count]
    
    # Time Analysis - Calculate duration for each attempt
    time_analysis = []
    for attempt in attempts:
        if attempt.start_time and attempt.end_time:
            total_seconds = (attempt.end_time - attempt.start_time).total_seconds()
            duration = total_seconds / 60  # in minutes
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            
            if hours > 0:
                duration_display = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                duration_display = f"{minutes}m {seconds}s"
            else:
                duration_display = f"{seconds}s"
            
            time_analysis.append({
                'attempt': attempt,
                'duration_minutes': round(duration, 2),
                'duration_display': duration_display
            })
    
    # Sort by duration
    time_analysis.sort(key=lambda x: x['duration_minutes'])
    
    # Fastest and Slowest
    fastest_attempts = time_analysis[:5] if time_analysis else []
    slowest_attempts = time_analysis[-5:][::-1] if time_analysis else []
    
    # Average completion time
    avg_duration = sum([t['duration_minutes'] for t in time_analysis]) / len(time_analysis) if time_analysis else 0
    
    # Question-wise analysis
    question_analysis = []
    for question in quiz.questions.all():
        answers = StudentAnswer.objects.filter(
            attempt__in=attempts,
            question=question
        )
        
        total_answers = answers.count()
        correct_answers = 0
        
        for answer in answers:
            if question.question_type in ['single', 'true_false']:
                if answer.selected_options.filter(is_correct=True).exists():
                    correct_answers += 1
            elif question.question_type == 'multiple':
                selected = set(answer.selected_options.all())
                correct = set(question.options.filter(is_correct=True))
                if selected == correct:
                    correct_answers += 1
        
        accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0
        
        question_analysis.append({
            'question': question,
            'total_answers': total_answers,
            'correct_answers': correct_answers,
            'accuracy': round(accuracy, 2),
            'difficulty': 'Easy' if accuracy >= 70 else 'Medium' if accuracy >= 40 else 'Hard'
        })
    
    # Score distribution
    score_ranges = [
        {'range': '0-20%', 'count': attempts.filter(percentage__lt=20).count(), 'label': 'Fail'},
        {'range': '20-40%', 'count': attempts.filter(percentage__gte=20, percentage__lt=40).count(), 'label': 'Poor'},
        {'range': '40-60%', 'count': attempts.filter(percentage__gte=40, percentage__lt=60).count(), 'label': 'Average'},
        {'range': '60-80%', 'count': attempts.filter(percentage__gte=60, percentage__lt=80).count(), 'label': 'Good'},
        {'range': '80-100%', 'count': attempts.filter(percentage__gte=80).count(), 'label': 'Excellent'},
    ]
    
    # Student Performance Summary (all attempts per student)
    student_performance = []
    for student_id in student_ids:
        student_attempts = attempts.filter(student_id=student_id)
        student = student_attempts.first().student
        # Get best attempt based on percentage (desc) and then end_time (asc)
        # Note: We can't easily sort by two fields in different directions in one ORM call if we want strict control
        # So we fetch all and sort in python or use multiple order_by
        # For finding the "best" attempt for a student, usually it's just max score. 
        # If scores are tied, the one with earlier completion is "better".
        best_attempt = student_attempts.order_by('-percentage', 'end_time').first()
        latest_attempt = student_attempts.order_by('-start_time').first()
        
        student_performance.append({
            'student': student,
            'total_attempts': student_attempts.count(),
            'best_score': best_attempt.percentage,
            'best_attempt_end_time': best_attempt.end_time,
            'latest_score': latest_attempt.percentage,
            'avg_score': student_attempts.aggregate(Avg('percentage'))['percentage__avg'],
            'passed': best_attempt.is_passed,
            'improvement': latest_attempt.percentage - student_attempts.order_by('start_time').first().percentage if student_attempts.count() > 1 else 0
        })
    
    # Sort by best score (desc) and then best attempt end time (asc)
    student_performance.sort(key=lambda x: (-x['best_score'], x['best_attempt_end_time']))
    
    # Recent attempts
    recent_attempts = attempts.order_by('-start_time')[:20]
    
    context = {
        'quiz': quiz,
        'total_attempts': total_attempts,
        'unique_students': unique_students,
        'avg_score': round(avg_score, 2),
        'pass_rate': round(pass_rate, 2),
        
        # Top Performers
        'topper': topper,
        'top_10_percent': top_10_percent,
        'top_10_percent_count': top_10_percent_count,
        
        # Time Analysis
        'fastest_attempts': fastest_attempts,
        'slowest_attempts': slowest_attempts,
        'avg_duration_minutes': round(avg_duration, 2),
        'avg_duration_display': format_duration_with_seconds(avg_duration),
        
        # Question Analysis
        'question_analysis': question_analysis,
        'score_distribution': score_ranges,
        
        # Student Performance
        'student_performance': student_performance,
        'recent_attempts': recent_attempts,
    }
    return render(request, 'quiz/analytics.html', context)


@login_required
def export_quiz_analytics(request, quiz_id):
    """Export quiz analytics to CSV/Excel"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('quiz_list')
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check permissions (same as analytics)
    if not request.user.is_superuser and not quiz.is_owner(request.user):
        messages.error(request, 'You can only export analytics for quizzes you created.')
        return redirect('quiz_list')
    
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{quiz.title}_analytics.csv"'
    
    writer = csv.writer(response)
    # Header row
    writer.writerow(['Student Email', 'Student Name', 'Score', 'Total Marks', 'Percentage', 'Status', 'Date Time'])
    
    # Get completed attempts
    attempts = QuizAttempt.objects.filter(quiz=quiz, is_completed=True).select_related('student').order_by('-start_time')
    
    total_marks = quiz.get_total_marks()
    
    for attempt in attempts:
        writer.writerow([
            attempt.student.email,
            attempt.student.get_full_name() or attempt.student.username,
            attempt.score,
            total_marks,
            f"{attempt.percentage}%",
            "Passed" if attempt.is_passed else "Failed",
            attempt.end_time.strftime("%Y-%m-%d %H:%M:%S") if attempt.end_time else "N/A"
        ])
        
    return response

