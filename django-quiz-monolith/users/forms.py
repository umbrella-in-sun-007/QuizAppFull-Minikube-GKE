from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import User, UserProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['academic_year', 'subject_specialization', 'institution', 
                 'experience_years', 'student_id']
        widgets = {
            'academic_year': forms.TextInput(attrs={'class': 'form-control'}),
            'subject_specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.instance.user if self.instance else None
        
        if user and user.is_student:
            # Show only student-relevant fields
            self.fields.pop('subject_specialization', None)
            self.fields.pop('experience_years', None)
        elif user and user.is_teacher:
            # Show only teacher-relevant fields
            self.fields.pop('academic_year', None)
            self.fields.pop('student_id', None)

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio', 'phone_number', 'date_of_birth']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SimplePasswordResetForm(forms.Form):
    """Simple password reset form without email verification"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-dark-700 bg-dark-800 text-white focus:outline-none focus:border-primary',
            'placeholder': 'Enter your username'
        })
    )
    admin_password = forms.CharField(
        label="Admin password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-dark-700 bg-dark-800 text-white focus:outline-none focus:border-primary',
            'placeholder': 'Enter admin password'
        }),
        required=False  # Will be required conditionally
    )
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-dark-700 bg-dark-800 text-white focus:outline-none focus:border-primary',
            'placeholder': 'Enter new password'
        })
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-dark-700 bg-dark-800 text-white focus:outline-none focus:border-primary',
            'placeholder': 'Confirm new password'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user_is_authenticated = kwargs.pop('user_is_authenticated', False)
        super().__init__(*args, **kwargs)
        
        # If user is authenticated, remove admin password field
        if self.user_is_authenticated:
            del self.fields['admin_password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("User with this username does not exist.")
        return username

    def clean_admin_password(self):
        admin_password = self.cleaned_data.get('admin_password')
        
        # Only validate admin password if user is not authenticated
        if not self.user_is_authenticated:
            if not admin_password:
                raise forms.ValidationError("Admin password is required for password reset.")
            
            # Check if admin password is correct
            try:
                admin_user = User.objects.filter(is_superuser=True).first()
                if not admin_user or not admin_user.check_password(admin_password):
                    raise forms.ValidationError("Invalid admin password.")
            except Exception:
                raise forms.ValidationError("Admin verification failed.")
        
        return admin_password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        
        return cleaned_data

    def save(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['new_password1']
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()
        return user
