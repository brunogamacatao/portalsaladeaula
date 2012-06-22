__author__ = 'brunocatao'

from django import forms
from portal.files.models import UploadedFile

class UploadedFileForm(forms.ModelForm):
    class Meta:
        model  = UploadedFile
        fields = ['file', 'description', ]