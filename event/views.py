from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import CalendarEvent
from .serializer import CalendarEventSerializer
from quiz.models import Quiz, QuizAttempt

# Create your views here.

class MyCalendarView(generics.ListAPIView):
    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if hasattr(user, "instructorprofile"):
            instructor = user.instructorprofile
            quizzes = Quiz.objects.filter(
                author=instructor, due_date__isnull=False
            ).select_related("course")

            for quiz in quizzes:
                CalendarEvent.objects.update_or_create(
                    user=user,
                    related_quiz=quiz,
                    defaults={
                        "title": f"Quiz due: {quiz.title}",
                        "description": quiz.description or "",
                        "start": quiz.due_date,
                        "end": quiz.due_date,
                        "event_type": "quiz_due",
                        "related_course": quiz.course,
                    },
                )

            return CalendarEvent.objects.filter(user=user).order_by("start")

        if hasattr(user, "studentprofile"):
            student = user.studentprofile

            pending_quizzes = (
                Quiz.objects.filter(
                    course__in=student.enrolled_courses.all(),
                    due_date__isnull=False,
                )
                .exclude(attempts__student=student)
                .select_related("course")
            )

            for quiz in pending_quizzes:
                CalendarEvent.objects.update_or_create(
                    user=user,
                    related_quiz=quiz,
                    defaults={
                        "title": f"Quiz: {quiz.title}",
                        "description": quiz.description or "",
                        "start": quiz.due_date,
                        "end": quiz.due_date,
                        "event_type": "quiz_due",
                        "related_course": quiz.course,
                    },
                )

            attempted_ids = QuizAttempt.objects.filter(student=student).values_list(
                "quiz_id", flat=True
            )
            return (
                CalendarEvent.objects.filter(user=user)
                .exclude(event_type="quiz_due", related_quiz_id__in=attempted_ids)
                .order_by("start")
            )

        return CalendarEvent.objects.filter(user=user).order_by("start")