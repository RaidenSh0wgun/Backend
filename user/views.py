from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from event.models import CalendarEvent
from quiz.models import Quiz, QuizAttempt

from .models import *
from .serializers import (
    AdminUserSerializer,
    CurrentUserSerializer,
    InstructorProfileSerializer,
    NotificationItemSerializer,
    ProfileUpdateSerializer,
    ReportSerializer,
    RoleTokenObtainPairSerializer,
    StudentProfileSerializer,
)


def coerce_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


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
        full_name=user.username,
    )


def get_user_profile(user):
    if hasattr(user, "instructorprofile"):
        return user.instructorprofile
    if hasattr(user, "studentprofile"):
        return user.studentprofile
    return None


def send_verification_email(user, frontend_url):
    profile = get_user_profile(user)
    if not profile or not user.email:
        return
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verify_link = f"{frontend_url}/verify-email/{uid}/{token}/"
    subject = "Verify your QuizApp email"
    message = f"""
    Hello {user.username},
    Please verify your email address by clicking the link below:
    {verify_link}
    If you did not request this, please ignore this email.
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        pass


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
            full_name=user.username,
        )


def build_notification_item(user, channel, source_type, source_id, title, created_at, metadata=None):
    return NotificationItem.objects.update_or_create(
        user=user,
        channel=channel,
        source_type=source_type,
        source_id=str(source_id),
        defaults={
            "title": title,
            "created_at": created_at,
            "metadata": metadata or {},
        },
    )[0]


def sync_notifications_for_user(user):
    now = timezone.now()

    if hasattr(user, "studentprofile"):
        student = user.studentprofile
        if student.email_verified:
            attempts = (
                QuizAttempt.objects.filter(student=student)
                .select_related("quiz")
                .order_by("-created_at")[:10]
            )
            attempted_quiz_ids = QuizAttempt.objects.filter(student=student).values_list("quiz_id", flat=True)
            pending_or_missed = (
                Quiz.objects.filter(course__in=student.enrolled_courses.all())
                .exclude(id__in=attempted_quiz_ids)
                .select_related("course")
                .order_by("due_date")[:10]
            )

            for attempt in attempts:
                score_text = ""
                if attempt.quiz.show_scores_after_quiz:
                    score_text = f" ({attempt.effective_score}/{attempt.total})"
                build_notification_item(
                    user=user,
                    channel="in_app",
                    source_type="submission_status",
                    source_id=f"attempt-{attempt.id}",
                    title=f"Submitted: {attempt.quiz.title}{score_text}",
                    created_at=attempt.created_at,
                    metadata={
                        "quiz_id": attempt.quiz_id,
                        "attempt_id": attempt.id,
                        "score": attempt.effective_score,
                        "total": attempt.total,
                    },
                )

            for quiz in pending_or_missed:
                if not quiz.due_date:
                    continue
                status_label = "Missed" if quiz.due_date < now else "Pending"
                build_notification_item(
                    user=user,
                    channel="in_app",
                    source_type="submission_status",
                    source_id=f"quiz-{quiz.id}",
                    title=f"{status_label}: {quiz.title}",
                    created_at=quiz.due_date,
                    metadata={
                        "quiz_id": quiz.id,
                        "course_id": quiz.course_id,
                        "status": status_label,
                    },
                )

            events = (
                CalendarEvent.objects.filter(user=user, event_type="quiz_due")
                .order_by("start")[:10]
            )
            for event in events:
                build_notification_item(
                    user=user,
                    channel="in_app",
                    source_type="calendar_deadline",
                    source_id=f"event-{event.id}",
                    title=event.title,
                    created_at=event.start,
                    metadata={
                        "event_id": event.id,
                        "quiz_id": event.related_quiz_id,
                        "course_id": event.related_course_id,
                    },
                )

    elif hasattr(user, "instructorprofile"):
        instructor = user.instructorprofile
        quizzes = (
            Quiz.objects.filter(author=instructor, due_date__isnull=False)
            .select_related("course")
            .order_by("due_date")[:10]
        )
        for quiz in quizzes:
            build_notification_item(
                user=user,
                channel="in_app",
                source_type="calendar_deadline",
                source_id=f"quiz-{quiz.id}",
                title=f"Quiz due: {quiz.title}",
                created_at=quiz.due_date,
                metadata={
                    "quiz_id": quiz.id,
                    "course_id": quiz.course_id,
                },
            )

        attempts = (
            QuizAttempt.objects.filter(quiz__author=instructor)
            .select_related("quiz", "student__user")
            .order_by("-created_at")[:10]
        )
        for attempt in attempts:
            build_notification_item(
                user=user,
                channel="in_app",
                source_type="submission_status",
                source_id=f"attempt-{attempt.id}",
                title=f"{attempt.student.user.username} submitted {attempt.quiz.title}",
                created_at=attempt.created_at,
                metadata={
                    "quiz_id": attempt.quiz_id,
                    "attempt_id": attempt.id,
                    "student_id": attempt.student_id,
                },
            )

    elif user.is_superuser:
        reports = (
            Report.objects.select_related("reporter")
            .order_by("-created_at")[:10]
        )
        for report in reports:
            reporter_name = report.reporter.username if report.reporter else "Unknown user"
            build_notification_item(
                user=user,
                channel="in_app",
                source_type="admin_report",
                source_id=f"report-{report.id}",
                title=f"Report from {reporter_name}: {report.title}",
                created_at=report.created_at,
                metadata={
                    "report_id": report.id,
                    "reporter_id": report.reporter_id,
                },
            )


def get_visible_notifications(user):
    sync_notifications_for_user(user)
    return NotificationItem.objects.filter(
        user=user,
        channel="in_app",
        is_removed=False,
    ).order_by("-created_at")


class StudentProfileView(generics.RetrieveUpdateAPIView):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset().order_by("user_id")
        return queryset


class InstructorProfileView(generics.RetrieveUpdateAPIView):
    queryset = InstructorProfile.objects.all()
    serializer_class = InstructorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset().order_by("user_id")
        return queryset


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password1") or request.data.get("password")
        role = "student"
        full_name = request.data.get("full_name") or username
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
        frontend_url = request.data.get("frontend_url") or "http://localhost:5173"
        if email:
            send_verification_email(user, frontend_url)
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
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        ensure_user_default_student(request.user)
        serializer = CurrentUserSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        if "role" in request.data:
            SecurityAuditLog.objects.create(
                user=user,
                action="role_switch_attempt",
                detail="User attempted to change role through profile update.",
                metadata={"requested_role": request.data.get("role")},
            )
            return Response({"detail": "Role updates are not allowed here."}, status=status.HTTP_403_FORBIDDEN)
        profile = get_user_profile(user)
        serializer = ProfileUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        username = serializer.validated_data.get("username")
        email = serializer.validated_data.get("email")
        full_name = serializer.validated_data.get("full_name")
        bio = serializer.validated_data.get("bio")
        sex = serializer.validated_data.get("sex")
        avatar_url = serializer.validated_data.get("avatar_url")
        if username is not None:
            username = str(username).strip()
            if not username:
                return Response({"detail": "Username cannot be blank."}, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.exclude(id=user.id).filter(username=username).exists():
                return Response({"detail": "A user with that username already exists."}, status=status.HTTP_400_BAD_REQUEST)
            user.username = username
        email_changed = False
        if email is not None:
            email = str(email).strip()
            if email and User.objects.exclude(id=user.id).filter(email=email).exists():
                return Response({"detail": "A user with that email already exists."}, status=status.HTTP_400_BAD_REQUEST)
            if email != user.email:
                email_changed = True
            user.email = email
        if full_name is not None:
            full_name = str(full_name).strip()
            if profile is not None:
                profile.full_name = full_name
            else:
                user.first_name = full_name
                user.last_name = ""
        if bio is not None and profile is not None:
            profile.bio = str(bio).strip()
        if sex is not None and profile is not None:
            profile.sex = str(sex).strip()
        if "avatar_url" in serializer.validated_data and profile is not None:
            if profile.avatar_url:
                profile.avatar_url.delete(save=False)
            if avatar_url:
                profile.avatar_url = avatar_url
                SecurityAuditLog.objects.create(
                    user=user,
                    action="media_upload",
                    detail="User uploaded a profile image.",
                    metadata={
                        "filename": getattr(avatar_url, "name", ""),
                        "size": getattr(avatar_url, "size", 0),
                        "content_type": getattr(avatar_url, "content_type", ""),
                    },
                )
            else:
                profile.avatar_url = None
        user.save()
        if profile is not None:
            if email_changed:
                profile.email_verified = False
                frontend_url = request.data.get("frontend_url") or "http://localhost:5173"
                if user.email:
                    send_verification_email(user, frontend_url)
            profile.save()
        serializer = CurrentUserSerializer(user, context={"request": request})
        return Response(serializer.data)


class EmailVerificationRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
        cooldown_key = f"email_verification_cooldown:{str(email).strip().lower()}"
        if cache.get(cooldown_key):
            return Response(
                {"message": "Please wait before requesting another verification email."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"message": "If an account with that email exists, a verification email has been sent."},
                status=status.HTTP_200_OK,
            )
        frontend_url = request.data.get("frontend_url") or "http://localhost:5173"
        send_verification_email(user, frontend_url)
        cache.set(cooldown_key, True, timeout=60)
        SecurityAuditLog.objects.create(
            user=user,
            action="email_verification_request",
            detail="Verification email requested.",
            metadata={"email": email},
        )
        return Response(
            {"message": "A verification email has been sent if the account exists."},
            status=status.HTTP_200_OK,
        )


class EmailVerificationConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        if not uid or not token:
            return Response({"error": "UID and token are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid verification link."}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired verification token."}, status=status.HTTP_400_BAD_REQUEST)
        profile = get_user_profile(user)
        if profile is not None:
            profile.email_verified = True
            profile.save()
        return Response({"message": "Email has been verified."}, status=status.HTTP_200_OK)


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
        email = request.data.get("email")
        full_name = request.data.get("full_name")
        password = request.data.get("password")
        is_active = request.data.get("is_active")
        role = request.data.get("role")
        email_verified = request.data.get("email_verified")
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
        if email is not None:
            email = str(email).strip()
            if email and User.objects.exclude(id=user.id).filter(email=email).exists():
                return Response(
                    {"detail": "A user with that email already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.email = email
        if is_active is not None:
            user.is_active = coerce_bool(is_active)
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
        if email_verified is not None:
            profile = get_user_profile(user)
            if profile is None:
                ensure_user_default_student(user)
                profile = get_user_profile(user)
            if profile is not None:
                profile.email_verified = coerce_bool(email_verified)
                profile.save(update_fields=["email_verified"])
        if role is not None:
            role = str(role).strip().lower()
            if role == "teacher":
                previous_role = "teacher" if hasattr(user, "instructorprofile") else "student"
                promote_to_teacher(user)
                SecurityAuditLog.objects.create(
                    user=request.user,
                    action="role_change",
                    detail=f"Admin changed user {user.username} role to teacher.",
                    metadata={"target_user_id": user.id, "from": previous_role, "to": "teacher"},
                )
            elif role == "student":
                previous_role = "teacher" if hasattr(user, "instructorprofile") else "student"
                demote_to_student(user)
                SecurityAuditLog.objects.create(
                    user=request.user,
                    action="role_change",
                    detail=f"Admin changed user {user.username} role to student.",
                    metadata={"target_user_id": user.id, "from": previous_role, "to": "student"},
                )
            else:
                return Response(
                    {"detail": "Invalid role."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        user.refresh_from_db()
        user.save()
        ensure_user_default_student(user)
        user.refresh_from_db()
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


class ReportListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get(self, request):
        role = (request.query_params.get("role") or "all").strip().lower()
        reports = (
            Report.objects.select_related("reporter")
            .prefetch_related(
                "reporter__studentprofile",
                "reporter__instructorprofile",
                "reporter__groups",
            )
            .filter(is_removed=False)
            .order_by("-created_at")
        )

        if role == "teacher":
            reports = reports.filter(
                reporter__is_superuser=False,
            ).filter(
                Q(reporter__instructorprofile__isnull=False)
                | Q(reporter__is_staff=True)
                | Q(reporter__groups__name="Teachers")
            ).distinct()
        elif role == "student":
            reports = reports.filter(
                reporter__is_superuser=False,
                reporter__studentprofile__isnull=False,
            ).distinct()
        elif role != "all":
            return Response(
                {"detail": "Invalid role filter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReportSerializer(reports, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ReportSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReportDetailView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get_object(self, report_id):
        return Report.objects.select_related("reporter").get(id=report_id)

    def patch(self, request, report_id):
        try:
            report = self.get_object(report_id)
        except Report.DoesNotExist:
            return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)
        if report.is_removed:
            return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)

        is_resolved = request.data.get("is_resolved")
        is_removed = request.data.get("is_removed")

        if is_resolved is not None:
            resolved = coerce_bool(is_resolved)
            report.is_resolved = resolved
            if resolved:
                report.resolved_at = timezone.now()
                report.resolved_by = request.user
            else:
                report.resolved_at = None
                report.resolved_by = None

        if is_removed is not None:
            removed = coerce_bool(is_removed)
            report.is_removed = removed
            if removed:
                report.removed_at = timezone.now()
                report.removed_by = request.user
            else:
                report.removed_at = None
                report.removed_by = None

        report.save()
        serializer = ReportSerializer(report)
        return Response(serializer.data)

    def delete(self, request, report_id):
        try:
            report = self.get_object(report_id)
        except Report.DoesNotExist:
            return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)
        if report.is_removed:
            return Response(status=status.HTTP_204_NO_CONTENT)
        report.is_removed = True
        report.removed_at = timezone.now()
        report.removed_by = request.user
        report.save(update_fields=["is_removed", "removed_at", "removed_by"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        visible_notifications = get_visible_notifications(request.user)
        serialized_notifications = NotificationItemSerializer(visible_notifications, many=True)
        unread_count = visible_notifications.filter(is_read=False).count()
        return Response(
            {
                "email": [
                    {
                        "type": "invitation",
                        "title": "Invitations",
                    },
                    {
                        "type": "reminder",
                        "title": "Reminders",
                    },
                    {
                        "type": "result_publication",
                        "title": "Result publications",
                    },
                ],
                "in_app": serialized_notifications.data,
                "unread_count": unread_count,
            }
        )

    def patch(self, request):
        updated_count = NotificationItem.objects.filter(
            user=request.user,
            channel="in_app",
            is_removed=False,
            is_read=False,
        ).update(is_read=True)
        return Response({"updated": updated_count})

    def delete(self, request):
        removed_count = NotificationItem.objects.filter(
            user=request.user,
            channel="in_app",
            is_removed=False,
        ).update(is_removed=True)
        return Response({"removed": removed_count})


class NotificationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, notification_id):
        return NotificationItem.objects.get(
            id=notification_id,
            user=request.user,
            channel="in_app",
        )

    def patch(self, request, notification_id):
        try:
            notification = self.get_object(request, notification_id)
        except NotificationItem.DoesNotExist:
            return Response({"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        if notification.is_removed:
            return Response({"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        is_read = request.data.get("is_read")
        if is_read is not None:
            notification.is_read = coerce_bool(is_read)
            notification.save(update_fields=["is_read"])
        serializer = NotificationItemSerializer(notification)
        return Response(serializer.data)

    def delete(self, request, notification_id):
        try:
            notification = self.get_object(request, notification_id)
        except NotificationItem.DoesNotExist:
            return Response({"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        if not notification.is_removed:
            notification.is_removed = True
            notification.save(update_fields=["is_removed"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"message": "If an account with that email exists, a password reset link has been sent."},
                status=status.HTTP_200_OK
            )
        profile = get_user_profile(user)
        frontend_url = request.data.get("frontend_url", "http://localhost:5173")
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{frontend_url}/reset-password/{uid}/{token}/"
        subject = "Password Reset Request - QuizApp"
        message = f"""
        Hello {user.username},
        You requested a password reset for your QuizApp account.
        Click the link below to reset your password:
        {reset_link}
        This link will expire in 1 hour.
        If you didn't request this, please ignore this email.
        Thanks,
        WHALMMS Team
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
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")
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
        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "Invalid or expired reset token"},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        return Response(
            {"message": "Password has been reset successfully"},
            status=status.HTTP_200_OK
        )


class PublicUserProfileView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        data = {
            "id": user.id,
            "username": user.username,
            "full_name": "",
            "email": user.email if user.is_active else "",
            "role": "",
            "bio": "",
            "sex": "",
            "avatar_url": "",
        }
        if user.is_superuser:
            data["role"] = "admin"
        elif hasattr(user, "instructorprofile"):
            profile = user.instructorprofile
            data["role"] = "teacher"
            data["full_name"] = profile.full_name
            data["bio"] = profile.bio or ""
            data["sex"] = profile.sex or ""
            if profile.avatar_url:
                data["avatar_url"] = request.build_absolute_uri(profile.avatar_url.url)
        elif hasattr(user, "studentprofile"):
            profile = user.studentprofile
            data["role"] = "student"
            data["full_name"] = profile.full_name
            data["bio"] = profile.bio or ""
            data["sex"] = profile.sex or ""
            if profile.avatar_url:
                data["avatar_url"] = request.build_absolute_uri(profile.avatar_url.url)
        else:
            data["role"] = "student"
            data["full_name"] = user.get_full_name() or user.username
        return Response(data)
