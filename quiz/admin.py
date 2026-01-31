from django.contrib import admin
from .models import Quiz, Question, Category, Course

# Register your models here.
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Category)
admin.site.register(Course)

