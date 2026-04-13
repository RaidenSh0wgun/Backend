from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_save


SEX_CHOICES = [
    ("male", "Male"),
    ("female", "Female"),
    ("other", "Other"),
    ("prefer_not_to_say", "Prefer not to say"),
]


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='studentprofile')
    bio = models.TextField(blank=True)
    student_id = models.CharField(max_length=20, unique=True)
    enrolled_courses = models.ManyToManyField(
        "course.Course", related_name="students", blank=False
    )
    full_name = models.CharField(max_length=255, blank=True)
    sex = models.CharField(max_length=20, choices=SEX_CHOICES, blank=True)
    avatar_url = models.ImageField(upload_to='avatars/', blank=True, null=True)
    email_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.student_id}"


class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructorprofile')
    instructor_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True)
    assigned_courses = models.ManyToManyField(
        "course.Course", related_name="instructors", blank=False
    )
    full_name = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    sex = models.CharField(max_length=20, choices=SEX_CHOICES, blank=True)
    avatar_url = models.ImageField(upload_to='avatars/', blank=True, null=True)
    email_verified = models.BooleanField(default=False)

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
