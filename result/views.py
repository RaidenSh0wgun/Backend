from django.shortcuts import render
from rest_framework import generics, permissions
from .models import QuizResult
from .serializers import quizResultSerializer

# Create your views here.
class QuizResultView(generics.ListCreateAPIView):
    queryset = QuizResult.objects.all()
    serializer_class = quizResultSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class QuizResultDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = QuizResult.objects.all()
    serializer_class = quizResultSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]