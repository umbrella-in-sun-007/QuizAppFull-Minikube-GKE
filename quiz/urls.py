from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.student_login, name='student_login'),
    path('logout/', views.student_logout, name='student_logout'),
    path('register/student/', views.student_register, name='student_register'),
    path('register/teacher/', views.teacher_register, name='teacher_register'),
    path('', views.quiz_list, name='quiz_list'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('<int:quiz_id>/start/', views.start_quiz, name='start_quiz'),
    path('attempt/<int:attempt_id>/', views.take_quiz, name='take_quiz'),
    path('attempt/<int:attempt_id>/check-time/', views.check_quiz_time, name='check_quiz_time'),
    path('attempt/<int:attempt_id>/save-progress/', views.save_quiz_progress, name='save_quiz_progress'),
    path('attempt/<int:attempt_id>/result/', views.quiz_result, name='quiz_result'),
    # New AJAX API endpoints for fully backend-driven attempt flow
    path('attempt/<int:attempt_id>/api/questions/', views.api_attempt_questions, name='api_attempt_questions'),
    path('attempt/<int:attempt_id>/api/status/', views.api_attempt_status, name='api_attempt_status'),
    path('attempt/<int:attempt_id>/api/question/<int:question_id>/', views.api_attempt_question, name='api_attempt_question'),
    path('attempt/<int:attempt_id>/api/question/<int:question_id>/answer/', views.api_save_answer, name='api_save_answer'),
    path('attempt/<int:attempt_id>/api/finalize/', views.api_finalize_attempt, name='api_finalize_attempt'),
    path('<int:quiz_id>/analytics/', views.quiz_analytics, name='quiz_analytics'),
    path('<int:quiz_id>/analytics/export/', views.export_quiz_analytics, name='export_quiz_analytics'),
]
