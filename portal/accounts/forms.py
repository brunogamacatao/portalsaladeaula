__author__ = 'brunocatao'

from django import forms
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User

from portal.models import UserInfo

class RegisterUserForm(forms.Form):
    email            = forms.EmailField(label=_('Email'), required=True, max_length=100)
    password         = forms.CharField(label=_('Password'), widget=forms.PasswordInput, required=True, min_length=5, max_length=100)
    password_confirm = forms.CharField(
            label=_('Password Confirmation'),
            widget=forms.PasswordInput(attrs={'class':'validate[required,equals[id_password]] text-input'}), 
            required=True, min_length=5, max_length=100)

    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(username=email).exists():
            raise forms.ValidationError(_('A user with this email already exists.'))

        return email

    def clean(self):
        cleaned_data = self.cleaned_data

        password  = cleaned_data.get('password')
        p_confirm = cleaned_data.get('password_confirm')

        if password != p_confirm:
            msg = _("The two password fields didn't match.")
            self._errors['password_confirm'] = self.error_class([msg])

        return cleaned_data

class UserInfoForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        exclude = ('user', 'email', 'index', 'show_help_text', 'is_teacher', 'schedule_cache',)