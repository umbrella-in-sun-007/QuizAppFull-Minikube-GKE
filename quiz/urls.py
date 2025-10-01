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
    path('attempt/<int:attempt_id>/result/', views.quiz_result, name='quiz_result'),
    path('<int:quiz_id>/analytics/', views.quiz_analytics, name='quiz_analytics'),
]
