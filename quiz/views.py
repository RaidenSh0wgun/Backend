from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime
from collections import Counter

from .models import Quiz, Question, Answer, QuizAttempt
from .serializers import (
    QuizSerializer,
    QuizDetailSerializer,
    QuizCreateUpdateSerializer,
    QuestionSerializer,
    QuizAttemptSerializer,
)


def recalculate_attempt_scores(quiz_id):
    """Recalculate scores for all attempts of a quiz."""
    attempts = QuizAttempt.objects.filter(quiz_id=quiz_id)
    for attempt in attempts:
        correct = 0
        total = 0
        questions = attempt.quiz.questions.all()

        for question in questions:
            total += 1
            user_answer = attempt.answers.get(str(question.id))

            if user_answer is None or user_answer == "":
                continue

            if question.question_type in ["identification", "enumeration"]:
                correct_text = (question.correct_text or "").strip()
                if question.question_type == "enumeration":
                    correct_values = [
                        value.strip().lower()
                        for value in correct_text.split("\n")
                        if value.strip()
                    ]
                    if correct_values:
                        submitted_values = [
                            value.strip().lower()
                            for value in (user_answer or "").split("\n")
                            if value.strip()
                        ]
                        correct_counter = Counter(correct_values)
                        correct += sum(
                            min(count, submitted_values.count(value))
                            for value, count in correct_counter.items()
                        )
                else:
                    if correct_text and str(user_answer).strip().lower() == correct_text.lower():
                        correct += 1
            else:
                # MCQ or TF
                try:
                    answer_id = int(user_answer)
                    selected = question.answers.filter(id=answer_id).first()
                    if selected and selected.is_correct:
                        correct += 1
                except (ValueError, TypeError):
                    pass

        attempt.score = correct
        attempt.total = total
        attempt.save(update_fields=["score", "total"])


class ListCreateQuiz(generics.ListCreateAPIView):
    queryset = Quiz.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return QuizCreateUpdateSerializer
        return QuizSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)

        user = self.request.user
        if hasattr(user, "instructorprofile"):
            return qs.filter(author=user.instructorprofile)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        instructor = getattr(user, "instructorprofile", None)
        if instructor is None:
            raise PermissionDenied("Only teachers can create quizzes.")

        serializer.save(author=instructor)


class RetrieveUpdateDestroyQuiz(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return QuizDetailSerializer
        return QuizCreateUpdateSerializer


class QuizQuestions(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, quiz_id, format=None):
        questions = Question.objects.filter(quiz_id=quiz_id)
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)

    def post(self, request, quiz_id, format=None):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        serializer = QuestionSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(quiz=quiz)
            return Response(
                {
                    "message": "Question created successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuizQuestionDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Question, pk=pk)

    def get(self, request, pk, format=None):
        question = self.get_object(pk)
        serializer = QuestionSerializer(question)
        return Response(serializer.data)

    def patch(self, request, pk, format=None):
        question = self.get_object(pk)
        quiz_id = question.quiz_id
        serializer = QuestionSerializer(
            question, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            
            # Recalculate scores for all attempts of this quiz
            recalculate_attempt_scores(quiz_id)
            
            return Response(
                {
                    "message": "Question updated successfully",
                    "data": serializer.data,
                }
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        question = self.get_object(pk)
        question.delete()
        return Response(
            {"message": "Question deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class SubmitQuiz(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, quiz_id, format=None):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        answers_map = request.data.get("answers", {})

        if not isinstance(answers_map, dict):
            return Response(
                {"detail": "Invalid answers payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        if not hasattr(user, "studentprofile"):
            raise PermissionDenied("Only students can submit quizzes.")

        student = user.studentprofile

        if QuizAttempt.objects.filter(student=student, quiz=quiz).exists():
            return Response(
                {"detail": "You have already completed this quiz."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        questions = quiz.questions.prefetch_related("answers").all()

        total_points = 0
        for question in questions:
            if question.question_type == "enumeration":
                correct_values = [
                    value.strip()
                    for value in (question.correct_text or "").split("\n")
                    if value.strip()
                ]
                total_points += len(correct_values) if correct_values else 1
            else:
                total_points += 1

        total_points = total_points or 1

        score = 0
        for question in questions:
            submitted_value = answers_map.get(str(question.id)) or answers_map.get(
                question.id
            )
            if submitted_value is None or submitted_value == "":
                continue

            if question.question_type == "enumeration":
                correct_values = [
                    value.strip().casefold()
                    for value in (question.correct_text or "").split("\n")
                    if value.strip()
                ]
                submitted_values = [
                    value.strip().casefold()
                    for value in str(submitted_value).split("\n")
                    if value.strip()
                ]
                if correct_values:
                    correct_counter = Counter(correct_values)
                    submitted_counter = Counter(submitted_values)
                    score += sum(
                        min(count, submitted_counter.get(value, 0))
                        for value, count in correct_counter.items()
                    )
                continue

            if question.question_type == "identification":
                correct = (question.correct_text or "").strip()
                submitted_text = str(submitted_value).strip()
                if not correct and hasattr(question, "answers"):
                    correct = (
                        question.answers.filter(is_correct=True)
                        .values_list("answer_text", flat=True)
                        .first()
                        or ""
                    ).strip()

                if correct and submitted_text.casefold() == correct.casefold():
                    score += 1
                continue

            # Multiple choice and True/False are scored by which answer option
            # the student selected (via answer id).
            try:
                selected_answer_id = int(submitted_value)
            except (TypeError, ValueError):
                continue

            try:
                selected = question.answers.get(id=selected_answer_id)
            except Answer.DoesNotExist:
                continue

            if selected.is_correct:
                score += 1

        attempt = QuizAttempt.objects.create(
            student=student,
            quiz=quiz,
            score=score,
            total=total_points,
            answers=answers_map,
        )

        # Clear in-progress timer when attempt is submitted.
        cache.delete(f"quiz_timer_start_{student.id}_{quiz.id}")

        return Response({"score": attempt.score, "total": attempt.total})


class QuizTimerView(APIView):
    """Server-backed quiz timer (doesn't reset when navigating away)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, quiz_id, format=None):
        quiz = get_object_or_404(Quiz, id=quiz_id)

        if not hasattr(request.user, "studentprofile"):
            raise PermissionDenied("Only students can take quiz timers.")

        student = request.user.studentprofile

        cache_key = f"quiz_timer_start_{student.id}_{quiz.id}"
        start_ts = cache.get(cache_key)
        now_ts = timezone.now().timestamp()

        if start_ts is None:
            start_ts = now_ts
            # Keep the timer around longer than quiz duration.
            timeout = quiz.duration_minutes * 60 + 60 * 24
            cache.set(cache_key, start_ts, timeout=timeout)

        elapsed = now_ts - float(start_ts)
        remaining_seconds = int(max(0, (quiz.duration_minutes * 60) - elapsed))

        return Response(
            {
                "started_at": datetime.fromtimestamp(
                    float(start_ts), tz=timezone.utc
                ).isoformat(),
                "remaining_seconds": remaining_seconds,
            }
        )


class QuizAttemptsView(APIView):
    """List quiz attempts (scores) for a quiz.

    - Instructors can view all attempts for quizzes they created.
    - Students can view only their own attempt.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, quiz_id, format=None):
        quiz = get_object_or_404(Quiz, id=quiz_id)

        if hasattr(request.user, "instructorprofile"):
            if quiz.author and quiz.author.user != request.user:
                raise PermissionDenied("You can only view scores for your own quizzes.")
            attempts = quiz.attempts.select_related("student", "student__user").all().order_by("-created_at")
        elif hasattr(request.user, "studentprofile"):
            student = request.user.studentprofile
            attempts = (
                quiz.attempts.filter(student=student)
                .select_related("student", "student__user")
                .order_by("-created_at")
            )
        else:
            raise PermissionDenied("Only authenticated users can view quiz attempts.")

        serializer = QuizAttemptSerializer(attempts, many=True)
        return Response(serializer.data)


class QuizAttemptDetail(APIView):
    """Retrieve or update a single quiz attempt.

    - Instructors can view any attempt for their quizzes.
    - Students can view their own attempt.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, quiz_id, attempt_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)

        if hasattr(self.request.user, "instructorprofile"):
            if quiz.author and quiz.author.user != self.request.user:
                raise PermissionDenied("You can only view attempts for your own quizzes.")
            return get_object_or_404(quiz.attempts, id=attempt_id)

        if hasattr(self.request.user, "studentprofile"):
            student = self.request.user.studentprofile
            return get_object_or_404(quiz.attempts, id=attempt_id, student=student)

        raise PermissionDenied("Only authenticated users can view quiz attempts.")

    def get(self, request, quiz_id, attempt_id, format=None):
        attempt = self.get_object(quiz_id, attempt_id)
        serializer = QuizAttemptSerializer(attempt)
        return Response(serializer.data)

    def patch(self, request, quiz_id, attempt_id, format=None):
        if not hasattr(request.user, "instructorprofile"):
            raise PermissionDenied("Only instructors can update quiz attempts.")
        attempt = self.get_object(quiz_id, attempt_id)
        
        serializer = QuizAttemptSerializer(
            attempt, data=request.data, partial=True
        )
        if serializer.is_valid():
            updated_attempt = serializer.save()
            
            # Recalculate score if answers were changed
            if "answers" in request.data:
                recalculate_attempt_scores(quiz_id)
                # Refresh attempt from DB
                attempt = QuizAttempt.objects.get(id=attempt_id)
            
            # Return updated attempt with recalculated score
            return Response(QuizAttemptSerializer(attempt).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PendingQuizzesView(APIView):
    """List quizzes the current student has not attempted yet (from enrolled courses)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        if not hasattr(request.user, "studentprofile"):
            raise PermissionDenied("Only students can view pending quizzes.")
        student = request.user.studentprofile
        enrolled_course_ids = student.enrolled_courses.values_list("id", flat=True)
        attempted_quiz_ids = QuizAttempt.objects.filter(student=student).values_list("quiz_id", flat=True)
        quizzes = Quiz.objects.filter(
            course_id__in=enrolled_course_ids
        ).exclude(id__in=attempted_quiz_ids).select_related("course").order_by("due_date")
        serializer = QuizSerializer(quizzes, many=True, context={"request": request})
        return Response(serializer.data)


class QuizViewDetail(APIView):
    """Quiz landing page data.

    Used by the student/teacher `quizview` screen:
    - quiz details (title/description/duration/question_count/has_attempted)
    - current student's attempt score (if the viewer is a student and has attempted)
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, quiz_id, format=None):
        quiz = get_object_or_404(Quiz, id=quiz_id)

        quiz_data = QuizSerializer(quiz, context={"request": request}).data

        attempt_payload = None
        if hasattr(request.user, "studentprofile"):
            student = request.user.studentprofile
            attempt = (
                quiz.attempts.filter(student=student).order_by("-created_at").first()
            )
            if attempt:
                attempt_payload = {
                    "id": attempt.id,
                    "score": attempt.score,
                    "total": attempt.total,
                    "effective_score": attempt.effective_score,
                    "created_at": attempt.created_at,
                }

        return Response({"quiz": quiz_data, "attempt": attempt_payload})


class AttemptedQuizzesView(APIView):
    """List quizzes the current student has already attempted."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        if not hasattr(request.user, "studentprofile"):
            raise PermissionDenied("Only students can view attempted quizzes.")

        student = request.user.studentprofile
        enrolled_course_ids = student.enrolled_courses.values_list("id", flat=True)
        attempted_quiz_ids = QuizAttempt.objects.filter(student=student).values_list(
            "quiz_id", flat=True
        )

        quizzes = (
            Quiz.objects.filter(
                course_id__in=enrolled_course_ids, id__in=attempted_quiz_ids
            )
            .select_related("course")
            .order_by("-created_at")
        )
        serializer = QuizSerializer(quizzes, many=True, context={"request": request})
        return Response(serializer.data)


class CalendarQuizzesView(APIView):
    """List quizzes with due dates for calendar display.

    Students see quizzes from enrolled courses.
    Teachers see quizzes they authored.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user

        if hasattr(user, "studentprofile"):
            student = user.studentprofile
            course_ids = student.enrolled_courses.values_list("id", flat=True)
            quizzes = Quiz.objects.filter(
                course_id__in=course_ids,
                due_date__isnull=False,
            )
        elif hasattr(user, "instructorprofile"):
            instructor = user.instructorprofile
            quizzes = Quiz.objects.filter(
                author=instructor,
                due_date__isnull=False,
            )
        else:
            raise PermissionDenied(
                "Only students and teachers can view calendar quizzes."
            )

        quizzes = quizzes.select_related("course").order_by("due_date")
        serializer = QuizSerializer(quizzes, many=True, context={"request": request})
        return Response(serializer.data)