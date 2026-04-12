from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .models import *
from .serializers import (
    StudentProfileSerializer,
    InstructorProfileSerializer,
    CurrentUserSerializer,
    RoleTokenObtainPairSerializer,
    AdminUserSerializer,
)
import uuid

# Create your views here.
def ensure_user_default_student(user):
    if user.is_superuser:
        return
    if hasattr(user, "instructorprofile"):
        return
    if hasattr(user, "studentprofile"):
        return
    student_group, _ = Group.objects.get_or_create(name="Students")
    user.groups.add(student_group)
    StudentProfile.objects.create(
        user=user,
        student_id=f"STU_{uuid.uuid4().hex[:8].upper()}",
        full_name=user.username,
    )


def promote_to_teacher(user):
    teacher_group, _ = Group.objects.get_or_create(name="Teachers")
    student_group, _ = Group.objects.get_or_create(name="Students")
    user.groups.remove(student_group)
    user.groups.add(teacher_group)
    user.is_staff = True
    user.save()
    if hasattr(user, "studentprofile"):
        user.studentprofile.delete()
    if not hasattr(user, "instructorprofile"):
        InstructorProfile.objects.create(
            user=user,
            instructor_id=f"INSTR_{uuid.uuid4().hex[:8].upper()}",
            full_name=user.username,
        )


def demote_to_student(user):
    teacher_group, _ = Group.objects.get_or_create(name="Teachers")
    student_group, _ = Group.objects.get_or_create(name="Students")
    user.groups.remove(teacher_group)
    user.groups.add(student_group)
    user.is_staff = False
    user.save()
    if hasattr(user, "instructorprofile"):
        user.instructorprofile.delete()
    if not hasattr(user, "studentprofile"):
        StudentProfile.objects.create(
            user=user,
            student_id=f"STU_{uuid.uuid4().hex[:8].upper()}",
            full_name=user.username,
        )


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

        ensure_user_default_student(user)

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
        ensure_user_default_student(request.user)
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


class AdminUserListView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        search = (request.query_params.get("search") or "").strip()
        role = (request.query_params.get("role") or "student").strip().lower()
        users = User.objects.all().order_by("username")

        if role == "student":
            users = users.filter(
                is_superuser=False,
            ).exclude(instructorprofile__isnull=False)
        elif role == "teacher":
            users = users.filter(is_superuser=False, instructorprofile__isnull=False)
        elif role == "all":
            users = users.exclude(is_superuser=True)
        else:
            return Response(
                {"detail": "Invalid role filter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if search:
            users = users.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(studentprofile__full_name__icontains=search)
                | Q(instructorprofile__full_name__icontains=search)
            ).distinct()

        serializer = AdminUserSerializer(users, many=True)
        return Response(serializer.data)


class AdminUserDetailView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get_object(self, user_id):
        return User.objects.get(id=user_id)

    def get(self, request, user_id):
        try:
            user = self.get_object(user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminUserSerializer(user)
        return Response(serializer.data)

    def patch(self, request, user_id):
        try:
            user = self.get_object(user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_superuser:
            return Response(
                {"detail": "Superuser accounts cannot be modified here."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = request.data.get("username")
        full_name = request.data.get("full_name")
        password = request.data.get("password")
        is_active = request.data.get("is_active")
        role = request.data.get("role")

        if username is not None:
            username = str(username).strip()
            if not username:
                return Response(
                    {"detail": "Username cannot be empty."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if User.objects.exclude(id=user.id).filter(username=username).exists():
                return Response(
                    {"detail": "A user with that username already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.username = username

        if is_active is not None:
            user.is_active = bool(is_active)

        if password is not None:
            password = str(password)
            if len(password) < 8:
                return Response(
                    {"detail": "Password must be at least 8 characters."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(password)

        if full_name is not None:
            full_name = str(full_name).strip()
            if hasattr(user, "instructorprofile"):
                user.instructorprofile.full_name = full_name
                user.instructorprofile.save(update_fields=["full_name"])
            else:
                ensure_user_default_student(user)
                user.studentprofile.full_name = full_name
                user.studentprofile.save(update_fields=["full_name"])

        if role is not None:
            role = str(role).strip().lower()
            if role == "teacher":
                promote_to_teacher(user)
            elif role == "student":
                demote_to_student(user)
            else:
                return Response(
                    {"detail": "Invalid role."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        user.save()
        ensure_user_default_student(user)
        serializer = AdminUserSerializer(user)
        return Response(serializer.data)

    def delete(self, request, user_id):
        try:
            user = self.get_object(user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        if user.is_superuser:
            return Response(
                {"detail": "Superuser accounts cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================
# Password Reset Views
# ==========================================

class PasswordResetRequestView(APIView):
    """
    POST /api/auth/password/reset/
    Request a password reset email with a confirmation link.
    Body: { "email": "user@example.com" }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists or not (security best practice)
            return Response(
                {"message": "If an account with that email exists, a password reset link has been sent."},
                status=status.HTTP_200_OK
            )

        # Generate token and UID
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Build reset link (frontend will handle this URL)
        frontend_url = request.data.get('frontend_url', 'http://localhost:5173')
        reset_link = f"{frontend_url}/reset-password/{uid}/{token}/"

        # Send email
        subject = "Password Reset Request - HorizonDev"
        message = f"""
        Hello {user.username},

        You requested a password reset for your HorizonDev account.
        
        Click the link below to reset your password:
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Thanks,
        HorizonDev Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response(
            {"message": "If an account with that email exists, a password reset link has been sent."},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    """
    POST /api/auth/password/reset/confirm/
    Confirm password reset with new password.
    Body: { "uid": "encoded_uid", "token": "reset_token", "new_password": "newpassword123" }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not all([uid, token, new_password]):
            return Response(
                {"error": "UID, token, and new_password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"error": "Invalid reset link"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate token
        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "Invalid or expired reset token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Password has been reset successfully"},
            status=status.HTTP_200_OK
        )
