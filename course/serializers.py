from rest_framework import serializers
from .models import Course
from user.models import StudentProfile


class EnrolledStudentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = StudentProfile
        fields = ["id", "user", "username", "full_name"]


class CourseSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(
        source="author.user.username", read_only=True
    )
    is_enrolled = serializers.SerializerMethodField()
    passkey = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "is_active",
            "author",
            "author_name",
            "passkey",
            "created_at",
            "updated_at",
            "is_enrolled",
        ]
        read_only_fields = [
            "id",
            "author",
            "author_name",
            "created_at",
            "updated_at",
            "is_enrolled",
        ]

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        if not request or not hasattr(request.user, "studentprofile"):
            return False

        student = request.user.studentprofile
        return student.enrolled_courses.filter(id=obj.id).exists()

    def validate_title(self, value):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not hasattr(user, "instructorprofile"):
            return value
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("Course title is required.")
        queryset = Course.objects.filter(
            author=user.instructorprofile,
            title__iexact=normalized,
        )
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("You already have a course with this title.")
        return normalized