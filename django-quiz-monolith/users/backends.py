from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

User = get_user_model()

class TeacherApprovalBackend(ModelBackend):
    """
    Custom authentication backend that handles teacher approval requirements
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False. Custom behavior for teachers.
        """
        is_active = getattr(user, 'is_active', None)
        
        # If user is inactive and is a teacher, provide specific feedback
        if not is_active and hasattr(user, 'role') and user.role == 'teacher':
            # This will be caught in the login view to show appropriate message
            raise PermissionDenied("Teacher account pending approval")
        
        return is_active or is_active is None
