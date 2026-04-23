from django.conf import settings
from django.db import models
from course.models import Course
from quiz.models import Quiz


class CalendarEvent(models.Model):
    EVENT_TYPES = (
        ('quiz_due', 'Quiz Deadline'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calendar_events'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, default='quiz_due')
    related_quiz = models.ForeignKey(Quiz, on_delete=models.SET_NULL, null=True, blank=True)
    related_course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'related_quiz')
        ordering = ['start']
    def __str__(self):
        return f"{self.title} for {self.user.username}"
