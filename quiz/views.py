from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Quiz, Question, Answer
from .serializers import QuizSerializer, QuestionSerializer, AnswerSerializer
from django.http import Http404 #Followed through tutorial on youtube ("https://youtu.be/OLOQr3y_FZs")

# Create your views here.
class ListCreateQuiz(generics.ListCreateAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # self.request.user
        serializer.save(author=self.request.user.username)
    

class RetrieveUpdateDestroyQuiz(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

class QuizQuestions(APIView):
    def get(self, request, format=None, **kwargs):
        question = Question.objects.filter(quiz_id=kwargs["quiz_id"], author=request.user.username)
        serializer = QuestionSerializer(question, many=True)

        return Response(serializer.data)
    
    def post(self, request, format=None, **kwargs):
        quiz = Question.objects.get(id=kwargs["quiz_id"])
        serializer = QuestionSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(quiz=quiz)
            return Response({"message": "Question created successfully", "data": serializer.data},
                            status=status.HTTP_201_CREATED
                        )

class QuizQuestionDetail(APIView):
    def get_object(self, pk):
        try:
            return Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            raise Http404
        
    def get(self, request, pk, format=None):
        question = self.get_object(pk)
        serializer = QuestionSerializer(question)
        return Response(serializer.data)
    
    def patch(self, request, pk, format=None):
        question = self.get_object(pk)
        serializer = QuestionSerializer(question, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Question updated successfully", "data": serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk, format=None):
        question = self.get_object(pk)
        question.delete()
        return Response({"message": "Question deleted successfully"}, 
                        status=status.HTTP_204_NO_CONTENT
                    )