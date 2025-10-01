from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count, Q
from .models import Quiz, QuizAttempt, StudentAnswer, Question, AnswerOption
import random


def student_login(request):
    """Student login view"""
    if request.user.is_authenticated:
        return redirect('quiz_list')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('quiz_list')
        else:
            messages.error(request, 'Invalid username or password.')
    
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
        
        quiz_data.append({
            'quiz': quiz,
            'can_attempt': can_attempt,
            'message': message,
            'attempts_count': attempts.count(),
            'best_score': best_attempt.percentage if best_attempt else None,
            'last_attempt': attempts.first()
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
    
    context = {
        'quiz': quiz,
        'can_attempt': can_attempt,
        'message': message,
        'attempts': attempts,
        'total_marks': quiz.get_total_marks()
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
    questions = list(quiz.questions.all())
    
    # Randomize questions if enabled
    if quiz.randomize_questions:
        random.shuffle(questions)
    
    if request.method == 'POST':
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
                selected_option_ids = request.POST.getlist(f'question_{question.id}')
                answer, created = StudentAnswer.objects.get_or_create(
                    attempt=attempt,
                    question=question
                )
                answer.selected_options.clear()
                
                for option_id in selected_option_ids:
                    try:
                        option = AnswerOption.objects.get(id=option_id, question=question)
                        answer.selected_options.add(option)
                    except AnswerOption.DoesNotExist:
                        pass
                
                answer.save()
        
        # Calculate score
        result = attempt.calculate_score()
        
        messages.success(request, f'Quiz submitted! You scored {result["percentage"]:.1f}%')
        return redirect('quiz_result', attempt_id=attempt_id)
    
    context = {
        'attempt': attempt,
        'quiz': quiz,
        'questions': questions
    }
    return render(request, 'quiz/take_quiz.html', context)


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
@login_required
def quiz_analytics(request, quiz_id):
    """Analytics for a specific quiz"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('quiz_list')
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Get all completed attempts
    attempts = QuizAttempt.objects.filter(quiz=quiz, is_completed=True)
    
    # Statistics
    total_attempts = attempts.count()
    unique_students = attempts.values('student').distinct().count()
    avg_score = attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0
    pass_rate = (attempts.filter(is_passed=True).count() / total_attempts * 100) if total_attempts > 0 else 0
    
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
            'accuracy': round(accuracy, 2)
        })
    
    # Score distribution
    score_ranges = [
        {'range': '0-20%', 'count': attempts.filter(percentage__lt=20).count()},
        {'range': '20-40%', 'count': attempts.filter(percentage__gte=20, percentage__lt=40).count()},
        {'range': '40-60%', 'count': attempts.filter(percentage__gte=40, percentage__lt=60).count()},
        {'range': '60-80%', 'count': attempts.filter(percentage__gte=60, percentage__lt=80).count()},
        {'range': '80-100%', 'count': attempts.filter(percentage__gte=80).count()},
    ]
    
    # Top performers
    top_performers = attempts.order_by('-percentage')[:10]
    
    context = {
        'quiz': quiz,
        'total_attempts': total_attempts,
        'unique_students': unique_students,
        'avg_score': round(avg_score, 2),
        'pass_rate': round(pass_rate, 2),
        'question_analysis': question_analysis,
        'score_distribution': score_ranges,
        'top_performers': top_performers,
        'recent_attempts': attempts.order_by('-start_time')[:20]
    }
    return render(request, 'quiz/analytics.html', context)

