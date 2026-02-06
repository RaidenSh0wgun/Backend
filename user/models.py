from django.db import models
from django.contrib.auth.models import User
from quiz.models import Course

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    enrolled_courses = models.ManyToManyField(Course, related_name='students', blank=False)

    def __str__(self):
        return f"{self.user.username} - {self.student_id}"

class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    instructor_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True)
    assigned_courses = models.ManyToManyField(Course, related_name='instructors', blank=False)

    def __str__(self):
        return f"{self.user.username} - {self.instructor_id}" 