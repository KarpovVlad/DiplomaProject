from django import forms
from .models import Student
from django.contrib.auth.models import User
import random
import string


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['average_grade', 'current_course', 'document']
        widgets = {
            'average_grade': forms.NumberInput(attrs={'step': 0.1, 'min': 0}),
            'current_course': forms.NumberInput(attrs={'min': 1}),
        }


class BulkUserCreationForm(forms.Form):
    number_of_users = forms.IntegerField(min_value=1, max_value=1000)

    def save(self):
        number_of_users = self.cleaned_data['number_of_users']
        users = []

        for _ in range(number_of_users):
            username = self.generate_unique_username()
            email = self.generate_random_email()
            password = self.generate_temporary_password()

            user = User.objects.create_user(username=username, email=email, password=password)
            user.raw_password = password
            users.append(user)

        return users

    def generate_unique_username(self):
        while True:
            username = 'user' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            if not User.objects.filter(username=username).exists():
                return username

    def generate_random_email(self):
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        random_digits = ''.join(random.choices(string.digits, k=3))
        email = f"{random_string}{random_digits}@gmail.com"
        return email

    def generate_temporary_password(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=12))