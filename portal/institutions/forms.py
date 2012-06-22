__author__ = 'brunocatao'

from django import forms
from django.utils.translation import ugettext as _

from portal.models import Institution
from portal.constants import STATES_CHOICES

class InstitutionForm(forms.ModelForm):
    name         = forms.CharField(label=_('Name'), required=True, max_length=100)
    acronym      = forms.CharField(label=_('Acronym'), required=False, max_length=100)

    #Address fields, maybe there's a better way to do this
    address      = forms.CharField(label=_('Address'), required=True, max_length=200)
    number       = forms.CharField(label=_('Number'), required=True, max_length=10)
    neighborhood = forms.CharField(label=_('Neighborhood'), required=True, max_length=100)
    city         = forms.CharField(label=_('City'), required=True, max_length=100)
    province     = forms.ChoiceField(label=_('State or Province'), required=True, choices=STATES_CHOICES)

    description  = forms.CharField(label=_('Description'), widget=forms.Textarea)
    homepage     = forms.URLField(label=_('Homepage'), required=False)
    feed_url     = forms.CharField(label=_('News Feed URL'), required=False, max_length=512)
    twitter_id   = forms.CharField(label=_('Twitter ID'), required=False, max_length=100)

    class Meta:
        model = Institution
        exclude = ('picture', 'slug', 'address', 'index', 'messages_cache',
                   'updates_cache', 'teachers_cache', 'students_cache')