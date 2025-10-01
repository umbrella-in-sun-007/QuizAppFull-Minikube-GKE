from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from wagtail import hooks
from wagtail.models import Page
from wagtail.admin import messages as wagtail_messages
from .models import Quiz, Question, AnswerOption
import csv
import io


@hooks.register('before_edit_page')
def check_quiz_edit_permission(request, page):
    """
    Hook to check if user has permission to edit a quiz before showing edit form
    """
    if isinstance(page, Quiz):
        quiz = page
        can_edit, message = quiz.can_edit_quiz(request.user)
        
        if not can_edit:
            messages.error(request, f"Permission Denied: {message}")
            return HttpResponseRedirect(f'/admin/pages/{page.id}/')
    
    return None


@hooks.register('before_delete_page')
def check_quiz_delete_permission(request, page):
    """
    Hook to check if user has permission to delete a quiz
    """
    if isinstance(page, Quiz):
        quiz = page
        can_delete, message = quiz.can_delete_quiz(request.user)
        
        if not can_delete:
            messages.error(request, f"Permission Denied: {message}")
            # Redirect back to page explorer or page view
            return HttpResponseRedirect(f'/admin/pages/{page.id}/')
    
    return None


@hooks.register('after_create_page')
def set_quiz_creator(request, page):
    """
    Automatically set the created_by field when a quiz is created
    """
    if isinstance(page, Quiz):
        if not page.created_by:
            page.created_by = request.user
            page.save_revision().publish()


@hooks.register('construct_page_action_menu')
def remove_edit_delete_for_non_owners(menu_items, request, context):
    """
    Remove edit and delete actions from page action menu for non-owners
    """
    page = context.get('page')
    
    if isinstance(page, Quiz):
        quiz = page
        user = request.user
        
        # Check if user is owner or superuser
        if not user.is_superuser and not quiz.is_owner(user):
            # Remove edit and delete actions
            menu_items[:] = [
                item for item in menu_items 
                if item.name not in ['edit', 'delete', 'unpublish']
            ]


@hooks.register('construct_page_listing_buttons')
def remove_edit_button_for_non_owners(buttons, page, user, context=None):
    """
    Remove edit button from page listings for non-owner teachers
    """
    if isinstance(page, Quiz):
        quiz = page
        
        # If user is not owner and not superuser, remove edit/delete buttons
        if not user.is_superuser and not quiz.is_owner(user):
            buttons[:] = [
                button for button in buttons 
                if button.label not in ['Edit', 'Delete']
            ]


def import_questions_csv(request, quiz_id):
    """
    View to handle CSV import of questions for a specific quiz
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check permissions
    if not request.user.is_staff:
        wagtail_messages.error(request, "You don't have permission to import questions.")
        return redirect('wagtailadmin_explore', quiz.get_parent().id)
    
    if not request.user.is_superuser and not quiz.is_owner(request.user):
        wagtail_messages.error(request, "You can only import questions to quizzes you created.")
        return redirect('wagtailadmin_explore', quiz.get_parent().id)
    
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            wagtail_messages.error(request, "Please select a CSV file to upload.")
            return render(request, 'quiz/admin/import_questions.html', {'quiz': quiz})
        
        if not csv_file.name.endswith('.csv'):
            wagtail_messages.error(request, "Please upload a valid CSV file.")
            return render(request, 'quiz/admin/import_questions.html', {'quiz': quiz})
        
        try:
            # Read CSV file
            csv_data = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            
            # Validate headers
            required_headers = ['question_text', 'question_type', 'marks', 'option_1', 'option_1_correct']
            headers = csv_reader.fieldnames
            
            if not all(header in headers for header in required_headers):
                wagtail_messages.error(
                    request, 
                    f"CSV file must contain these headers: {', '.join(required_headers)}"
                )
                return render(request, 'quiz/admin/import_questions.html', {'quiz': quiz})
            
            # Get current max sort_order
            max_sort_order = quiz.questions.count()
            
            imported_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):  # start=2 because row 1 is header
                try:
                    # Extract question data
                    question_text = row.get('question_text', '').strip()
                    question_type = row.get('question_type', '').strip().lower()
                    marks = row.get('marks', '1').strip()
                    explanation = row.get('explanation', '').strip()
                    is_required = row.get('is_required', 'true').strip().lower() in ['true', '1', 'yes']
                    
                    # Validate question data
                    if not question_text:
                        errors.append(f"Row {row_num}: Question text is required")
                        continue
                    
                    # Map question types
                    question_type_map = {
                        'mcq': 'single',
                        'single': 'single',
                        'single choice': 'single',
                        'single_choice': 'single',
                        'multiple': 'multiple',
                        'multi': 'multiple',
                        'multiple choice': 'multiple',
                        'multiple_choice': 'multiple',
                        'multichoice': 'multiple',
                        'true/false': 'true_false',
                        'true_false': 'true_false',
                        'tf': 'true_false',
                        'short': 'short_answer',
                        'short answer': 'short_answer',
                        'short_answer': 'short_answer',
                    }
                    
                    question_type = question_type_map.get(question_type, 'single')
                    
                    # Validate marks
                    try:
                        marks = int(marks)
                        if marks < 1:
                            marks = 1
                    except ValueError:
                        marks = 1
                    
                    # Create question
                    question = Question(
                        quiz=quiz,
                        question_text=question_text,
                        question_type=question_type,
                        marks=marks,
                        explanation=explanation,
                        is_required=is_required,
                        sort_order=max_sort_order + imported_count
                    )
                    question.save()
                    
                    # Add answer options
                    option_count = 0
                    for i in range(1, 11):  # Support up to 10 options
                        option_text_key = f'option_{i}'
                        option_correct_key = f'option_{i}_correct'
                        
                        option_text = row.get(option_text_key, '').strip()
                        if not option_text:
                            break
                        
                        option_correct = row.get(option_correct_key, '').strip().lower() in ['true', '1', 'yes']
                        
                        answer_option = AnswerOption(
                            question=question,
                            option_text=option_text,
                            is_correct=option_correct,
                            sort_order=option_count
                        )
                        answer_option.save()
                        option_count += 1
                    
                    # Validate that at least one option is correct for MCQ/Multiple choice
                    if question_type in ['single', 'multiple', 'true_false']:
                        correct_options = question.options.filter(is_correct=True).count()
                        if correct_options == 0:
                            errors.append(f"Row {row_num}: No correct answer specified for question")
                            question.delete()
                            continue
                        
                        # Validate single choice has only one correct answer
                        if question_type == 'single' and correct_options > 1:
                            errors.append(f"Row {row_num}: Single choice question should have only one correct answer")
                            question.delete()
                            continue
                    
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    continue
            
            # Show results
            if imported_count > 0:
                wagtail_messages.success(
                    request, 
                    f"Successfully imported {imported_count} question(s)."
                )
            
            if errors:
                error_message = "Errors encountered:\n" + "\n".join(errors[:10])  # Show first 10 errors
                if len(errors) > 10:
                    error_message += f"\n... and {len(errors) - 10} more errors"
                wagtail_messages.warning(request, error_message)
            
            # Redirect to quiz edit page
            return redirect('wagtailadmin_pages:edit', quiz.id)
            
        except Exception as e:
            wagtail_messages.error(request, f"Error processing CSV file: {str(e)}")
            return render(request, 'quiz/admin/import_questions.html', {'quiz': quiz})
    
    return render(request, 'quiz/admin/import_questions.html', {'quiz': quiz})


@hooks.register('register_admin_urls')
def register_import_questions_url():
    """
    Register custom admin URLs for CSV import
    """
    return [
        path('quiz/<int:quiz_id>/import-questions/', import_questions_csv, name='import_questions_csv'),
    ]


@hooks.register('register_page_listing_more_buttons')
def add_import_button(page, user, next_url=None):
    """
    Add 'Import Questions' button to quiz listing
    """
    from wagtail.admin.widgets.button import Button
    
    if isinstance(page, Quiz):
        if user.is_staff and (user.is_superuser or page.is_owner(user)):
            return [
                Button(
                    'Import Questions',
                    reverse('import_questions_csv', args=[page.id]),
                    attrs={'title': 'Import questions from CSV'},
                    priority=10
                )
            ]
    
    return []

