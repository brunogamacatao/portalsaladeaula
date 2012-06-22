# -*- coding: utf-8 -*-
__author__ = 'brunocatao'

import datetime

from django import forms
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

QUESTION_KIND_CHOICES = (
    ('',  u'Selecione um tipo'),
    ('M', u'Múltipla Escolha'),
    ('L', u'Lickert'),
    ('D', u'Discursiva'),
)

class Poll(models.Model):
    """
    A poll, defined by a title and a set of questions.
    """
    title          = models.CharField(_('Title'), blank=False, max_length=100)
    date_published = models.DateTimeField(default=datetime.datetime.now)

    def __unicode__(self):
        return self.title

class Group(models.Model):
    """
    This class models groups of questions.
    """
    title    = models.CharField(_('Title'), blank=False, max_length=100)
    sequence = models.IntegerField(_('Sequence'), blank=True, default=0)
    poll     = models.ForeignKey(Poll)
    help     = models.CharField(_('Help'), blank=True, max_length=1024)

    def __unicode__(self):
        return '%d. %s' % (self.sequence, self.title, )

    class Meta:
        ordering = ('sequence', )

def fill_group_sequence(sender, instance, **kw):
    """This function will automatically fill the group's sequence value"""
    if instance.sequence == 0:
        instance.sequence = Group.objects.filter(poll=instance.poll).count() + 1

models.signals.pre_save.connect(fill_group_sequence, sender=Group)

class Question(models.Model):
    """
    A poll's question.
    """
    title    = models.CharField(_('Title'), blank=False, max_length=100)
    help     = models.CharField(_('Help'), blank=True, max_length=1024)
    group    = models.ForeignKey(Group)
    kind     = models.CharField(_('Kind'), blank=False, max_length=1, choices=QUESTION_KIND_CHOICES)
    sequence = models.IntegerField(_('Sequence'), blank=True, default=0)

    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ('sequence', )

def fill_question_sequence(sender, instance, **kw):
    """This function will automatically fill the question's sequence value"""
    if instance.sequence == 0:
        instance.sequence = Question.objects.filter(group=instance.group).count() + 1

models.signals.pre_save.connect(fill_question_sequence, sender=Question)


class Choice(models.Model):
    '''
    If a question's kind is "multiple choice" than it should have choices associated.
    '''
    choice   = models.CharField(_('Choice'), blank=False, max_length=100)
    question = models.ForeignKey(Question, null=False)

    class Meta:
        ordering = ('choice', )

class Answer(models.Model):
    """
    An answer associated to a question and to a user.
    """
    answer   = models.CharField(_('Answer'), blank=False, max_length=100)
    question = models.ForeignKey(Question)