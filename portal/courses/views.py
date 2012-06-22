# -*- coding: utf-8 -*-
import re
import logging
from time import mktime
from datetime import datetime

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.template import Context
from django.template.loader import get_template

from google.appengine.ext import deferred
from feedparser import feedparser
from filetransfers.api import prepare_upload

from portal.models import Course, Institution, Picture, RelCourseOwner, RelUserCourse, UserCourseRole, RelUserInstitution, UserInstitutionRole
from portal.album.models import Album
from portal.courses.forms import CourseForm
from portal.messages.forms import MessageForm, AttachmentForm
from portal.files.models import UploadedFile
from portal.institutions.views import rebuild_caches as rebuild_institution_caches

from settings import PERIODO_ATUAL

def save(request, inst_slug, course_slug=None):
    inst   = get_object_or_404(Institution, slug__exact=inst_slug)
    course = None
    form   = None
    ctx    = dict()

    if request.method == 'GET':
        if course_slug:
            course = inst.course_set.get(slug__exact=course_slug)
            ctx['picture'] = course.picture
            form = CourseForm(instance=course)
        else:
            form = CourseForm()
    else:
        if course_slug:
            course = inst.course_set.get(slug__exact=course_slug)
            form   = CourseForm(request.POST, instance=course)
        else:
            form = CourseForm(request.POST)

        if form.is_valid():
            course = form.save(commit=False)

            if request.POST['picture_id']:
                picture = Picture.objects.get(pk=int(request.POST['picture_id']))
                course.picture = picture

            course.institution = inst
            course.save()

            if not RelCourseOwner.objects.filter(course=course, owner=request.user.get_profile()).exists():
                RelCourseOwner(course=course, owner=request.user.get_profile()).save()

            if not RelUserCourse.objects.filter(course=course, role=UserCourseRole.objects.teacher_role(), user=request.user.get_profile()).exists():
                RelUserCourse(course=course, role=UserCourseRole.objects.teacher_role(), user=request.user.get_profile()).save()
                rebuild_caches(course.id)

            if not RelUserInstitution.objects.filter(institution=course.institution, role=UserInstitutionRole.objects.teacher_role(), user=request.user.get_profile()).exists():
                RelUserInstitution(institution=course.institution, role=UserInstitutionRole.objects.teacher_role(), user=request.user.get_profile()).save()
                rebuild_institution_caches(course.institution.id)

            return HttpResponseRedirect(reverse('portal.courses.views.detail', args=[inst.slug, course.slug,]))

    ctx['form'] = form
    return direct_to_template(request, 'courses/form.html', ctx)

def detail(request, inst_slug, course_slug):
    inst   = get_object_or_404(Institution, slug__exact=inst_slug)
    course = inst.course_set.get(slug__exact=course_slug)

    msg_form = MessageForm(course)
    upload_url, upload_data = prepare_upload(request, reverse('portal.messages.views.attach_file'))

    ctx = {
        'request'    : request,
        'course'     : course,
        'photo_count': 0,
        'institution': inst,
        'files'      : UploadedFile.objects.for_model(course).all(),
        'next'       : reverse('portal.courses.views.detail', args=[inst_slug, course_slug,]),
        'msg_form'   : msg_form,
        'attach_form': AttachmentForm(),
        'upload_url' : upload_url,
        'upload_data': upload_data,
    }

    albums = Album.objects.for_model(course)
    if albums.exists():
        ctx['albums'] = albums.all()
        qtd = 0
        for album in albums:
            qtd += album.picture_album_set.count()
        ctx['photo_count'] = qtd

    return direct_to_template(request, 'courses/detail.html', ctx)

@csrf_protect
def delete(request, inst_slug, course_slug):
    inst   = get_object_or_404(Institution, slug__exact=inst_slug)
    course = inst.course_set.get(slug__exact=course_slug)
    course.delete()
    return HttpResponseRedirect(reverse('portal.institutions.views.detail', args[inst_slug, ]))

@csrf_protect
@login_required
def save_picture(request, id):
    picture = Picture.objects.get(pk=request.POST['picture_id'])
    course = get_object_or_404(Course, pk=id)
    course.picture = picture
    course.save()

    return HttpResponse('{"result":{"picture_id":%s,"thumb_id":%s,"thumb_small_id":%s}}' % (str(picture.id), Picture.create_thumbnail(picture, 180, 180).id, Picture.create_thumbnail(picture, 50, 50).id), 'text/html', 200)

def get_news(request, id, first=0, nresults=3):
    course = get_object_or_404(Course, pk=id)

    if not course.feed_url:
        raise Http404('The is no feed url for this course.')

    feed = feedparser.parse(course.feed_url)

    for news in feed.entries:
        news.updated   = datetime.fromtimestamp(mktime(news.updated_parsed))
        news.main_link = news.links[0].href
        match = re.search(r'<\s*img[^>]+>', news.summary_detail.value)
        if match:
            news.main_image = match.group(0)
            news.summary_detail.value = re.sub(r'<\s*img[^>]+>', '', news.summary_detail.value)

    first    = int(first)
    nresults = int(nresults)

    ctx = {
        'entries': feed.entries[first : nresults + first],
    }

    if (first + nresults) <= len(feed.entries):
        ctx['next_url'] = reverse('portal.courses.views.get_news', args=[id, int(first + nresults), int(nresults),])
    if (first - nresults) >= 0:
        ctx['prev_url'] = reverse('portal.courses.views.get_news', args=[id, int(first - nresults), int(nresults),])

    return direct_to_template(request, 'news/list.html', ctx)

def get_disciplines(request, id, first=0, nresults=9):
    course   = get_object_or_404(Course, pk=id)
    queryset = course.discipline_set.filter(period=PERIODO_ATUAL).all()

    first    = int(first)
    nresults = int(nresults)
    last = first + nresults
    if last > len(queryset):
        last = len(queryset)
    prev = first - nresults
    if prev < 0:
        prev = 0

    disciplines = queryset[first:last]

    import logging
    logging.info('FIRST: %d' % first)

    ctx = {
        'course': course,
        'discipline_set': queryset, 
        'disciplines': disciplines,
        'first': last,
        'prev': prev,
        'nresults': nresults,
        'has_more': last < len(queryset),
        'has_prev': first > 0,
    }

    return direct_to_template(request, 'disciplines/list.html', ctx)

def get_teachers(request, inst_slug, course_slug):
    inst   = get_object_or_404(Institution, slug__exact=inst_slug)
    course = inst.course_set.get(slug__exact=course_slug)
    return HttpResponse(course.teachers_cache)

def get_students(request, inst_slug, course_slug):
    inst   = get_object_or_404(Institution, slug__exact=inst_slug)
    course = inst.course_set.get(slug__exact=course_slug)
    return HttpResponse(course.students_cache)

def rebuild_students_cache(id):
    course = Course.objects.get(pk=id)
    logging.info('Rebuilding teachers cache for %s' % course.slug)

    data = {
        'MEDIA_URL': '/media/',
        'institution': course.institution,
        'students': course.get_students(),
    }

    course.students_cache = get_template('institutions/students_list.html').render(Context(data))
    course.save()
    logging.info('[DONE] - Rebuilding teachers cache for %s' % course.slug)

def rebuild_teacher_cache(id):
    course = Course.objects.get(pk=id)
    logging.info('Rebuilding students cache for %s' % course.slug)

    data = {
        'MEDIA_URL': '/media/',
        'teachers': course.get_teachers(),
    }

    course.teachers_cache = get_template('institutions/teachers_list.html').render(Context(data))
    course.save()
    logging.info('[DONE] - Rebuilding students cache for %s' % course.slug)

def rebuild_caches(id):
    deferred.defer(rebuild_teacher_cache, id)
    deferred.defer(rebuild_students_cache, id)

def rebuild_caches_view(request, inst_slug, course_slug):
    inst   = get_object_or_404(Institution, slug__exact=inst_slug)
    course = inst.course_set.get(slug__exact=course_slug)
    rebuild_caches(course.id)
    return HttpResponse('Caches reconstruidas com sucesso !')