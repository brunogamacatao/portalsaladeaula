__author__ = 'brunocatao'

from django import forms
from portal.models import Discipline
from django.utils.translation import ugettext as _

class DisciplineForm(forms.ModelForm):
    class Meta:
        model = Discipline
        fields = ('name', 'acronym', 'description', 'feed_url', 'twitter_id',
                  'registration_type', 'access_type', )
