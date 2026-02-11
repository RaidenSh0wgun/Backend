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
)


class ListCreateQuiz(generics.ListCreateAPIView):
    """
    List quizzes or create a new quiz with nested questions.
    """

    queryset = Quiz.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        # Use a simpler serializer for listing, and a nested one for creation.
        if self.request.method == "POST":
            return QuizCreateUpdateSerializer
        return QuizSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # Optional filter by course from query params.
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

        # Prevent multiple attempts for the same quiz by the same student.
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