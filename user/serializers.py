from django.contrib.auth.models import Group, User
from .models import *
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer
import uuid


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = "__all__"


class InstructorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorProfile
        fields = "__all__"


class CurrentUserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "role")

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
                student_id=f"STU_{uuid.uuid4().hex[:8].upper()}",
                full_name=user.username,
            )

        if role == "teacher":
            if not (
                hasattr(user, "instructorprofile")
                or user.is_staff
                or user.groups.filter(name="Teachers").exists()
            ):
                raise serializers.ValidationError({"detail": "User is not a teacher."})
        if role == "student":
            if not hasattr(user, "studentprofile"):
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
                instructor_id=f"INSTR_{uuid.uuid4().hex[:8].upper()}",
                full_name=full_name,
            )
        else:
            student_group, _ = Group.objects.get_or_create(name="Students")
            user.groups.add(student_group)
            user.save()
            StudentProfile.objects.create(
                user=user,
                student_id=f"STU_{uuid.uuid4().hex[:8].upper()}",
                full_name=full_name,
            )

        return user


class AdminUserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "is_active", "role", "full_name")

    def get_role(self, obj):
        if obj.is_superuser:
            return "admin"
        if hasattr(obj, "instructorprofile"):
            return "teacher"
        return "student"

    def get_full_name(self, obj):
        if hasattr(obj, "instructorprofile"):
            return obj.instructorprofile.full_name
        if hasattr(obj, "studentprofile"):
            return obj.studentprofile.full_name
        return ""