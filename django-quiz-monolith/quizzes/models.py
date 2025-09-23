from django.db import models
from users.models import User

class Quiz(models.Model):
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)

class Question(models.Model):
	quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
	text = models.TextField()
	image = models.ImageField(upload_to='question_images/', blank=True, null=True)

class Option(models.Model):
	question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
	text = models.CharField(max_length=255)
	image = models.ImageField(upload_to='option_images/', blank=True, null=True)
	is_correct = models.BooleanField(default=False)
