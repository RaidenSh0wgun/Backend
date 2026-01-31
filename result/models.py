from django.db import models

# Create your models here.
class QuizResult(models.Model):
    quiz = models.ForeignKey('quiz.Quiz', related_name='results', on_delete=models.CASCADE)
    user = models.ForeignKey('user.StudentProfile', related_name='quiz_results', on_delete=models.CASCADE)
    score = models.FloatField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.quiz} : {self.score}"