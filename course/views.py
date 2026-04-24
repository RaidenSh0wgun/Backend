from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions, status

from rest_framework.exceptions import PermissionDenied, ValidationError

from rest_framework.pagination import PageNumberPagination

from rest_framework.response import Response

from rest_framework.views import APIView

from .serializers import CourseSerializer, EnrolledStudentSerializer

from .models import Course


class CourseListCreate(generics.ListCreateAPIView):

    queryset = Course.objects.all().order_by("title")
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "instructorprofile"):
            return Course.objects.filter(author__user=user).order_by("title")
        return Course.objects.filter(is_active=True).order_by("title")
    def perform_create(self, serializer):
        user = self.request.user
        instructor = getattr(user, "instructorprofile", None)
        if instructor is None:
            raise PermissionDenied("Only teachers can create courses.")
        serializer.save(author=instructor)


class CourseRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "instructorprofile"):
            return Course.objects.filter(author__user=user)
        return Course.objects.filter(is_active=True)
    def perform_update(self, serializer):
        user = self.request.user
        instructor = getattr(user, "instructorprofile", None)
        if instructor is None:
            raise PermissionDenied("Only teachers can update courses.")
        serializer.save(author=instructor)
    def perform_destroy(self, instance):
        user = self.request.user
        if not (hasattr(user, "instructorprofile") or user.is_staff):
            raise PermissionDenied("Only teachers can delete courses.")
        instance.delete()


class CourseList(generics.ListAPIView):

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "instructorprofile"):
            return Course.objects.filter(author__user=user)
        if hasattr(user, "studentprofile"):
            return user.studentprofile.enrolled_courses.filter(is_active=True).order_by("title")
        return Course.objects.filter(is_active=True)


class EnrolledCoursesList(APIView):

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination
    def get(self, request, format=None):
        if not hasattr(request.user, "studentprofile"):
            return Response([])
        student = request.user.studentprofile
        courses = student.enrolled_courses.filter(is_active=True).order_by("title")
        paginator = self.pagination_class()
        paginated_courses = paginator.paginate_queryset(courses, request, view=self)
        serializer = CourseSerializer(paginated_courses, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class CourseDetail(generics.RetrieveAPIView):

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "instructorprofile"):
            return Course.objects.filter(author__user=user)
        return Course.objects.filter(is_active=True)


class EnrollCourseView(APIView):

    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk, format=None):
        if not hasattr(request.user, "studentprofile"):
            raise PermissionDenied("Only students can enroll in courses.")
        course = get_object_or_404(Course, pk=pk, is_active=True)
        passkey = request.data.get("passkey")
        if course.passkey:
            if passkey is None or str(passkey).strip() != course.passkey:
                raise ValidationError({"passkey": "Invalid passkey for this course."})
        student = request.user.studentprofile
        student.enrolled_courses.add(course)
        try:
            from event.models import CalendarEvent
        except Exception:
            CalendarEvent = None
        if CalendarEvent is not None:
            quizzes = course.quizzes.filter(due_date__isnull=False)
            for quiz in quizzes:
                CalendarEvent.objects.update_or_create(
                    user=request.user,
                    related_quiz=quiz,
                    defaults={
                        "title": f"Quiz: {quiz.title}",
                        "description": quiz.description or "",
                        "start": quiz.due_date,
                        "end": quiz.due_date,
                        "event_type": "quiz_due",
                        "related_course": course,
                    },
                )
        serializer = CourseSerializer(course, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    def delete(self, request, pk, format=None):
        if not hasattr(request.user, "studentprofile"):
            raise PermissionDenied("Only students can unenroll from courses.")
        course = get_object_or_404(Course, pk=pk)
        student = request.user.studentprofile
        student.enrolled_courses.remove(course)
        try:
            from event.models import CalendarEvent
        except Exception:
            CalendarEvent = None
        if CalendarEvent is not None:
            CalendarEvent.objects.filter(
                user=request.user, related_course=course, event_type="quiz_due"
            ).delete()
        serializer = CourseSerializer(course, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CourseEnrolledStudentsView(APIView):

    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk, format=None):
        if not hasattr(request.user, "instructorprofile"):
            raise PermissionDenied("Only instructors can view enrolled students.")
        course = get_object_or_404(Course, pk=pk)
        if course.author and course.author.user != request.user:
            raise PermissionDenied("You can only view students for your own courses.")
        students = course.students.all().order_by("user__username")
        serializer = EnrolledStudentSerializer(students, many=True)
        return Response(serializer.data)
