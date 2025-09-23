from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from .models import User, UserProfile

try:
    from .forms import CustomUserCreationForm, UserProfileForm, SimplePasswordResetForm
except ImportError:
    # Fallback if forms are not available yet
    CustomUserCreationForm = None
    UserProfileForm = None
    SimplePasswordResetForm = None

class CustomLoginView(LoginView):
    """Custom login view that redirects authenticated users and handles teacher approval"""
    
    def dispatch(self, request, *args, **kwargs):
        # Redirect authenticated users to dashboard
        if request.user.is_authenticated:
            return redirect('users:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Handle successful form validation with teacher approval checks"""
        try:
            return super().form_valid(form)
        except PermissionDenied as e:
            if "Teacher account pending approval" in str(e):
                messages.error(
                    self.request, 
                    'Your teacher account is pending admin approval. Please contact the administrator to activate your account.'
                )
                return self.form_invalid(form)
            raise
    
    def form_invalid(self, form):
        """Handle invalid form submission with custom teacher messaging"""
        username = form.cleaned_data.get('username')
        
        if username:
            try:
                user = User.objects.get(username=username)
                if user.role == 'teacher' and not user.is_active:
                    messages.error(
                        self.request,
                        'Your teacher account is pending admin approval. Please contact the administrator to activate your account.'
                    )
                    # Clear the form errors to show only our custom message
                    form.errors.clear()
            except User.DoesNotExist:
                pass
        
        return super().form_invalid(form)

def register(request):
    """User registration view"""
    # Redirect authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect('users:dashboard')
        
    if CustomUserCreationForm is None:
        messages.error(request, 'Registration is temporarily unavailable.')
        return redirect('users:login')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            username = form.cleaned_data.get('username')
            
            if user.role == 'teacher':
                messages.info(request, f'Teacher account created for {username}! Your account is pending admin approval. You will be able to login once an administrator activates your account.')
            else:
                messages.success(request, f'Account created for {username}!')
            
            return redirect('users:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    """User profile view"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'users/profile.html', {'form': form, 'user': request.user})

@login_required
@require_http_methods(["GET"])
def api_user_info(request):
    """API endpoint to get user information"""
    user = request.user
    data = {
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'is_student': user.is_student,
        'is_teacher': user.is_teacher,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }
    return JsonResponse(data)

def dashboard(request):
    """Dashboard view based on user role"""
    if not request.user.is_authenticated:
        return redirect('users:login')
    
    if request.user.is_student:
        return render(request, 'users/student_dashboard.html')
    elif request.user.is_teacher:
        return render(request, 'users/teacher_dashboard.html')
    else:
        return render(request, 'users/dashboard.html')

def logout_view(request):
    """Custom logout view"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('frontend:home')

def simple_password_reset(request):
    """Simple password reset without email verification"""
    # Note: Allow both authenticated and unauthenticated users to reset password
        
    if SimplePasswordResetForm is None:
        messages.error(request, 'Password reset is temporarily unavailable.')
        return redirect('users:login')
    
    if request.method == 'POST':
        form = SimplePasswordResetForm(request.POST, user_is_authenticated=request.user.is_authenticated)
        if form.is_valid():
            user = form.save()
            if request.user.is_authenticated:
                # If user was logged in, log them out and redirect to login
                logout(request)
                messages.success(request, 'Password has been changed successfully! Please login with your new password.')
            else:
                messages.success(request, 'Password has been reset successfully! You can now login with your new password.')
            return redirect('users:login')
    else:
        # Pre-fill username for authenticated users
        initial_data = {}
        if request.user.is_authenticated:
            initial_data['username'] = request.user.username
        form = SimplePasswordResetForm(initial=initial_data, user_is_authenticated=request.user.is_authenticated)
    
    return render(request, 'users/simple_password_reset.html', {'form': form})
