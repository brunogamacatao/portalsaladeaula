__author__ = 'brunocatao'

import random
import datetime
from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _

from portal.models import Picture, Institution

class AlbumManager(models.Manager):
    def for_model(self, model):
        """
        QuerySet for all albums for a particular model (either an instance or a class).
        """
        ct = ContentType.objects.get_for_model(model)
        qs = self.get_query_set().filter(content_type=ct)
        if isinstance(model, models.Model):
            qs = qs.filter(object_pk=force_unicode(model._get_pk_val()))
        return qs

'''
Albums are a group of pictures. They have a title, a date when it was published
and they can be associated with any kind of entities.
'''
class Album(models.Model):
    title = models.CharField(_('Name'), blank=False, max_length=100)
    date_published = models.DateTimeField(default=datetime.datetime.now)
    date_modified  = models.DateTimeField(blank=True, null=True)

    content_type   = models.ForeignKey(ContentType, verbose_name=_('content type'), related_name="content_type_set_for_%(class)s")
    object_pk      = models.CharField(_('object ID'), max_length=100)
    content_object = generic.GenericForeignKey(ct_field="content_type", fk_field="object_pk")

    objects = AlbumManager()

    def add_picture(self, picture):
        rpa = RelPictureAlbum(album=self, picture=picture)
        rpa.save()

    def _cover(self):
        if self.picture_album_set.count() == 0:
            return None
        if self.picture_album_set.filter(is_cover=True).exists():
            rpa = self.picture_album_set.get(is_cover=True)
            return rpa.picture
        pics = list(self.picture_album_set.all())
        random.shuffle(pics)
        return pics[0].picture
    cover = property(_cover)

    @classmethod
    def create_album(cls, title, instance):
        album = Album(title=title)
        album.content_type = ContentType.objects.get_for_model(instance)
        album.object_pk    = force_unicode(instance._get_pk_val())
        album.save()
        return album

def fill_date_modified(sender, instance, **kw):
    instance.date_modified = datetime.datetime.now()

models.signals.pre_save.connect(fill_date_modified, sender=Album)

class RelPictureAlbum(models.Model):
    picture        = models.ForeignKey(Picture, blank=False, related_name='picture_album_set')
    album          = models.ForeignKey(Album, blank=False, related_name='picture_album_set')
    description    = models.CharField(_('Description'), blank=True, null=True, max_length=100)
    is_cover       = models.BooleanField(default=False)
    date_published = models.DateTimeField(default=datetime.datetime.now)
    date_modified  = models.DateTimeField(blank=True, null=True)

def just_one_cover(sender, instance, **kw):
    if instance.is_cover:
        #Ensure the no other picture is also tagged as the album's cover
        for pic in instance.album.picture_album_set.filter(is_cover=True):
            pic.is_cover=False
            pic.save()

models.signals.pre_save.connect(just_one_cover, sender=RelPictureAlbum)
models.signals.pre_save.connect(fill_date_modified, sender=RelPictureAlbum)