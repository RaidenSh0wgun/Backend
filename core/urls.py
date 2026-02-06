"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from quiz.views import ListCreateQuiz, QuizQuestionDetail, RetrieveUpdateDestroyQuiz, QuizQuestions



urlpatterns = [
    path('admin/', admin.site.urls),
   # JWT Auth urls
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Quiz app urls
    path('api/quizzes/', ListCreateQuiz.as_view(), name='quiz_list'),
    path('api/quizzes/<int:pk>/', RetrieveUpdateDestroyQuiz.as_view(), name='retrieve_update_destroy_quiz'),
    path('api/quizzes/<int:quiz_id>/questions/', QuizQuestions.as_view(), name='questions'),
    path('api/questions/<int:pk>/', QuizQuestionDetail.as_view(), name='quiz_question_detail'),

    # Registration and authentication urls
    path("/api/register/", include("dj_rest_auth.registration.urls")),
    path("auth/", include("dj_rest_auth.urls")),
]