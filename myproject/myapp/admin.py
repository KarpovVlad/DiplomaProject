from datetime import datetime
from django.urls import reverse
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import University, Faculty, Department, Professor, Course, Student, CourseApplication, CourseEnrollment
from docx import Document
from django.utils.html import format_html
from django.core.management import call_command
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .forms import BulkUserCreationForm
from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponse
from django.utils.text import slugify
import io
import csv


def generate_idp_for_student(student_id):
    student = Student.objects.get(id=student_id)
    enrollments = CourseEnrollment.objects.filter(student=student)

    document = Document()
    document.add_heading('Індивідуальний навчальний план', level=1)

    document.add_paragraph(f"Студент: {student.user.first_name} {student.user.last_name}")
    document.add_paragraph(f"Кафедра: {student.department.name}")
    document.add_paragraph(f"Середній бал: {student.average_grade}")

    document.add_heading('Обрані дисципліни:', level=2)
    table = document.add_table(rows=1, cols=3)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Назва дисципліни'
    hdr_cells[1].text = 'Викладач'

    for enrollment in enrollments:
        row_cells = table.add_row().cells
        row_cells[0].text = enrollment.course.name
        row_cells[1].text = str(enrollment.course.professor)

    document.add_page_break()

    file_path = f'documents/{student.user.username}_IDP.docx'
    document.save(file_path)

    student.document = file_path
    student.save()


def generate_idp_for_group(department_id):
    students = Student.objects.filter(department_id=department_id)

    for student in students:
        generate_idp_for_student(student.id)


class UniversityAdmin(ImportExportModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class FacultyAdmin(ImportExportModelAdmin):
    list_display = ('name', 'university')
    search_fields = ('name', 'university__name')
    list_filter = ('university__name',)


class DepartmentAdmin(ImportExportModelAdmin):
    list_display = ('name', 'faculty')
    search_fields = ('name', 'faculty__name')
    list_filter = ('faculty__name', 'faculty__university__name')


class ProfessorAdmin(ImportExportModelAdmin):
    list_display = ('name', 'department')
    search_fields = ('name',)
    list_filter = ('department__name',)


class CourseAdmin(ImportExportModelAdmin):
    list_display = ('name', 'department', 'professor', 'seats', 'prerequisite')
    search_fields = ('name', 'professor__name', 'department__name')
    list_filter = ('department__name', 'professor__name', 'department__faculty__university__name')


class StudentResource(resources.ModelResource):
    class Meta:
        model = Student
        fields = ('user__username', 'department__name', 'average_grade', 'document')


class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ('user', 'department', 'average_grade', 'current_course', 'download_link')
    search_fields = ('user__username', 'department__name')
    list_filter = ('department__name', 'department__faculty__name')
    actions = ['generate_idp_single', 'generate_idp_group', 'process_applications']

    def download_link(self, obj):
        if obj.document:
            url = reverse('download_document', args=[obj.document.name])
            return format_html("<a href='{}' download='{}'>Завантажити</a>", obj.document.url.rstrip('/'),
                               obj.document.name)
        return "Файл відсутній"

    download_link.short_description = 'Документ'

    def generate_idp_single(self, request, queryset):
        for student in queryset:
            generate_idp_for_student(student.id)

    generate_idp_single.short_description = "Генерувати ІНП для вибраних студентів"

    def generate_idp_group(self, request, queryset):
        department_ids = set(queryset.values_list('department__id', flat=True))
        for department_id in department_ids:
            generate_idp_for_group(department_id)

    generate_idp_group.short_description = "Генерувати ІНП для груп студентів за кафедрами"

    def process_applications(self, request, queryset):
        output = io.StringIO()
        call_command('process_applications', stdout=output)
        self.message_user(request, output.getvalue())

    process_applications.short_description = "Запустити алгоритм багатокритеріального вибору"


class CourseApplicationAdmin(ImportExportModelAdmin):
    list_display = ('student', 'course', 'priority')
    search_fields = ('student__user__username', 'course__name')
    list_filter = ('course__name', 'student__department__name')


class CourseEnrollmentAdmin(ImportExportModelAdmin):
    list_display = ('student', 'course')
    search_fields = ('student__user__username', 'course__name')
    list_filter = ('course__name', 'student__department__name')


class CustomUserAdmin(UserAdmin):
    change_list_template = "admin/auth/user/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk_add/', self.admin_site.admin_view(self.bulk_add_users), name='bulk_add_users'),
            path('export_users/', self.admin_site.admin_view(self.export_users), name='export_users'),
        ]
        return custom_urls + urls

    def bulk_add_users(self, request):
        if request.method == 'POST':
            form = BulkUserCreationForm(request.POST)
            if form.is_valid():
                users = form.save()
                self.message_user(request, f"Створено {len(users)} користувачів.")
                return redirect('..')
        else:
            form = BulkUserCreationForm()

        context = {
            'form': form,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        return render(request, 'admin/bulk_add_users.html', context)

    def export_users(self, request):
        users = User.objects.all()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="users_{slugify(str(datetime.now()))}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'Password'])

        for user in users:
            writer.writerow([user.username, user.email, user.password])

        return response


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(University, UniversityAdmin)
admin.site.register(Faculty, FacultyAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(CourseEnrollment, CourseEnrollmentAdmin)
admin.site.register(CourseApplication, CourseApplicationAdmin)
admin.site.register(Professor, ProfessorAdmin)
