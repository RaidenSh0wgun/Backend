from django.db import models
from django.utils.translation import gettext_lazy as _
# from autoslug import AutoSlugField



# Create your models here.
class Quiz(models.Model):
    author = models.ForeignKey(
        "user.InstructorProfile",
        on_delete=models.CASCADE,
        related_name="quizzes",
        null=True,
        blank=True,
    )
    course = models.ForeignKey(
        "course.Course",
        on_delete=models.CASCADE,
        related_name="quizzes",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True, help_text="Whether students can take this quiz")
    due_date = models.DateTimeField(null=True, blank=True, help_text="Quiz deadline for calendar")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["course", "title"]]

class Question(models.Model):
    TYPE_IDENTIFICATION = "identification"
    TYPE_MULTIPLE_CHOICE = "mcq"
    TYPE_TRUE_FALSE = "tf"

    TYPE_CHOICES = [
        (TYPE_IDENTIFICATION, "Identification"),
        (TYPE_MULTIPLE_CHOICE, "Multiple choice"),
        (TYPE_TRUE_FALSE, "True or false"),
    ]

    quiz = models.ForeignKey(Quiz, related_name="questions", on_delete=models.CASCADE)
    text = models.CharField(max_length=255, null=True, blank=True)
    question_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default=TYPE_MULTIPLE_CHOICE
    )
    correct_text = models.CharField(max_length=255, blank=True)
        
class Answer(models.Model):
    Question = models.ForeignKey(Question, related_name="answers", on_delete=models.CASCADE)
    answer_text = models.CharField(max_length=200, null=True, blank=True)
    is_correct = models.BooleanField(default=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")
        ordering = ["id"]

    def __str__(self):
        return self.answer_text


class QuizAttempt(models.Model):
    student = models.ForeignKey(
        "user.StudentProfile",
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "quiz")

    def __str__(self):
        return f"{self.student} - {self.quiz} ({self.score}/{self.total})"