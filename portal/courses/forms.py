__author__ = 'brunocatao'

from django import forms
from portal.models import Course

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        exclude = ('picture', 'slug', 'institution', 'index', 'messages_cache',
                   'updates_cache', 'teachers_cache', 'students_cache')