from django.contrib import admin

from .models import StudentProfile, InstructorProfile

admin.site.register(StudentProfile)

admin.site.register(InstructorProfile)
