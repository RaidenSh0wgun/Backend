from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import Group, User
from .models import *
from .serializers import (
    StudentProfileSerializer,
    InstructorProfileSerializer,
    CurrentUserSerializer,
    RoleTokenObtainPairSerializer,
)
import uuid

# Create your views here.
class StudentProfileView(generics.RetrieveUpdateAPIView):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True).order_by('username')

class InstructorProfileView(generics.RetrieveUpdateAPIView):
    queryset = InstructorProfile.objects.all()
    serializer_class = InstructorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True).order_by("username")

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password1") or request.data.get("password")
        role = str(request.data.get("role") or "student").strip().lower()

        if not username or not password:
            return Response(
                {"detail": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"detail": "A user with that username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        if role == "teacher":
            teacher_group, _ = Group.objects.get_or_create(name="Teachers")
            user.groups.add(teacher_group)
            user.is_staff = True
            user.save()
            InstructorProfile.objects.create(
                user=user,
                instructor_id=f"INSTR_{uuid.uuid4().hex[:8].upper()}",
                full_name=username,
            )
        else:
            student_group, _ = Group.objects.get_or_create(name="Students")
            user.groups.add(student_group)
            user.save()
            StudentProfile.objects.create(
                user=user,
                student_id=f"STU_{uuid.uuid4().hex[:8].upper()}",
                full_name=username,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data)


class RoleTokenObtainPairView(TokenObtainPairView):
    serializer_class = RoleTokenObtainPairSerializer

class ChangeUserGroupView(generics.ListAPIView):
   
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        username = request.data.get("username")
        group_name = request.data.get("group")
        if not username or not group_name:
            return Response({"detail": "username and group are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail": "user not found"}, status=status.HTTP_404_NOT_FOUND)

       
        for g in ["Students", "Teachers"]:
            try:
                grp = Group.objects.get(name=g)
                user.groups.remove(grp)
            except Group.DoesNotExist:
                pass

        target_group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(target_group)
        user.save()
        return Response({"detail": f"{user.username} added to {group_name}"})