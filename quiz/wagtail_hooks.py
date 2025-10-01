from django.contrib import messages
from django.http import HttpResponseRedirect
from wagtail import hooks
from wagtail.models import Page
from .models import Quiz


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
