from django.http import HttpResponse, Http404
from django.conf import settings
from django.views.generic import TemplateView
from .models import Course, CourseApplication, Student, CourseEnrollment, Department
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
import os


def download_document(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404("File does not exist")


class StudentDashboardView(TemplateView):
    template_name = 'student_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            student = Student.objects.get(user=self.request.user)
            applications = CourseApplication.objects.filter(student=student)
            available_courses = Course.objects.exclude(applications__student=student)
            context.update({
                'student': student,
                'applications': applications,
                'available_courses': available_courses,
            })
        except Student.DoesNotExist:
            messages.error(self.request, "Ваш профіль студента не знайдено. Зверніться до адміністратора.")
            return redirect('profile_creation')
        return context


@method_decorator(login_required, name='dispatch')
class PersonalCabinetView(View):
    template_name = 'personal_cabinet.html'

    def get(self, request):
        student = Student.objects.get(user=request.user)
        return render(request, self.template_name, {'student': student})

    def post(self, request):
        student = Student.objects.get(user=request.user)
        user = request.user

        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        average_grade = request.POST.get('average_grade')
        current_course = request.POST.get('current_course')

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        user.save()

        if average_grade:
            student.average_grade = average_grade
        if current_course:
            student.current_course = current_course
        student.save()

        return redirect('personal_cabinet')


@method_decorator(login_required, name='dispatch')
class CourseSelectionView(View):
    template_name = 'course_selection.html'

    def get(self, request, *args, **kwargs):
        try:
            student = Student.objects.get(user=request.user)
            departments = Department.objects.filter(faculty=student.department.faculty)
            department_ids = departments.values_list('id', flat=True)

            if student.current_course == 1:
                semesters = [3, 4]
            elif student.current_course == 2:
                semesters = [5, 6]
            elif student.current_course == 3:
                semesters = [7, 8]
            else:
                semesters = []

            available_courses = Course.objects.filter(department_id__in=department_ids, semester__in=semesters)

            # Виключаємо курси, на які студент вже зарахований
            enrolled_courses = CourseEnrollment.objects.filter(student=student).values_list('course', flat=True)
            available_courses = available_courses.exclude(id__in=enrolled_courses)

            # Отримуємо заявки студента
            applications = CourseApplication.objects.filter(student=student)
            course_priorities = {app.course_id: app.priority for app in applications}

            # Додаємо атрибут пріоритету до кожного курсу в списку доступних
            for course in available_courses:
                course.user_priority = course_priorities.get(course.id, None)

            context = {
                'student': student,
                'available_courses': available_courses,
                'current_year': student.current_course,
                'semesters': semesters,
            }
            return render(request, self.template_name, context)
        except Student.DoesNotExist:
            messages.error(request, "Ваш профіль студента не знайдено. Зверніться до адміністратора.")
            return redirect('profile_creation')

    def post(self, request, *args, **kwargs):
        try:
            student = Student.objects.get(user=request.user)
            course_id = request.POST.get('course_id')
            priority = request.POST.get('priority')

            if not course_id or not priority:
                messages.error(request, 'Ви повинні вибрати курс та встановити пріоритет.')
                return redirect('course_selection')

            course = Course.objects.get(id=course_id)

            if CourseApplication.objects.filter(student=student, course=course).exists():
                messages.error(request, 'Ви вже подали заявку на цей курс.')
                return redirect('course_selection')

            existing_priorities = CourseApplication.objects.filter(student=student,
                                                                   course__catalog=course.catalog).values_list(
                'priority', flat=True)
            if int(priority) in existing_priorities:
                messages.error(request, f'Пріоритет {priority} вже використаний у каталозі {course.catalog}.')
                return redirect('course_selection')

            CourseApplication.objects.create(student=student, course=course, priority=priority)
            messages.success(request, 'Ваша заявка подана успішно!')
            return redirect('course_selection')
        except Student.DoesNotExist:
            messages.error(request, "Ваш профіль студента не знайдено. Зверніться до адміністратора.")
            return redirect('profile_creation')
        except Course.DoesNotExist:
            messages.error(request, "Курс не знайдено.")
            return redirect('course_selection')


@method_decorator(login_required, name='dispatch')
class SemesterCourseSelectionView(TemplateView):
    template_name = 'semester_course_selection.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        semester = self.kwargs.get('semester')
        try:
            student = Student.objects.get(user=self.request.user)
            available_courses = Course.objects.filter(semester=semester)
            context.update({
                'student': student,
                'available_courses': available_courses,
                'semester': semester,
            })
        except Student.DoesNotExist:
            messages.error(self.request, "Ваш профіль студента не знайдено. Зверніться до адміністратора.")
            return redirect('profile_creation')
        return context

    def post(self, request, *args, **kwargs):
        semester = self.kwargs.get('semester')
        if request.method == "POST":
            priority = request.POST.get('priority')
            student = Student.objects.get(user=request.user)
            course_id = request.POST.get('course_id')
            course = Course.objects.get(id=course_id)
            CourseApplication.objects.create(student=student, course=course, priority=priority)
            messages.success(request, 'Ваша заявка подана успішно!')
        return redirect('course_selection')


def apply_course(request, course_id):
    if request.method == "POST":
        priority = request.POST.get('priority')
        student = Student.objects.get(user=request.user)
        course = Course.objects.get(id=course_id)
        CourseApplication.objects.create(student=student, course=course, priority=priority)
        messages.success(request, 'Ваша заявка подана успішно!')
    return redirect('course_selection')


@method_decorator(login_required, name='dispatch')
class AssignedCoursesView(TemplateView):
    template_name = 'assigned_courses.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = Student.objects.get(user=self.request.user)

        courses_by_semester = {3: [], 4: [], 5: [], 6: [], 7: [], 8: []}

        enrollments = CourseEnrollment.objects.filter(student=student)

        for enrollment in enrollments:
            course_semester = enrollment.course.semester
            courses_by_semester[course_semester].append(enrollment.course)

        context['courses_by_semester'] = courses_by_semester
        context['student'] = student
        return context


class ApplyCoursesView(LoginRequiredMixin, TemplateView):
    template_name = 'apply_courses.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            student = Student.objects.get(user=self.request.user)
            available_courses = Course.objects.exclude(applications__student=student)
            context.update({
                'student': student,
                'available_courses': available_courses,
            })
        except Student.DoesNotExist:
            messages.error(self.request, "Ваш профіль студента не знайдено. Зверніться до адміністратора.")
            return redirect('profile_creation')
        return context

    def post(self, request):
        student = Student.objects.get(user=request.user)
        course_id = request.POST.get('course_id')
        priority = request.POST.get('priority')
        course = Course.objects.get(id=course_id)
        CourseApplication.objects.create(student=student, course=course, priority=priority)
        return redirect('apply_courses')


class AppliedCoursesView(LoginRequiredMixin, TemplateView):
    template_name = 'applied_courses.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            student = Student.objects.get(user=self.request.user)
            applications = CourseApplication.objects.filter(student=student)
            context.update({
                'student': student,
                'applications': applications,
            })
        except Student.DoesNotExist:
            messages.error(self.request, "Ваш профіль студента не знайдено. Зверніться до адміністратора.")
            return redirect('profile_creation')
        return context