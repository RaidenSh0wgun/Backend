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
from django.urls import path
from quiz.views import CourseListCreateView, CourseDetailView, QuizListCreateView, QuizDetailView, QuestionListCreateView, QuestionDetailView
from user.views import StudentProfileView, InstructorProfileView, RegisterView
from result.views import QuizResultView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    
    path('admin/', admin.site.urls),
    
        #course 
    path('api/courses/', CourseListCreateView.as_view(), name='course-list'),
    path('api/courses/<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
     
        #quiz
    path('api/quizzes/', QuizListCreateView.as_view(), name='quiz-list'),
    path('api/quizzes/<int:pk>/', QuizDetailView.as_view(), name='quiz-detail'),
     
        #user profiles
    path('api/student-profile/<int:pk>/', StudentProfileView.as_view(), name='student-profile'),
    path('api/instructor-profile/<int:pk>/', InstructorProfileView.as_view(), name='instructor-profile'),
    
        #quiz results
    path('api/quiz-results/', QuizResultView.as_view(), name='quiz-results'),

        #authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', RegisterView.as_view(), name='register'),

        #questions
    path('api/questions/', QuestionListCreateView.as_view(), name='question-list'),
    path('api/questions/<int:pk>/', QuestionDetailView.as_view(), name='question-detail'),
]
