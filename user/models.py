from django.db import models
from django.contrib.auth.models import User
from quiz.models import Course
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_save


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='studentprofile')
    bio = models.TextField(blank=True)
    student_id = models.CharField(max_length=20, unique=True)
    enrolled_courses = models.ManyToManyField(Course, related_name='students', blank=False)
    full_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.student_id}"


class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructorprofile')
    instructor_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True)
    assigned_courses = models.ManyToManyField(Course, related_name='instructors', blank=False)
    full_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.instructor_id}" 
    
    
@receiver(post_save, sender=User)
def save_student_profile(sender, instance, **kwargs):
    try:
        instance.studentprofile.save()
    except StudentProfile.DoesNotExist:
        pass

@receiver(post_save, sender=User)
def save_instructor_profile(sender, instance, **kwargs):
    try:
        instance.instructorprofile.save()
    except InstructorProfile.DoesNotExist:
        pass