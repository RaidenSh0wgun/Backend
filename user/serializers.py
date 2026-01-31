from email.headerregistry import Group
from .models import *
from rest_framework import serializers
import uuid
from django.contrib.auth.hashers import make_password

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = '__all__'

class InstructorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorProfile
        fields = '__all__'

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(choices=['student', 'teacher'], write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role"]

    def create(self, validated_data):
        role = validated_data.pop("role", "student")
        
        user = User.objects.create(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=make_password(validated_data["password"])
        )
        
        if role == "teacher":
            teacher_group, _ = Group.objects.get_or_create(name="Teachers")
            user.groups.add(teacher_group)
            user.is_staff = True
            user.save()
            InstructorProfile.objects.create(
                user=user,
                instructor_id=f"INSTR_{uuid.uuid4().hex[:8].upper()}"
            )
        else:
            student_group, _ = Group.objects.get_or_create(name="Students")
            user.groups.add(student_group)
            user.save()
            StudentProfile.objects.create(
                user=user,
                student_id=f"STU_{uuid.uuid4().hex[:8].upper()}"
            )
        
        return user