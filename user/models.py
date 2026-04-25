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
    enrolled_courses = models.ManyToManyField(
        "course.Course", related_name="students", blank=False
    )
    full_name = models.CharField(max_length=255, blank=True)
    sex = models.CharField(max_length=20, choices=SEX_CHOICES, blank=True)
    avatar_url = models.ImageField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user.username} - {self.user.id}"


class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructorprofile')
    department = models.CharField(max_length=100, blank=True)
    assigned_courses = models.ManyToManyField(
        "course.Course", related_name="instructors", blank=False
    )
    full_name = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    sex = models.CharField(max_length=20, choices=SEX_CHOICES, blank=True)
    avatar_url = models.ImageField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user.username} - {self.user.id}"


class SecurityAuditLog(models.Model):
    ACTION_CHOICES = [
        ("role_change", "Role Change"),
        ("role_switch_attempt", "Role Switch Attempt"),
        ("media_upload", "Media Upload"),
        ("email_verification_request", "Email Verification Request"),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="security_logs")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    detail = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.action} - {self.user_id or 'anonymous'}"


class Report(models.Model):
    CATEGORY_CHOICES = [
        ("bug", "Bug"),
        ("problem", "Problem"),
        ("feature", "Feature Request"),
        ("other", "Other"),
    ]
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reports")
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def reporter_username(self):
        return self.reporter.username if self.reporter else ""

    @property
    def reporter_email(self):
        return self.reporter.email if self.reporter else ""

    @property
    def reporter_role(self):
        if not self.reporter:
            return ""
        if self.reporter.is_superuser:
            return "admin"
        if hasattr(self.reporter, "instructorprofile"):
            return "teacher"
        return "student"

    def __str__(self):
        return f"{self.title} by {self.reporter_username or 'unknown'}"


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
