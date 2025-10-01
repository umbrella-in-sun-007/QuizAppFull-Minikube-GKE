from django.contrib import admin
from .models import QuizAttempt, StudentAnswer


# Django Admin for Quiz Attempts
@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'student', 'start_time', 'score', 'percentage', 'is_passed', 'is_completed')
    list_filter = ('is_completed', 'is_passed', 'quiz', 'start_time')
    search_fields = ('student__username', 'student__email', 'quiz__title')
    ordering = ['-start_time']
    readonly_fields = ('start_time', 'end_time', 'score', 'percentage', 'is_passed')
    
    def has_add_permission(self, request):
        return False


# Django Admin for Student Answers
@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'is_correct')
    list_filter = ('is_correct',)
    search_fields = ('attempt__student__username', 'question__question_text')
    readonly_fields = ('attempt', 'question', 'is_correct')
    
    def has_add_permission(self, request):
        return False



