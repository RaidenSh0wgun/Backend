from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CourseSerializer
from .models import Course


class CourseListCreate(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "instructorprofile"):
            return Course.objects.filter(author__user=user)
        return Course.objects.all()

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
        return Course.objects.all()

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
        return Course.objects.all()


class CourseDetail(generics.RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "instructorprofile"):
            return Course.objects.filter(author__user=user)
        return Course.objects.all()


class EnrollCourseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, format=None):
        if not hasattr(request.user, "studentprofile"):
            raise PermissionDenied("Only students can enroll in courses.")

        course = get_object_or_404(Course, pk=pk)
        student = request.user.studentprofile
        student.enrolled_courses.add(course)

        serializer = CourseSerializer(course, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk, format=None):
        if not hasattr(request.user, "studentprofile"):
            raise PermissionDenied("Only students can unenroll from courses.")

        course = get_object_or_404(Course, pk=pk)
        student = request.user.studentprofile
        student.enrolled_courses.remove(course)

        serializer = CourseSerializer(course, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)