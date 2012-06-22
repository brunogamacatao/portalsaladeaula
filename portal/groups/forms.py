__author__ = 'brunocatao'

from django import forms
from django.utils.translation import ugettext as _

from .models import Group

class GroupForm(forms.ModelForm):
    name         = forms.CharField(label=_('Name'),          required=True, max_length=100)
    acronym      = forms.CharField(label=_('Acronym'),       required=False, max_length=100)
    description  = forms.CharField(label=_('Description'),   widget=forms.Textarea)
    feed_url     = forms.CharField(label=_('News Feed URL'), required=False, max_length=512)
    twitter_id   = forms.CharField(label=_('Twitter ID'),    required=False, max_length=100)

    class Meta:
        model = Group
        fields = ('name', 'acronym', 'description', 'feed_url', 'twitter_id', )