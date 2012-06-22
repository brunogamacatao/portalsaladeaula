__author__ = 'brunocatao'

import datetime
from django.contrib.auth.models import User
from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _

class UploadedFileManager(models.Manager):
    def for_model(self, model):
        """
        QuerySet for all uploaded files for a particular model (either an instance or a class).
        """
        ct = ContentType.objects.get_for_model(model)
        qs = self.get_query_set().filter(content_type=ct)
        if isinstance(model, models.Model):
            qs = qs.filter(object_pk=force_unicode(model._get_pk_val()))
        return qs

class UploadedFile(models.Model):
    file           = models.FileField(_('File'), blank=False, upload_to='uploads/%Y/%m/%d/%H/%M/%S/')
    description    = models.CharField(_('Description'), blank=False, max_length=100)
    date_published = models.DateTimeField(default=datetime.datetime.now)
    date_modified  = models.DateTimeField(blank=True, null=True)
    downloads      = models.IntegerField(default=0)
    user           = models.ForeignKey(User)

    content_type   = models.ForeignKey(ContentType, verbose_name=_('content type'), related_name="content_type_set_for_%(class)s")
    object_pk      = models.CharField(_('object ID'), max_length=100)
    content_object = generic.GenericForeignKey(ct_field="content_type", fk_field="object_pk")

    objects        = UploadedFileManager()

def fill_date_modified(sender, instance, **kw):
    instance.date_modified = datetime.datetime.now()

models.signals.pre_save.connect(fill_date_modified, sender=UploadedFile)