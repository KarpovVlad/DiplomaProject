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
    num_users = forms.IntegerField(label='Кількість користувачів', min_value=1, max_value=1000)

    def save(self):
        users = []
        for _ in range(self.cleaned_data['num_users']):
            username = self.generate_random_username()
            password = self.generate_random_password()
            user = User(username=username)
            user.set_password(password)
            user.save()
            users.append(user)
        return users

    def generate_random_username(self, length=8):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))

    def generate_random_password(self, length=12):
        letters = string.ascii_letters
        digits = string.digits
        special_chars = string.punctuation
        all_chars = letters + digits + special_chars
        password = ''.join(random.choice(all_chars) for i in range(length))
        return password
