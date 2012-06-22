__author__ = 'brunocatao'

from django import forms
from django.utils.translation import ugettext as _

class AlbumForm(forms.Form):
    title = forms.CharField(label=_('Title'), required=True, max_length=100)
    slug  = forms.CharField(widget=forms.HiddenInput, required=True, max_length=100)

class PictureForm(forms.Form):
    description = forms.CharField(label=_('Description'), required=False, max_length=100)
    is_cover    = forms.BooleanField(label=_('Album Cover ?'), required=False)