from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test

def is_teacher(user):
    return getattr(user, 'role', '').lower() == 'teacher'

@user_passes_test(is_teacher)
def create_quiz(request):
    if request.method == 'POST':
        quiz_title = request.POST.get('quiz_title', '').strip()
        quiz_description = request.POST.get('quiz_description', '').strip()
        if quiz_title:
            from .models import Quiz
            quiz = Quiz.objects.create(
                title=quiz_title,
                description=quiz_description,
                created_by=request.user
            )
            return redirect('quizzes:add_questions', quiz_id=quiz.id)
        else:
            error = "Quiz title is required."
            return render(request, 'quizzes/create_quiz.html', {'error': error, 'quiz_title': quiz_title, 'quiz_description': quiz_description})
    return render(request, 'quizzes/create_quiz.html')


@user_passes_test(is_teacher)
def add_questions(request, quiz_id):
    from .models import Quiz, Question, Option
    quiz = get_object_or_404(Quiz, id=quiz_id)
    success = False
    if request.method == 'POST':
        for i in range(1, 4):
            q_text = request.POST.get(f'question_{i}', '').strip()
            q_image = request.FILES.get(f'question_{i}_image')
            if q_text:
                question = Question.objects.create(
                    quiz=quiz,
                    text=q_text,
                    image=q_image
                )
                for opt in ['a', 'b', 'c', 'd']:
                    opt_text = request.POST.get(f'option_{i}_{opt}', '').strip()
                    opt_image = request.FILES.get(f'option_{i}_{opt}_image')
                    is_correct = request.POST.get(f'correct_{i}') == opt
                    if opt_text:
                        Option.objects.create(
                            question=question,
                            text=opt_text,
                            image=opt_image,
                            is_correct=is_correct
                        )
        success = True
    return render(request, 'quizzes/add_questions.html', {'quiz_id': quiz_id, 'quiz': quiz, 'success': success})
