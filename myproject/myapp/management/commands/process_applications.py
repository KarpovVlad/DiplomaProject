from django.core.management.base import BaseCommand
from myproject.myapp.models import Student, CourseApplication, Course, CourseEnrollment


def process_applications_task(student_ids=None):
    if student_ids:
        applications = CourseApplication.objects.filter(student__id__in=student_ids)
    else:
        applications = CourseApplication.objects.all()

    catalogs = Course.objects.values_list('catalog', flat=True).distinct()
    print(f"Обробка за каталогами: {list(catalogs)}")

    for catalog in catalogs:
        print(f"Обробка каталогу: {catalog}")
        catalog_courses = Course.objects.filter(catalog=catalog)
        catalog_applications = applications.filter(course__in=catalog_courses)

        while catalog_applications.exists():
            for course in catalog_courses:
                if course.seats > CourseEnrollment.objects.filter(course=course).count():
                    relevant_applications = catalog_applications.filter(course=course)
                    if relevant_applications.exists():
                        scores = []

                        for app in relevant_applications:
                            score = calculate_priority_score(app.student, app)
                            scores.append((score, app.student, app.course))

                        scores.sort(reverse=True, key=lambda x: x[0])

                        if scores:
                            best_score, best_student, best_course = scores[0]
                            CourseEnrollment.objects.create(student=best_student, course=best_course)

                            CourseApplication.objects.filter(student=best_student, course__catalog=catalog).delete()

                            print(
                                f"{best_student.user.username} обрано для курсу {best_course.name} з балом {best_score}")

                            catalog_applications = catalog_applications.exclude(student=best_student)

    print('Розподіл студентів завершено.')


def calculate_priority_score(student, application):
    score = student.average_grade * 0.5 + (5 - application.priority) * 0.1
    if CourseEnrollment.objects.filter(student=student, course=application.course.prerequisite).exists():
        score += 0.1
    return score


class Command(BaseCommand):
    help = 'Розподіл студентів по дисциплінах'

    def add_arguments(self, parser):
        parser.add_argument('--students', nargs='+', type=int, help='ID студентів для обробки')

    def handle(self, *args, **options):
        student_ids = options.get('students')
        process_applications_task(student_ids=student_ids)
