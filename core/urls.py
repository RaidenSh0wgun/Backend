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
    QuizActivityLogView,
)

from user.views import (
    RegisterView,
    CurrentUserView,
    RoleTokenObtainPairView,
    AdminUserListView,
    AdminUserDetailView,
    ReportListCreateView,
    ReportDetailView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    EmailVerificationRequestView,
    EmailVerificationConfirmView,
    PublicUserProfileView,
    NotificationsView,
    NotificationDetailView,
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
    path("api/token/", RoleTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/register/", RegisterView.as_view(), name="register"),
    path("api/users/me/", CurrentUserView.as_view(), name="current_user"),
    path("api/users/<str:username>/", PublicUserProfileView.as_view(), name="public_user_profile"),
    path("api/admin/users/", AdminUserListView.as_view(), name="admin_users"),
    path("api/admin/users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin_user_detail"),
    path("api/reports/", ReportListCreateView.as_view(), name="reports"),
    path("api/reports/<int:report_id>/", ReportDetailView.as_view(), name="report_detail"),
    path("api/auth/email/verify/", EmailVerificationRequestView.as_view(), name="email_verify"),
    path("api/auth/email/verify/confirm/", EmailVerificationConfirmView.as_view(), name="email_verify_confirm"),
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
    path(
        "api/quizzes/<int:quiz_id>/activity/",
        QuizActivityLogView.as_view(),
        name="quiz_activity_log",
    ),
    path("api/courses/", CourseListCreate.as_view(), name="course_list_create"),
    path("api/courses/<int:pk>/", CourseRetrieveUpdateDestroy.as_view(), name="course_retrieve_update_destroy",),
    path("api/courses/my/", CourseList.as_view(), name="course_list",),
    path("api/courses/enrolled/", EnrolledCoursesList.as_view(), name="enrolled_courses",),
    path("api/courses/<int:pk>/detail/", CourseDetail.as_view(), name="course_detail",),
    path("api/courses/<int:pk>/enroll/", EnrollCourseView.as_view(), name="course_enroll",),
    path("api/courses/<int:pk>/students/", CourseEnrolledStudentsView.as_view(), name="course_enrolled_students",),
    path("api/events/", MyCalendarView.as_view(), name="my_calendar"),
    path("api/notifications/", NotificationsView.as_view(), name="notifications"),
    path("api/notifications/<int:notification_id>/", NotificationDetailView.as_view(), name="notification_detail"),
    path("dj-rest-auth/registration/", include("dj_rest_auth.registration.urls")),
    path("dj-rest-auth/", include("dj_rest_auth.urls")),
    path("api/auth/password/reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("api/auth/password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
