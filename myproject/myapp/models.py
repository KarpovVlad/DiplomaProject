from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError


class University(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)

    def __str__(self):
        return self.name


class Faculty(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='faculties')
    name = models.CharField(max_length=255, db_index=True, validators=[RegexValidator(regex='^Faculty of')])

    def __str__(self):
        return f"{self.name} ({self.university.name})"


class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.faculty.name})"


class Professor(models.Model):
    name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='professors')

    def __str__(self):
        return f"{self.name} ({self.department.name})"


class Course(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=255, db_index=True)
    seats = models.IntegerField(default=30, db_index=True)
    professor = models.ForeignKey(Professor, null=True, on_delete=models.SET_NULL, related_name='courses')
    prerequisite = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='advanced_courses')
    semester = models.IntegerField(choices=[
        (3, '3rd Semester'), (4, '4th Semester'),
        (5, '5th Semester'), (6, '6th Semester'),
        (7, '7th Semester'), (8, '8th Semester')
    ], default=3)
    catalog = models.IntegerField(choices=[
        (1, 'Catalog 1'), (2, 'Catalog 2'),
        (3, 'Catalog 3'), (4, 'Catalog 4'),
        (5, 'Catalog 5'), (6, 'Catalog 6')
    ], default=1)

    def clean(self):
        if self.seats < 1:
            raise ValidationError('Number of seats must be at least 1.')

    def __str__(self):
        prereq = f", prerequisite: {self.prerequisite.name}" if self.prerequisite else ""
        return (f"{self.name} - {self.professor.name if self.professor else 'No professor'} ({self.department.name}, "
                f"seats: {self.seats}{prereq}), ({self.semester}")


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    average_grade = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    document = models.FileField(upload_to='documents/', blank=True, null=True)
    current_course = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)], default=1)

    def previously_studied(self, course):
        return CourseApplication.objects.filter(student=self, course=course, passed=True).exists()

    def __str__(self):
        if self.user:
            return f"{self.user.username} ({self.department.name}, Course: {self.current_course})"
        return f"Unknown user ({self.department.name}, Course: {self.current_course})"


class CourseApplication(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='applications')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='applications')
    priority = models.IntegerField(validators=[MinValueValidator(1)])
    semester = models.IntegerField(choices=[(3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8')], default=3)

    class Meta:
        unique_together = ('student', 'course')
        indexes = [
            models.Index(fields=['student', 'course']),
        ]

    def __str__(self):
        return f"{self.student.user.username} applied for {self.course.name} with priority {self.priority}"


class CourseEnrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrolled_students')

    def __str__(self):
        return f"{self.student.user.username} enrolled in {self.course.name}"
