__author__ = 'brunocatao'

from django import forms
from django.utils.translation import ugettext as _

from .models import Poll, Question, Choice, Answer, Group

class PollForm(forms.ModelForm):
    class Meta:
        model = Poll

class QuestionForm(forms.ModelForm):
    help = forms.CharField(label=_('Help'), widget=forms.Textarea, required=False, max_length=1024)
    
    class Meta:
        model = Question

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer

class GroupForm(forms.ModelForm):
    help = forms.CharField(label=_('Help'), widget=forms.Textarea, required=False, max_length=1024)
    
    class Meta:
        model = Group