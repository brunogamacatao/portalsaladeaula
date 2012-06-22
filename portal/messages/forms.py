__author__ = 'brunocatao'

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

from portal.messages.models import Message, Attachment

class MessageForm(forms.Form):
    content_type  = forms.CharField(widget=forms.HiddenInput)
    object_pk     = forms.CharField(widget=forms.HiddenInput)
    subject       = forms.CharField(label=_("Subject"), required=True, max_length=100, widget=forms.TextInput(attrs={'class':'validate[required] text-input'}))
    text          = forms.CharField(label=_("Message"), required=True, widget=forms.Textarea(attrs={'class':'validate[required] text-input'}))

    def __init__(self, target_object, data=None, initial=None):
        self.target_object = target_object
        if initial is None:
            initial = {}
        initial.update(self.generate_data())
        super(MessageForm, self).__init__(data=data, initial=initial)

    def generate_data(self):
        data_dict =   {
            'content_type'  : str(self.target_object._meta),
            'object_pk'     : str(self.target_object._get_pk_val()),
        }
        
        return data_dict

    def get_message_object(self):
        if not self.is_valid():
            raise ValueError("get_message_object may only be called on valid forms")
        message = Message(**self.get_message_create_data())
        return message

    def get_message_create_data(self):
        return dict(
            content_type = ContentType.objects.get_for_model(self.target_object),
            object_pk    = force_unicode(self.target_object._get_pk_val()),
            subject      = self.cleaned_data["subject"],
            text         = self.cleaned_data["text"],
        )

class AttachmentForm(forms.ModelForm):
    class Meta:
        model  = Attachment
        fields = ['file',]