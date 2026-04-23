from rest_framework import serializers
from .models import Quiz, Question, Answer, QuizAttempt


def normalize_answer(text, format_type):
    if not text:
        return ""
    text = str(text).strip()
    if format_type == 'ignore':
        return text.lower()
    elif format_type == 'upper':
        return text.upper()
    elif format_type == 'lower':
        return text.lower()
    elif format_type == 'capitalize':
        return text.capitalize()
    else:
        return text


def recalculate_attempt_scores(quiz_id):

    from collections import Counter
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
                user_answer_str = str(user_answer or "").strip()
                if question.question_type == "enumeration":
                    correct_values = [
                        normalize_answer(value.strip(), question.answer_format)
                        for value in correct_text.split("\n")
                        if value.strip()
                    ]
                    if correct_values:
                        submitted_values = [
                            normalize_answer(value.strip(), question.answer_format)
                            for value in user_answer_str.split("\n")
                            if value.strip()
                        ]
                        correct_counter = Counter(correct_values)
                        correct += sum(
                            min(count, submitted_values.count(value))
                            for value, count in correct_counter.items()
                        )
                else:
                    correct_normalized = normalize_answer(correct_text, question.answer_format)
                    user_normalized = normalize_answer(user_answer_str, question.answer_format)
                    if correct_normalized and user_normalized == correct_normalized:
                        correct += 1
            else:
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


class AnswerSerializer(serializers.ModelSerializer):

    text = serializers.CharField(source="answer_text")
    class Meta:
        model = Answer
        fields = [
            "id",
            "text",
            "is_correct",
        ]


class QuestionSerializer(serializers.ModelSerializer):

    choices = AnswerSerializer(many=True, source="answers")
    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "question_type",
            "correct_text",
            "answer_format",
            "choices",
        ]
    def create(self, validated_data):
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
        instance.answer_format = validated_data.get(
            "answer_format", instance.answer_format
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
    effective_score = serializers.ReadOnlyField()
    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "student",
            "student_name",
            "username",
            "score",
            "total",
            "answers",
            "score_override",
            "effective_score",
            "created_at",
        ]
        extra_kwargs = {
            "score_override": {"required": False, "allow_null": True},
            "answers": {"required": False},
        }


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
            "show_scores_after_quiz",
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
            "show_scores_after_quiz",
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
        recalculate_attempt_scores(instance.id)
        return instance
