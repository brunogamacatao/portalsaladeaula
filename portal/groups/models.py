# -*- coding: utf-8 -*-
__author__ = 'brunocatao'

from django.db import models
from django.utils.translation import ugettext as _

from portal.models import Indexable, Picture, UserInfo
from portal.fields import AutoSlugField

'''
Groups are a place where users who share similar interests can share messages,
files, pictures and so on.
There are two roles for the relationship between users and groups:
1. Owners - They administrate the group. Owners can invite other users to
            participate of the group;
2. Users  - They can post messages, files and pictures. They can join a group
            in two ways: i) accessing the group and applying for membership, or
            ii) receiving an email from an invitement from a group's owner. 
'''
class Group(Indexable):
    name        = models.CharField(_('Name'), blank=False, max_length=100)
    slug        = AutoSlugField(prepopulate_from=('acronym',), parent_name='course', unique=True, blank=True, max_length=100)
    acronym     = models.CharField(_('Acronym'), blank=True, null=True, max_length=100)
    picture     = models.ForeignKey(Picture, blank=True, null=True)
    description = models.TextField(_('Description'))
    feed_url    = models.CharField(_('News Feed URL'), blank=True, null=True, max_length=512)
    twitter_id  = models.CharField(_('Twitter ID'), blank=True, null=True, max_length=100)

class ManagerUserGroupRole(models.Manager):
    def owner_role(self):
        queryset = self.filter(slug='owner')
        if queryset.exists():
            return queryset.all()[0]
        role = UserGroupRole(name='Owner', slug='owner')
        role.save()
        return role

    def user_role(self):
        queryset = self.filter(slug='user')
        if queryset.exists():
            return queryset.all()[0]
        role = UserGroupRole(name='User', slug='user')
        role.save()
        return role

class UserGroupRole(models.Model):
    name = models.CharField(_('Role Name'), blank=False, max_length=100)
    slug = AutoSlugField(prepopulate_from=('name',), unique=True, blank=True, max_length=100)

    objects = ManagerUserGroupRole()

    class Meta:
        verbose_name        = _('Role for Group Relationship')
        verbose_name_plural = _('Roles for Group Relationship')

    def __unicode__(self):
        return self.name

class RelUserGroup(models.Model):
    user  = models.ForeignKey(UserInfo, blank=False)
    group = models.ForeignKey(Group, blank=False)
    role  = models.ForeignKey(UserGroupRole, blank=False)
