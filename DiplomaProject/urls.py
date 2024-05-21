from django.contrib import admin
from myproject.myapp.views import download_document
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth import views as auth_views
from myproject.myapp.views import StudentDashboardView
from myproject.myapp.views import apply_course
from myproject.myapp.views import PersonalCabinetView
from myproject.myapp.views import CourseSelectionView
from myproject.myapp.views import AssignedCoursesView
from myproject.myapp.views import ApplyCoursesView
from myproject.myapp.views import AppliedCoursesView
from myproject.myapp.views import SemesterCourseSelectionView

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),
    path('password_change/',
         auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'),
         name='password_change'),
    path('password_change_done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'),
         name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),
    path('admin/', admin.site.urls),
    path('media/<path:filename>/', download_document, name='download_document'),
    path('personal-cabinet/', PersonalCabinetView.as_view(), name='personal_cabinet'),
    path('assigned_courses/', AssignedCoursesView.as_view(), name='assigned_courses'),
    path('dashboard/', StudentDashboardView.as_view(), name='student_dashboard'),
    path('apply_courses/', ApplyCoursesView.as_view(), name='apply_courses'),
    path('applied_courses/', AppliedCoursesView.as_view(), name='applied_courses'),
    path('course-selection/', CourseSelectionView.as_view(), name='course_selection'),
    path('course-selection/semester/<int:semester>/', SemesterCourseSelectionView.as_view(),
         name='semester_course_selection'),
    path('apply_course/<int:course_id>/', apply_course, name='apply_course'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)