from django.db import models
from django.utils.translation import gettext_lazy as _
from autoslug import AutoSlugField



# Create your models here.
class Quiz(models.Model):
    author = models.CharField(_("Author"), max_length=50, blank=True)
    title = models.CharField(_("Quiz Title"), max_length=100, unique=True, default="New Quiz")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def question_count(self):
        return self.questions.count()  
    
    class Meta:
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")  
        ordering = ["id"]

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name="questions", on_delete=models.CASCADE)
    title = models.CharField(max_length=200, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ["id"]

    def __str__(self):
        return self.title
        
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
        
class Course(models.Model):
    name = models.CharField(max_length=100, null=True, blank=False, unique=True)
    description = models.TextField()
    