from django.contrib import admin
from .models import StudentProfile, InstructorProfile

# Register your models here.
admin.site.register(StudentProfile)
admin.site.register(InstructorProfile)