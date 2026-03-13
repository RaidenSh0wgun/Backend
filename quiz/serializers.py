from rest_framework import serializers
from .models import Quiz, Question, Answer, QuizAttempt


class AnswerSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source="answer_text")

    class Meta:
        model = Answer
        fields = [
            "id",
            "text",
            "is_correct",
        ]
        extra_kwargs = {
            "is_correct": {"write_only": True},
        }


class QuestionSerializer(serializers.ModelSerializer):
    choices = AnswerSerializer(many=True, source="answers")

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "question_type",
            "correct_text",
            "choices",
        ]

    def create(self, validated_data):
        # Because `choices` uses `source="answers"`, DRF stores the validated
        # nested payload under the source key (`answers`) in `validated_data`.
        choices_data = validated_data.pop("answers", validated_data.pop("choices", []))
        question = Question.objects.create(**validated_data)

        for choice_data in choices_data:
            Answer.objects.create(Question=question, **choice_data)

        return question

    def update(self, instance, validated_data):
        instance.text = validated_data.get("text", instance.text)
        instance.question_type = validated_data.get(
            "question_type", instance.question_type
        )
        instance.correct_text = validated_data.get(
            "correct_text", instance.correct_text
        )

        choices_data = validated_data.pop("answers", validated_data.pop("choices", []))
        instance.answers.all().delete()
        for choice_data in choices_data:
            Answer.objects.create(Question=instance, **choice_data)

        instance.save()
        return instance


class QuizAttemptSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    username = serializers.CharField(source="student.user.username", read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ["id", "student", "student_name", "username", "score", "total", "created_at"]


class QuizSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    has_attempted = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "duration_minutes",
            "is_active",
            "course",
            "due_date",
            "created_at",
            "question_count",
            "has_attempted",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "question_count",
            "has_attempted",
        ]

    def get_question_count(self, obj):
        return obj.questions.count()

    def get_has_attempted(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        if not user or not hasattr(user, "studentprofile"):
            return False

        student = user.studentprofile
        return obj.attempts.filter(student=student).exists()


class QuizDetailSerializer(QuizSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta(QuizSerializer.Meta):
        fields = QuizSerializer.Meta.fields + ["questions"]


class QuizCreateUpdateSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "duration_minutes",
            "is_active",
            "course",
            "due_date",
            "questions",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        questions_data = validated_data.pop("questions", [])
        quiz = Quiz.objects.create(**validated_data)

        for question_data in questions_data:
            choices_data = question_data.pop("answers", [])
            question = Question.objects.create(quiz=quiz, **question_data)
            for choice_data in choices_data:
                Answer.objects.create(Question=question, **choice_data)

        return quiz

    def update(self, instance, validated_data):
        questions_data = validated_data.pop("questions", None)

        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get(
            "description", instance.description
        )
        instance.duration_minutes = validated_data.get(
            "duration_minutes", instance.duration_minutes
        )
        instance.course = validated_data.get("course", instance.course)
        instance.due_date = validated_data.get("due_date", instance.due_date)
        instance.save()

        if questions_data is None:
            return instance

        instance.questions.all().delete()
        for question_data in questions_data:
            choices_data = question_data.pop("answers", [])
            question = Question.objects.create(quiz=instance, **question_data)
            for choice_data in choices_data:
                Answer.objects.create(Question=question, **choice_data)

        return instance