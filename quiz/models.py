from django.db import models


# Create your models here.
class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name
    
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title

QUESTION_TYPES = [
    ('MC', 'Multiple Choice'),
    ('TF', 'True / False'),
    ('SA', 'Short Answer'),
]

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE, null=True, blank=True)
    question_type = models.CharField(
        max_length=2,
        choices=QUESTION_TYPES,
        default='MC'
    )
    text = models.TextField(null=True, blank=True)
    correct_text_answer = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.text
