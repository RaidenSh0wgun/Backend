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
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView

from quiz.views import (
    ListCreateQuiz,
    QuizQuestionDetail,
    RetrieveUpdateDestroyQuiz,
    QuizQuestions,
    SubmitQuiz,
    QuizAttemptsView,
    QuizAttemptDetail,
    PendingQuizzesView,
    QuizViewDetail,
    AttemptedQuizzesView,
    CalendarQuizzesView,
    QuizTimerView,
)
from user.views import (
    RegisterView,
    CurrentUserView,
    RoleTokenObtainPairView,
    AdminUserListView,
    AdminUserDetailView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    EmailVerificationRequestView,
    EmailVerificationConfirmView,
    PublicUserProfileView,
)
from event.views import MyCalendarView
from course.views import (
    CourseListCreate,
    CourseRetrieveUpdateDestroy,
    CourseList,
    CourseDetail,
    EnrollCourseView,
    CourseEnrolledStudentsView,
    EnrolledCoursesList,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    # JWT Auth urls
    path("api/token/", RoleTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # User / auth-related custom endpoints
    path("api/register/", RegisterView.as_view(), name="register"),
    path("api/users/me/", CurrentUserView.as_view(), name="current_user"),
    path("api/users/<str:username>/", PublicUserProfileView.as_view(), name="public_user_profile"),
    path("api/admin/users/", AdminUserListView.as_view(), name="admin_users"),
    path("api/admin/users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin_user_detail"),
    path("api/auth/email/verify/", EmailVerificationRequestView.as_view(), name="email_verify"),
    path("api/auth/email/verify/confirm/", EmailVerificationConfirmView.as_view(), name="email_verify_confirm"),

    # Quiz app urls
    path("api/quizzes/", ListCreateQuiz.as_view(), name="quiz_list"),
    path("api/quizzes/pending/", PendingQuizzesView.as_view(), name="pending_quizzes"),
    path(
        "api/quizzes/attempted/",
        AttemptedQuizzesView.as_view(),
        name="attempted_quizzes",
    ),
    path("api/quizzes/calendar/", CalendarQuizzesView.as_view(), name="calendar_quizzes"),
    path("api/quizzes/<int:pk>/", RetrieveUpdateDestroyQuiz.as_view(), name="retrieve_update_destroy_quiz",),
    path("api/quizzes/<int:quiz_id>/attempts/", QuizAttemptsView.as_view(), name="quiz_attempts",),
    path("api/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/", QuizAttemptDetail.as_view(), name="quiz_attempt_detail",),
    path("api/quizzes/<int:quiz_id>/questions/", QuizQuestions.as_view(), name="questions",),
    path("api/questions/<int:pk>/", QuizQuestionDetail.as_view(), name="quiz_question_detail",),
    path("api/quizzes/<int:quiz_id>/submit/", SubmitQuiz.as_view(), name="quiz_submit",),
    path(
        "api/quizzes/<int:quiz_id>/view/",
        QuizViewDetail.as_view(),
        name="quiz_view_detail",
    ),
    path(
        "api/quizzes/<int:quiz_id>/timer/",
        QuizTimerView.as_view(),
        name="quiz_timer",
    ),

    # Course
    path("api/courses/", CourseListCreate.as_view(), name="course_list_create"),
    path("api/courses/<int:pk>/", CourseRetrieveUpdateDestroy.as_view(), name="course_retrieve_update_destroy",),
    path("api/courses/my/", CourseList.as_view(), name="course_list",),
    path("api/courses/enrolled/", EnrolledCoursesList.as_view(), name="enrolled_courses",),
    path("api/courses/<int:pk>/detail/", CourseDetail.as_view(), name="course_detail",),
    path("api/courses/<int:pk>/enroll/", EnrollCourseView.as_view(), name="course_enroll",),
    path("api/courses/<int:pk>/students/", CourseEnrolledStudentsView.as_view(), name="course_enrolled_students",),

    # Calendar (events)
    path("api/events/", MyCalendarView.as_view(), name="my_calendar"),

    # dj-rest-auth
    path("dj-rest-auth/registration/", include("dj_rest_auth.registration.urls")),
    path("dj-rest-auth/", include("dj_rest_auth.urls")),

    # Password Reset
    path("api/auth/password/reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("api/auth/password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
