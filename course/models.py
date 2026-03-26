from django.db import models
    
class Course(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    author = models.ForeignKey(
        'user.InstructorProfile',
        on_delete=models.CASCADE,
        related_name='created_courses',
        verbose_name="Created by",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.title


# class Enrollment(models.Model):
#     student = models.ForeignKey(
#         'user.StudentProfile',
#         on_delete=models.CASCADE,
#         related_name="enrollments"
#     )
    
#     course = models.ForeignKey(
#         Course,
#         on_delete=models.CASCADE,
#         related_name="enrollments"
#     )

#     enrolled_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('student', 'course')

#     def __str__(self):
#         return f"{self.student} enrolled in {self.course}"

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
    Passkey = models.CharField(max_length=100, blank=True, null=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} enrolled in {self.course}"