from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import Group
from .models import *
from .serializers import StudentProfileSerializer, InstructorProfileSerializer, RegisterSerializer

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
        queryset = super().get_queryset().filter(is_active=True).order_by('username')

class RegisterView(generics.ListAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

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