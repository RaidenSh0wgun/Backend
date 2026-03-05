from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Quiz, Question, Answer, QuizAttempt
from .serializers import (
    QuizSerializer,
    QuizDetailSerializer,
    QuizCreateUpdateSerializer,
    QuestionSerializer,
    QuizAttemptSerializer,
)


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
        serializer = QuestionSerializer(
            question, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
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
        total_questions = questions.count() or 1

        score = 0
        for question in questions:
            selected_answer_id = answers_map.get(str(question.id)) or answers_map.get(
                question.id
            )
            if not selected_answer_id:
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
            total=total_questions,
        )

        return Response({"score": attempt.score, "total": attempt.total})


class QuizAttemptsView(APIView):
    """List all attempts (scores) for a quiz. Instructor only."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, quiz_id, format=None):
        if not hasattr(request.user, "instructorprofile"):
            raise PermissionDenied("Only instructors can view quiz scores.")
        quiz = get_object_or_404(Quiz, id=quiz_id)
        if quiz.author and quiz.author.user != request.user:
            raise PermissionDenied("You can only view scores for your own quizzes.")
        attempts = quiz.attempts.select_related("student", "student__user").all().order_by("-created_at")
        serializer = QuizAttemptSerializer(attempts, many=True)
        return Response(serializer.data)


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