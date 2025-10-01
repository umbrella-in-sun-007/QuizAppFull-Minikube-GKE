from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from wagtail.models import Page, Orderable, ClusterableModel
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase


# Quiz Category Tag
class QuizTag(TaggedItemBase):
    content_object = ParentalKey(
        'Quiz',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )


# Quiz Model (Main Quiz Page)
class Quiz(Page):
    """
    Main Quiz model that teachers can create and manage from CMS
    """
    description = RichTextField(blank=True)
    duration_minutes = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        help_text="Quiz duration in minutes"
    )
    pass_percentage = models.IntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum percentage required to pass"
    )
    max_attempts = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1)],
        help_text="Maximum number of attempts allowed per student"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this quiz available for students to attempt?"
    )
    show_results_immediately = models.BooleanField(
        default=True,
        help_text="Show results to students immediately after submission"
    )
    randomize_questions = models.BooleanField(
        default=False,
        help_text="Randomize question order for each attempt"
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Quiz will be available from this date"
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Quiz will be available until this date"
    )
    tags = ClusterTaggableManager(through=QuizTag, blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel('description'),
        MultiFieldPanel([
            FieldPanel('duration_minutes'),
            FieldPanel('pass_percentage'),
            FieldPanel('max_attempts'),
        ], heading="Quiz Settings"),
        MultiFieldPanel([
            FieldPanel('is_active'),
            FieldPanel('show_results_immediately'),
            FieldPanel('randomize_questions'),
        ], heading="Display Options"),
        MultiFieldPanel([
            FieldPanel('start_date'),
            FieldPanel('end_date'),
        ], heading="Schedule"),
        FieldPanel('tags'),
        InlinePanel('questions', label="Questions"),
    ]

    parent_page_types = ['home.HomePage']
    subpage_types = []

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return self.title

    def is_available(self):
        """Check if quiz is currently available"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    def get_total_marks(self):
        """Calculate total marks for this quiz"""
        return sum(question.marks for question in self.questions.all())

    def get_student_attempts_count(self, user):
        """Get number of attempts by a student"""
        return QuizAttempt.objects.filter(quiz=self, student=user).count()

    def can_attempt(self, user):
        """Check if student can attempt this quiz"""
        if not self.is_available():
            return False, "Quiz is not available"
        
        attempts_count = self.get_student_attempts_count(user)
        if attempts_count >= self.max_attempts:
            return False, f"Maximum attempts ({self.max_attempts}) reached"
        
        return True, "You can attempt this quiz"


# Question Model
class Question(ClusterableModel, Orderable):
    """
    Questions for each quiz
    """
    QUESTION_TYPES = [
        ('single', 'Single Choice'),
        ('multiple', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    ]

    quiz = ParentalKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = RichTextField()
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default='single'
    )
    marks = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    explanation = RichTextField(
        blank=True,
        help_text="Explanation shown after answer submission"
    )
    is_required = models.BooleanField(default=True)

    panels = [
        FieldPanel('question_text'),
        FieldPanel('question_type'),
        FieldPanel('marks'),
        FieldPanel('explanation'),
        FieldPanel('is_required'),
        InlinePanel('options', label="Answer Options"),
    ]

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"Question {self.sort_order + 1} - {self.quiz.title}"


# Answer Option Model
class AnswerOption(Orderable):
    """
    Answer options for each question
    """
    question = ParentalKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(
        default=False,
        help_text="Mark this option as correct"
    )

    panels = [
        FieldPanel('option_text'),
        FieldPanel('is_correct'),
    ]

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.option_text


# Quiz Attempt Model
class QuizAttempt(models.Model):
    """
    Records of student quiz attempts
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_completed = models.BooleanField(default=False)
    is_passed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_time']
        verbose_name = "Quiz Attempt"
        verbose_name_plural = "Quiz Attempts"

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} - Attempt {self.get_attempt_number()}"

    def get_attempt_number(self):
        """Get the attempt number for this student"""
        return QuizAttempt.objects.filter(
            quiz=self.quiz,
            student=self.student,
            start_time__lte=self.start_time
        ).count()

    def calculate_score(self):
        """Calculate and save the score for this attempt"""
        total_marks = 0
        earned_marks = 0

        for answer in self.answers.all():
            question = answer.question
            total_marks += question.marks

            # Check if answer is correct
            if question.question_type == 'single':
                selected_options = answer.selected_options.all()
                if selected_options.count() == 1 and selected_options.first().is_correct:
                    earned_marks += question.marks
            
            elif question.question_type == 'multiple':
                selected_options = set(answer.selected_options.all())
                correct_options = set(question.options.filter(is_correct=True))
                if selected_options == correct_options:
                    earned_marks += question.marks
            
            elif question.question_type == 'true_false':
                selected_options = answer.selected_options.all()
                if selected_options.count() == 1 and selected_options.first().is_correct:
                    earned_marks += question.marks

        self.score = earned_marks
        self.percentage = (earned_marks / total_marks * 100) if total_marks > 0 else 0
        self.is_passed = self.percentage >= self.quiz.pass_percentage
        self.is_completed = True
        self.end_time = timezone.now()
        self.save()

        return {
            'score': self.score,
            'total': total_marks,
            'percentage': self.percentage,
            'passed': self.is_passed
        }


# Student Answer Model
class StudentAnswer(models.Model):
    """
    Student's answer for each question
    """
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_options = models.ManyToManyField(
        AnswerOption,
        blank=True,
        related_name='student_answers'
    )
    text_answer = models.TextField(
        blank=True,
        help_text="For short answer questions"
    )
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ['attempt', 'question']
        verbose_name = "Student Answer"
        verbose_name_plural = "Student Answers"

    def __str__(self):
        return f"{self.attempt.student.username} - Question {self.question.sort_order + 1}"


# Student Profile (extends User model)
@register_snippet
class StudentProfile(models.Model):
    """
    Extended profile for students
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    enrollment_number = models.CharField(max_length=50, unique=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    panels = [
        FieldPanel('user'),
        FieldPanel('enrollment_number'),
        FieldPanel('phone'),
        FieldPanel('date_of_birth'),
        FieldPanel('is_active'),
    ]

    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    def get_quiz_statistics(self):
        """Get statistics for this student"""
        attempts = QuizAttempt.objects.filter(student=self.user, is_completed=True)
        total_attempts = attempts.count()
        passed_attempts = attempts.filter(is_passed=True).count()
        
        if total_attempts > 0:
            avg_percentage = attempts.aggregate(models.Avg('percentage'))['percentage__avg']
        else:
            avg_percentage = 0

        return {
            'total_attempts': total_attempts,
            'passed_attempts': passed_attempts,
            'failed_attempts': total_attempts - passed_attempts,
            'average_percentage': round(avg_percentage, 2) if avg_percentage else 0
        }
