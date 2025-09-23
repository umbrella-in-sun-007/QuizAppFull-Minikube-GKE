from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('quizzes/create/', views.create_quiz, name='create_quiz'),
    path('quizzes/<int:quiz_id>/add-questions/',
         views.add_questions, name='add_questions'),
]
