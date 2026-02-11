from rest_framework import serializers
from .models import Course


class CourseSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(
        source="author.user.username", read_only=True
    )
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "author",
            "author_name",
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