__author__ = 'brunocatao'

import datetime
from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
import portal.models

class UpdateManager(models.Manager):
    def for_model(self, model):
        """
        QuerySet for all updates for a particular model (either an instance or a class).
        """
        ct = ContentType.objects.get_for_model(model)
        qs = self.get_query_set().filter(content_type=ct)
        if isinstance(model, models.Model):
            qs = qs.filter(object_pk=force_unicode(model._get_pk_val()))
        return qs

class Update(models.Model):
    text           = models.CharField(blank=False, max_length=100)
    link           = models.CharField(blank=False, max_length=512)
    date_published = models.DateTimeField(default=datetime.datetime.now)
    author         = models.ForeignKey(User, blank=False)

    content_type   = models.ForeignKey(ContentType, verbose_name=_('content type'), related_name="content_type_set_for_%(class)s")
    object_pk      = models.CharField(_('object ID'), max_length=100)
    content_object = generic.GenericForeignKey(ct_field="content_type", fk_field="object_pk")

    objects        = UpdateManager()

    @classmethod
    def createUpdate(cls, author, text, link, instance):
        update = Update(author=author, text=text, link=link)
        update.content_type = ContentType.objects.get_for_model(instance)
        update.object_pk    = force_unicode(instance._get_pk_val())
        update.save()
        return update

def fill_date_published(sender, instance, **kw):
    if not instance.date_published:
        instance.date_published = datetime.datetime.now()

models.signals.pre_save.connect(fill_date_published, sender=Update)

def invalidate_cache(sender, instance, **kw):
    target = instance.content_type.get_object_for_this_type(pk=instance.object_pk)

    target.updates_cache = None
    target.save()

    if instance.content_type.model == 'institution':
        if target.get_teachers():
            for t in target.get_teachers():
                t.updates_cache = None
                t.save()
        if target.get_students():
            for s in target.get_students():
                s.updates_cache = None
                s.save()

        for course in target.course_set.all():
            course.updates_cache = None
            course.save()

            if course.get_teachers():
                for t in course.get_teachers():
                    t.updates_cache = None
                    t.save()
            if course.get_students():
                for s in course.get_students():
                    s.updates_cache = None
                    s.save()

            for discipline in course.discipline_set.all():
                discipline.updates_cache = None
                discipline.save()

                if discipline.get_teachers():
                    for t in discipline.get_teachers():
                        t.updates_cache = None
                        t.save()
                if discipline.get_students():
                    for s in discipline.get_students():
                        s.updates_cache = None
                        s.save()
    elif instance.content_type.model  == 'course':
        target.institution.updates_cache = None
        target.institution.save()

        if target.get_teachers():
            for t in target.get_teachers():
                t.updates_cache = None
                t.save()
        if target.get_students():
            for s in target.get_students():
                s.updates_cache = None
                s.save()

        for discipline in target.discipline_set.all():
            discipline.updates_cache = None
            discipline.save()

            if discipline.get_teachers():
                for t in discipline.get_teachers():
                    t.updates_cache = None
                    t.save()
            if discipline.get_students():
                for s in discipline.get_students():
                    s.updates_cache = None
                    s.save()
    elif instance.content_type.model == 'discipline':
        institution = target.course.institution
        institution.updates_cache = None
        institution.save()

        portal.models.InstitutionUpdateCache(text=instance.text, link=instance.link,
                               date_published=instance.date_published, author=instance.author,
                               institution=institution).save()

        target.course.updates_cache = None
        target.course.save()

        if target.get_teachers():
            for t in target.get_teachers():
                t.updates_cache = None
                t.save()
        if target.get_students():
            for s in target.get_students():
                s.updates_cache = None
                s.save()
    else:
        target.updates_cache = None
models.signals.pre_save.connect(invalidate_cache, sender=Update)