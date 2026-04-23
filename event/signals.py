from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from quiz.models import Quiz
from .models import CalendarEvent


@receiver(post_save, sender=Quiz)
def sync_quiz_deadline_to_calendar(sender, instance, created, **kwargs):
    if not instance.due_date or not instance.course_id:
        return
    course = instance.course
    if not course:
        return
    students = course.students.all()
    for student in students:
        user = student.user
        CalendarEvent.objects.update_or_create(
            user=user,
            related_quiz=instance,
            defaults={
                "title": f"Quiz: {instance.title}",
                "description": instance.description or "",
                "start": instance.due_date,
                "end": instance.due_date,
                "event_type": "quiz_due",
                "related_course": course,
            },
        )

    if instance.author and instance.author.user_id:
        CalendarEvent.objects.update_or_create(
            user=instance.author.user,
            related_quiz=instance,
            defaults={
                "title": f"Quiz due: {instance.title}",
                "description": instance.description or "",
                "start": instance.due_date,
                "end": instance.due_date,
                "event_type": "quiz_due",
                "related_course": course,
            },
        )
