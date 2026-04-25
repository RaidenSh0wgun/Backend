from django.contrib.auth.models import Group, User
from .models import *
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer

ALLOWED_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}
MAX_AVATAR_SIZE_BYTES = 50 * 1024 * 1024


class ProfileUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    full_name = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    sex = serializers.ChoiceField(choices=SEX_CHOICES, required=False, allow_blank=True)
    avatar_url = serializers.ImageField(required=False, allow_null=True)
    def validate_avatar_url(self, value):
        if value is None:
            return value
        content_type = getattr(value, "content_type", "") or ""
        if content_type not in ALLOWED_IMAGE_MIME_TYPES:
            raise serializers.ValidationError("Unsupported image type.")
        if getattr(value, "size", 0) > MAX_AVATAR_SIZE_BYTES:
            raise serializers.ValidationError("Image exceeds 50MB limit.")
        return value


class CurrentUserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    sex = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()
    courses = serializers.SerializerMethodField()
    enrolled_courses = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "role",
            "full_name",
            "bio",
            "sex",
            "avatar_url",
            "email_verified",
            "courses",
            "enrolled_courses",
        )
    def get_role(self, obj):
        if obj.is_superuser:
            return "admin"
        if hasattr(obj, "instructorprofile"):
            return "teacher"
        if hasattr(obj, "studentprofile"):
            return "student"
        if obj.is_staff or obj.groups.filter(name="Teachers").exists():
            return "teacher"
        return "student"
    def get_full_name(self, obj):
        if hasattr(obj, "instructorprofile"):
            return obj.instructorprofile.full_name
        if hasattr(obj, "studentprofile"):
            return obj.studentprofile.full_name
        return obj.get_full_name() or obj.username
    def get_bio(self, obj):
        if hasattr(obj, "instructorprofile"):
            return obj.instructorprofile.bio
        if hasattr(obj, "studentprofile"):
            return obj.studentprofile.bio
        return ""
    def get_sex(self, obj):
        if hasattr(obj, "instructorprofile"):
            return obj.instructorprofile.sex
        if hasattr(obj, "studentprofile"):
            return obj.studentprofile.sex
        return ""
    def get_avatar_url(self, obj):
        url = ""
        if hasattr(obj, "instructorprofile") and obj.instructorprofile.avatar_url:
            url = obj.instructorprofile.avatar_url.url
        elif hasattr(obj, "studentprofile") and obj.studentprofile.avatar_url:
            url = obj.studentprofile.avatar_url.url
        request = self.context.get("request") if hasattr(self, "context") else None
        if url and request is not None:
            if url.startswith('http://') or url.startswith('https://'):
                return url
            return request.build_absolute_uri(url)
        return url or ""
    def get_email_verified(self, obj):
        if hasattr(obj, "instructorprofile"):
            return obj.instructorprofile.email_verified
        if hasattr(obj, "studentprofile"):
            return obj.studentprofile.email_verified
        return False
    def get_courses(self, obj):
        if hasattr(obj, "instructorprofile"):
            return [course.title for course in obj.instructorprofile.assigned_courses.all()]
        return []
    def get_enrolled_courses(self, obj):
        if hasattr(obj, "studentprofile"):
            return [course.title for course in obj.studentprofile.enrolled_courses.all()]
        return []


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    role = serializers.CharField(required=False)
    def validate(self, attrs):
        data = super().validate(attrs)
        role = (self.initial_data.get("role") or "").strip().lower()
        user = self.user
        if (
            not user.is_superuser
            and not hasattr(user, "instructorprofile")
            and not hasattr(user, "studentprofile")
        ):
            student_group, _ = Group.objects.get_or_create(name="Students")
            user.groups.add(student_group)
            StudentProfile.objects.create(
                user=user,
                full_name=user.username,
            )
        if role == "teacher":
            if not (
                hasattr(user, "instructorprofile")
                or user.is_staff
                or user.groups.filter(name="Teachers").exists()
            ):
                SecurityAuditLog.objects.create(
                    user=user,
                    action="role_switch_attempt",
                    detail="User attempted to obtain a teacher token without teacher privileges.",
                    metadata={"requested_role": role},
                )
                raise serializers.ValidationError({"detail": "User is not a teacher."})
        if role == "student":
            if not hasattr(user, "studentprofile"):
                SecurityAuditLog.objects.create(
                    user=user,
                    action="role_switch_attempt",
                    detail="User attempted to obtain a student token without student profile.",
                    metadata={"requested_role": role},
                )
                raise serializers.ValidationError({"detail": "User is not a student."})
        return data


class CustomRegisterSerializer(RegisterSerializer):
    role = serializers.ChoiceField(choices=["student", "teacher"], required=False)
    full_name = serializers.CharField(required=False)
    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data["role"] = self.validated_data.get("role", "student")
        data["full_name"] = self.validated_data.get("full_name", "")
        return data
    def save(self, request):
        user = super().save(request)
        role = self.cleaned_data["role"]
        full_name = self.cleaned_data["full_name"]
        if role == "teacher":
            teacher_group, _ = Group.objects.get_or_create(name="Teachers")
            user.groups.add(teacher_group)
            user.is_staff = True
            user.save()
            InstructorProfile.objects.create(
                user=user,
                full_name=full_name,
            )
        else:
            student_group, _ = Group.objects.get_or_create(name="Students")
            user.groups.add(student_group)
            user.save()
            StudentProfile.objects.create(
                user=user,
                full_name=full_name,
            )
        return user


class AdminUserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    sex = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "is_active",
            "role",
            "full_name",
            "sex",
            "email_verified",
        )
    def get_role(self, obj):
        if obj.is_superuser:
            return "admin"
        if hasattr(obj, "instructorprofile"):
            return "teacher"
        if hasattr(obj, "studentprofile"):
            return "student"
        if obj.is_staff or obj.groups.filter(name="Teachers").exists():
            return "teacher"
        return "student"
    def get_full_name(self, obj):
        if hasattr(obj, "instructorprofile"):
            return obj.instructorprofile.full_name
        if hasattr(obj, "studentprofile"):
            return obj.studentprofile.full_name
        return obj.get_full_name() or obj.username
    def get_sex(self, obj):
        if hasattr(obj, "instructorprofile"):
            return obj.instructorprofile.sex
        if hasattr(obj, "studentprofile"):
            return obj.studentprofile.sex
        return ""
    def get_email_verified(self, obj):
        if hasattr(obj, "instructorprofile"):
            return obj.instructorprofile.email_verified
        if hasattr(obj, "studentprofile"):
            return obj.studentprofile.email_verified
        return False


class ReportSerializer(serializers.ModelSerializer):
    reporter_username = serializers.SerializerMethodField()
    reporter_email = serializers.SerializerMethodField()
    reporter_role = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = (
            "id",
            "title",
            "description",
            "category",
            "created_at",
            "reporter_username",
            "reporter_email",
            "reporter_role",
        )

    def get_reporter_username(self, obj):
        return obj.reporter_username

    def get_reporter_email(self, obj):
        return obj.reporter_email

    def get_reporter_role(self, obj):
        return obj.reporter_role

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return Report.objects.create(reporter=user, **validated_data)


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = '__all__'


class InstructorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorProfile
        fields = '__all__'
