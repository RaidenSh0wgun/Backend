from .models import QuizResult
from rest_framework import serializers

class quizResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizResult
        fields = '__all__'