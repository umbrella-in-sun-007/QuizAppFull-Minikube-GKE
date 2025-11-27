from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from .models import StudentProfile


class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="This will be used for login"
    )
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']  # Use email as username
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_staff = False  # Students are not staff
        
        if commit:
            user.save()
            # Add user to Students group
            student_group, created = Group.objects.get_or_create(name='Students')
            user.groups.add(student_group)
            
            # Create student profile
            StudentProfile.objects.create(user=user)
        return user


class TeacherRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="This will be used for login"
    )
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    employee_id = forms.CharField(max_length=50, required=False)
    department = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']  # Use email as username
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_staff = True  # Teachers are staff
        
        if commit:
            user.save()
            # Add user to Teachers group
            teacher_group, created = Group.objects.get_or_create(name='Teachers')
            user.groups.add(teacher_group)
            
            # Grant Wagtail access permissions
            from wagtail.models import Collection, GroupCollectionPermission
            from django.contrib.contenttypes.models import ContentType
            from wagtail.permission_policies import ModelPermissionPolicy
            
            # Add to Editors group in Wagtail
            try:
                from wagtail.models import GroupPagePermission
                from home.models import HomePage
                
                # Give page editing permissions
                root_page = HomePage.objects.first()
                if root_page:
                    GroupPagePermission.objects.get_or_create(
                        group=teacher_group,
                        page=root_page,
                        permission_type='add'
                    )
                    GroupPagePermission.objects.get_or_create(
                        group=teacher_group,
                        page=root_page,
                        permission_type='edit'
                    )
            except:
                pass
                
        return user


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
