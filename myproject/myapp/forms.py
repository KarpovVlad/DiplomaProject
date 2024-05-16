from django import forms
from .models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['average_grade', 'current_course', 'document']
        widgets = {
            'average_grade': forms.NumberInput(attrs={'step': 0.1, 'min': 0}),
            'current_course': forms.NumberInput(attrs={'min': 1}),
        }
