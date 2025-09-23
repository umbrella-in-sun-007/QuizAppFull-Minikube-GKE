from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from datetime import date
import math

class Institute(models.Model):
    """Institute/Institution model"""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Short code for the institute")
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class User(AbstractUser):
    """Custom User model with role-based authentication"""
    
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    institute = models.ForeignKey(Institute, on_delete=models.PROTECT, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    @property
    def is_teacher(self):
        return self.role == 'teacher'

class UserProfile(models.Model):
    """Extended profile information for users"""
    
    DEGREE_CHOICES = [
        ('btech', 'BTech (4 years)'),
        ('mtech', 'MTech (2 years)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Student-specific fields
    degree = models.CharField(max_length=10, choices=DEGREE_CHOICES, blank=True, null=True)
    year_of_admission = models.PositiveIntegerField(blank=True, null=True, help_text="Year when the student was admitted")
    student_id = models.CharField(max_length=20, blank=True, null=True)
    
    # Teacher-specific fields
    subject_specialization = models.CharField(max_length=100, blank=True)  # For teachers
    experience_years = models.PositiveIntegerField(null=True, blank=True)  # For teachers
    
    # Legacy field - keeping for backward compatibility
    academic_year = models.CharField(max_length=20, blank=True)  # For students (legacy)
    
    def clean(self):
        super().clean()
        if self.user and self.user.is_student:
            if self.year_of_admission and self.year_of_admission > date.today().year:
                raise ValidationError("Year of admission cannot be in the future.")
            if self.year_of_admission and self.year_of_admission < 1990:
                raise ValidationError("Year of admission seems too old.")
            
            # Check for unique student_id only if it's not empty
            if self.student_id and self.student_id.strip():
                existing = UserProfile.objects.filter(student_id=self.student_id.strip())
                if self.pk:
                    existing = existing.exclude(pk=self.pk)
                if existing.exists():
                    raise ValidationError("Student ID must be unique.")
    
    @property
    def current_semester(self):
        """Calculate current semester based on year of admission and current date"""
        if not self.year_of_admission or not self.user.is_student:
            return None
        
        current_date = date.today()
        admission_year = self.year_of_admission
        
        # Calculate total months since admission
        total_months = (current_date.year - admission_year) * 12 + current_date.month
        
        # Assuming academic year starts in July (month 7)
        # Adjust the calculation based on academic calendar
        if current_date.month >= 7:  # July to December
            academic_year_start = current_date.year
        else:  # January to June
            academic_year_start = current_date.year - 1
            
        # Calculate months from July of admission year
        if admission_year == academic_year_start:
            months_in_current_academic_year = current_date.month - 7 + 1 if current_date.month >= 7 else current_date.month + 6
        else:
            months_in_current_academic_year = current_date.month + 6 if current_date.month < 7 else current_date.month - 6
        
        # Calculate total academic years completed
        academic_years_completed = academic_year_start - admission_year
        if current_date.month < 7:
            academic_years_completed -= 1
            
        # Each semester is 6 months, so 2 semesters per academic year
        semester = (academic_years_completed * 2) + (1 if months_in_current_academic_year <= 6 else 2)
        
        # Validate against degree duration
        if self.degree == 'btech':
            max_semesters = 8  # 4 years * 2 semesters
        elif self.degree == 'mtech':
            max_semesters = 4  # 2 years * 2 semesters
        else:
            max_semesters = 8  # Default to BTech
            
        return min(semester, max_semesters)
    
    @property
    def current_academic_year(self):
        """Calculate current academic year based on year of admission"""
        if not self.year_of_admission or not self.user.is_student:
            return None
            
        current_date = date.today()
        
        # Academic year typically runs from July to June
        if current_date.month >= 7:  # July to December
            academic_year_start = current_date.year
            academic_year_end = current_date.year + 1
        else:  # January to June
            academic_year_start = current_date.year - 1
            academic_year_end = current_date.year
            
        return f"{academic_year_start}-{academic_year_end}"
    
    @property
    def year_of_study(self):
        """Calculate which year of study the student is in"""
        if not self.year_of_admission or not self.user.is_student:
            return None
            
        current_date = date.today()
        
        # Calculate academic years completed
        if current_date.month >= 7:  # July to December
            current_academic_year = current_date.year
        else:  # January to June
            current_academic_year = current_date.year - 1
            
        year_of_study = current_academic_year - self.year_of_admission + 1
        
        # Validate against degree duration
        if self.degree == 'btech':
            max_years = 4
        elif self.degree == 'mtech':
            max_years = 2
        else:
            max_years = 4  # Default to BTech
            
        return min(max(year_of_study, 1), max_years)
    
    def __str__(self):
        return f"Profile for {self.user.username}"
