from django.utils import timezone

from rest_framework import generics, permissions

from rest_framework.views import APIView

from rest_framework.response import Response

from rest_framework.exceptions import PermissionDenied

from .models import CalendarEvent

from .serializer import CalendarEventSerializer

from quiz.models import Quiz, QuizAttempt


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


class NotificationsView(APIView):

    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        now = timezone.now()
        notifications = []
        if hasattr(user, "studentprofile"):
            student = user.studentprofile
            attempts = (
                QuizAttempt.objects.filter(student=student)
                .select_related("quiz")
                .order_by("-created_at")[:10]
            )
            attempted_quiz_ids = [attempt.quiz_id for attempt in attempts]
            pending_or_missed = (
                Quiz.objects.filter(course__in=student.enrolled_courses.all())
                .exclude(id__in=attempted_quiz_ids)
                .select_related("course")
                .order_by("due_date")[:10]
            )
            for attempt in attempts:
                score_text = ""
                if attempt.quiz.show_scores_after_quiz:
                    score_text = f" ({attempt.effective_score}/{attempt.total})"
                notifications.append(
                    {
                        "channel": "in_app",
                        "type": "submission_status",
                        "title": f"Submitted: {attempt.quiz.title}{score_text}",
                        "created_at": attempt.created_at.isoformat(),
                    }
                )
            for quiz in pending_or_missed:
                if not quiz.due_date:
                    continue
                status = "Missed" if quiz.due_date < now else "Pending"
                notifications.append(
                    {
                        "channel": "in_app",
                        "type": "submission_status",
                        "title": f"{status}: {quiz.title}",
                        "created_at": quiz.due_date.isoformat(),
                    }
                )
            events = (
                CalendarEvent.objects.filter(user=user, event_type="quiz_due")
                .order_by("start")[:10]
            )
            for event in events:
                notifications.append(
                    {
                        "channel": "in_app",
                        "type": "calendar_deadline",
                        "title": event.title,
                        "created_at": event.start.isoformat(),
                    }
                )
        elif hasattr(user, "instructorprofile"):
            quizzes = (
                Quiz.objects.filter(author=user.instructorprofile, due_date__isnull=False)
                .select_related("course")
                .order_by("due_date")[:10]
            )
            for quiz in quizzes:
                notifications.append(
                    {
                        "channel": "in_app",
                        "type": "calendar_deadline",
                        "title": f"Quiz due: {quiz.title}",
                        "created_at": quiz.due_date.isoformat(),
                    }
                )
            attempts = (
                QuizAttempt.objects.filter(quiz__author=user.instructorprofile)
                .select_related("quiz", "student__user")
                .order_by("-created_at")[:10]
            )
            for attempt in attempts:
                notifications.append(
                    {
                        "channel": "in_app",
                        "type": "submission_status",
                        "title": f"{attempt.student.user.username} submitted {attempt.quiz.title}",
                        "created_at": attempt.created_at.isoformat(),
                    }
                )
        notifications.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return Response(
            {
                "email": [
                    {
                        "type": "invitation",
                        "title": "Invitations",
                    },
                    {
                        "type": "reminder",
                        "title": "Reminders",
                    },
                    {
                        "type": "result_publication",
                        "title": "Result publications",
                    },
                ],
                "in_app": notifications[:20],
            }
        )
