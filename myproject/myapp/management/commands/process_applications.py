from django.core.management.base import BaseCommand
from myproject.myapp.models import Student, CourseApplication, Course, CourseEnrollment


def process_applications_task(faculty_ids=None):
    if faculty_ids:
        applications = CourseApplication.objects.filter(student__department__faculty__id__in=faculty_ids)
    else:
        applications = CourseApplication.objects.all()

    catalogs = Course.objects.values_list('catalog', flat=True).distinct()
    print(f"Обробка за каталогами: {list(catalogs)}")

    for catalog in catalogs:
        print(f"Обробка каталогу: {catalog}")
        catalog_courses = Course.objects.filter(catalog=catalog)
        catalog_applications = applications.filter(course__in=catalog_courses)
        all_scores = []

        for course in catalog_courses:
            relevant_applications = catalog_applications.filter(course=course)
            scores = []

            for app in relevant_applications:
                score = calculate_priority_score(app.student, app)
                scores.append((score, app.student, app.course))

            scores.sort(reverse=True, key=lambda x: x[0])
            selected_students = scores[:course.seats]
            all_scores.extend(selected_students)

        final_selection = select_students_for_catalog(all_scores, catalog_courses)
        display_selected_students(final_selection)


def calculate_priority_score(student, application):
    score = student.average_grade * 0.5 + (5 - application.priority) * 0.1
    if CourseEnrollment.objects.filter(student=student, course=application.course.prerequisite).exists():
        score += 0.1
    return score


def select_students_for_catalog(all_scores, catalog_courses):
    selected_students = {}
    for score, student, course in all_scores:
        if student.id not in selected_students or len(selected_students[student.id]) < 1:
            selected_students.setdefault(student.id, []).append((course, score))
    return selected_students


def display_selected_students(final_selection):
    total_selected = 0
    for student_id, courses in final_selection.items():
        student = Student.objects.get(id=student_id)
        for course, score in courses:
            print(f"{student.user.username} обрано для курсу {course.name} з балом {score}")
            total_selected += 1

    print(f'Оброблено {total_selected} студентів.')
    if total_selected < len(final_selection):
        print('Не вдалося обробити деякі заявки через невистачу місць.')


class Command(BaseCommand):
    help = 'Розподіл студентів по дисциплінах'

    def add_arguments(self, parser):
        # Додавання аргументу для фільтрації за факультетом
        parser.add_argument('--faculty', nargs='+', type=int, help='ID факультетів для обробки')

    def handle(self, *args, **options):
        faculty_ids = options.get('faculty')
        process_applications_task(faculty_ids=faculty_ids)