from django.db import models


class Course(models.Model):

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    author = models.ForeignKey(
        'user.InstructorProfile',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='created_courses',
        verbose_name="Created by"
    )
    passkey = models.CharField(
        max_length=50,
        blank=False,
        null=True,
        help_text="Put PassKey"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=False)
    def __str__(self):
        return self.title


class Enrollment(models.Model):

    student = models.ForeignKey(
        'user.StudentProfile',
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    used_passkey = models.CharField(max_length=100, blank=True, null=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('student', 'course')
        indexes = [
            models.Index(fields=['student', 'course']),
        ]
    def __str__(self):
        return f"{self.student} enrolled in {self.course}"
