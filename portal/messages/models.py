# -*- coding: utf-8 -*-
from operator import attrgetter

__author__ = 'brunocatao'

import datetime
import logging

from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User

from django.template import Context
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives

from portal.models import UserInfo

class MessageManager(models.Manager):
    def for_model(self, model):
        """
        QuerySet for all updates for a particular model (either an instance or a class).
        """
        ct = ContentType.objects.get_for_model(model)
        qs = self.get_query_set().filter(content_type=ct)
        if isinstance(model, models.Model):
            qs = qs.filter(object_pk=force_unicode(model._get_pk_val()))
        return qs

    def get_replies(self, user):
        qs = self.get_query_set().filter(author=user, is_reply=False)
        messages = [msg for msg in list(qs.all()) if msg.replies.count() > 0]
        return sorted(messages, key=attrgetter('earlier_date'), reverse=True)

class Message(models.Model):
    subject        = models.CharField(blank=False, max_length=100)
    text           = models.TextField(blank=False)
    date_published = models.DateTimeField(default=datetime.datetime.now)
    author         = models.ForeignKey(User, blank=False)
    is_reply       = models.NullBooleanField(blank=True, null=True)

    content_type   = models.ForeignKey(ContentType, verbose_name=_('content type'), related_name="content_type_set_for_%(class)s")
    object_pk      = models.CharField(_('object ID'), max_length=100)
    content_object = generic.GenericForeignKey(ct_field="content_type", fk_field="object_pk")

    objects        = MessageManager()

    def get_earlier_date(self):
        earlier_date = self.date_published

        if self.replies:
            for reply in self.replies.all():
                if reply.child.date_published > earlier_date:
                    earlier_date = reply.child.date_published

        return earlier_date

    earlier_date = property(get_earlier_date)

def fill_date_published(sender, instance, **kw):
    if not instance.date_published:
        instance.date_published = datetime.datetime.now()
models.signals.pre_save.connect(fill_date_published, sender=Message)

def invalidate_cache(sender, instance, **kw):
    target = instance.content_type.get_object_for_this_type(pk=instance.object_pk)
    target.messages_cache = None
    target.save()
models.signals.pre_save.connect(invalidate_cache, sender=Message)

class ReplyRelationship(models.Model):
    parent = models.ForeignKey(Message, related_name="replies")
    child  = models.ForeignKey(Message, related_name="parent")

#Signal processing
import traceback
from portal.messages.signals import massage_was_posted

def message_notification(sender, **kwargs):
    message = kwargs['message']
    target  = message.content_type.get_object_for_this_type(pk=message.object_pk)

    text = u'%s postou, %s:' % (message.author.get_profile().name, message.subject, )
    text += '\n%s' % message.text

    ctx = {
        'mensagem': text,
        'link': 'http://www.portalsaladeaula.com%s' % target.get_absolute_url(),
    }

    subject      = message.subject
    from_email   = 'Portal Sala de Aula <gerencia@portalsaladeaula.com>'
    text_content = get_template('emails/update.txt').render(Context(ctx))
    html_content = get_template('emails/update.html').render(Context(ctx))

    if isinstance(target, UserInfo) :
        mail_to.append(target.email)
    else:
        if target.get_students():
            for student in target.get_students():
                msg = EmailMultiAlternatives(subject, text_content, from_email, [student.email, ])
                msg.attach_alternative(html_content, "text/html")

                try:
                    msg.send()
                except:
                    logging.error('Não foi possível enviar o email')
                    traceback.print_exc()
        if target.get_teachers():
            for teacher in target.get_teachers():
                msg = EmailMultiAlternatives(subject, text_content, from_email, [teacher.email, ])
                msg.attach_alternative(html_content, "text/html")

                try:
                    msg.send()
                except:
                    logging.error('Não foi possível enviar o email')
                    traceback.print_exc()

massage_was_posted.connect(message_notification)

class Attachment(models.Model):
    file    = models.FileField(_('Attachment'), blank=False, upload_to='uploads/%Y/%m/%d/%H/%M/%S/')
    message = models.ForeignKey(Message, blank=True, null=True)