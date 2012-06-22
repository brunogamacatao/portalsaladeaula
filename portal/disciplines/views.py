# -*- coding: utf-8 -*-
from portal.files.models import UploadedFile
import logging

__author__ = 'brunocatao'

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

import re
from time import mktime
from datetime import datetime
from feedparser import feedparser
from filetransfers.api import prepare_upload

from mediagenerator.utils import media_url

from portal.models import Institution, Discipline, DisciplineMetadata, Picture, RelDisciplineOwner, RelUserDiscipline, UserDisciplineRole, RelUserCourse, RelUserCourse, UserCourseRole, RelUserInstitution, UserInstitutionRole, UserInstitutionRole
from portal.album.models import Album
from portal.disciplines.forms import DisciplineForm
from portal.messages.forms import MessageForm, AttachmentForm
from portal.constants import MODERATE_REGISTRATION, EVERYONE_CAN_REGISTER, PUBLIC_ACCESS
from portal.courses.views import rebuild_caches as rebuild_course_caches
from portal.institutions.views import rebuild_caches as rebuild_institution_caches

def save(request, inst_slug, course_slug, disc_slug=None):
    institution = get_object_or_404(Institution, slug__exact=inst_slug)
    course      = institution.course_set.get(slug__exact=course_slug)
    disc        = None
    form        = None
    ctx         = dict()

    if request.method == 'GET':
        if disc_slug:
            disc = course.discipline_set.get(slug__exact=disc_slug)
            ctx['picture'] = disc.picture
            form = DisciplineForm(instance=disc)
        else:
            data = {'registration_type': MODERATE_REGISTRATION,
                    'access_type': PUBLIC_ACCESS,}
            form = DisciplineForm(initial=data)
    else:
        if disc_slug:
            disc = course.discipline_set.get(slug__exact=disc_slug)
            form = DisciplineForm(request.POST, instance=disc)
        else:
            form = DisciplineForm(request.POST)

        if form.is_valid():
            disc = form.save(commit=False)

            if request.POST['picture_id']:
                picture = Picture.objects.get(pk=int(request.POST['picture_id']))
                disc.picture = picture

            disc.course = course
            disc.save()

            mdata = DisciplineMetadata()
            mdata.discipline = disc
            mdata.cod_turma  = '123'
            mdata.periodo    = '123'
            mdata.senha      = '123'
            mdata.save()

            if not RelDisciplineOwner.objects.filter(discipline=disc, owner=request.user.get_profile()).exists():
                RelDisciplineOwner(discipline=disc, owner=request.user.get_profile()).save()

            if not RelUserDiscipline.objects.filter(discipline=disc, role=UserDisciplineRole.objects.teacher_role(), user=request.user.get_profile()).exists():
                RelUserDiscipline(discipline=disc, role=UserDisciplineRole.objects.teacher_role(), user=request.user.get_profile()).save()

            if not RelUserCourse.objects.filter(course=disc.course, role=UserCourseRole.objects.teacher_role(), user=request.user.get_profile()).exists():
                RelUserCourse(course=disc.course, role=UserCourseRole.objects.teacher_role(), user=request.user.get_profile()).save()
                rebuild_course_caches(course.id)

            if not RelUserInstitution.objects.filter(institution=disc.course.institution, role=UserInstitutionRole.objects.teacher_role(), user=request.user.get_profile()).exists():
                RelUserInstitution(institution=disc.course.institution, role=UserInstitutionRole.objects.teacher_role(), user=request.user.get_profile()).save()
                rebuild_institution_caches(course.institution.id)

            return HttpResponseRedirect(reverse('portal.disciplines.views.detail', args=[inst_slug, course_slug, disc.slug,]))

    ctx['form'] = form
    return direct_to_template(request, 'disciplines/form.html', ctx)

def detail(request, inst_slug, course_slug, disc_slug):
    institution = get_object_or_404(Institution, slug__exact=inst_slug)
    course      = institution.course_set.get(slug__exact=course_slug)
    disc        = course.discipline_set.get(slug__exact=disc_slug)

    msg_form = MessageForm(disc)
    upload_url, upload_data = prepare_upload(request, reverse('portal.messages.views.attach_file'))

    ctx = {
        'request'    : request,
        'discipline' : disc,
        'photo_count': 0,
        'course'     : course,
        'institution': institution,
        'files'      : UploadedFile.objects.for_model(disc).order_by('date_published').all(),
        'next'       : reverse('portal.disciplines.views.detail', args=[inst_slug, course_slug, disc_slug,]),
        'msg_form'   : msg_form,
        'attach_form': AttachmentForm(),
        'upload_url' : upload_url,
        'upload_data': upload_data,
        'MODERATE_REGISTRATION': disc.registration_type == MODERATE_REGISTRATION,
        'EVERYONE_CAN_REGISTER': disc.registration_type == EVERYONE_CAN_REGISTER,
        'PUBLIC_ACCESS'        : disc.access_type == PUBLIC_ACCESS,
    }

    albums = Album.objects.for_model(disc)
    if albums.exists():
        ctx['albums'] = albums.all()
        qtd = 0
        for album in albums:
            qtd += album.picture_album_set.count()
        ctx['photo_count'] = qtd

    return direct_to_template(request, 'disciplines/detail.html', ctx)

@csrf_protect
def delete(request, inst_slug, course_slug, disc_slug):
    institution = get_object_or_404(Institution, slug__exact=inst_slug)
    course      = institution.course_set.get(slug__exact=course_slug)
    disc        = course.discipline_set.get(slug__exact=disc_slug)
    disc.delete()
    return HttpResponseRedirect(reverse('portal.courses.views.detail', args=[inst_slug, course_slug,]))

@csrf_protect
@login_required
def save_picture(request, id):
    picture = Picture.objects.get(pk=request.POST['picture_id'])
    disc = get_object_or_404(Discipline, pk=id)
    disc.picture = picture
    disc.save()

    return HttpResponse('{"result":{"picture_id":%s,"thumb_id":%s,"thumb_small_id":%s}}' % (str(picture.id), Picture.create_thumbnail(picture, 180, 180).id, Picture.create_thumbnail(picture, 50, 50).id), 'text/html', 200)

def get_news(request, id, first=0, nresults=3):
    disc = get_object_or_404(Discipline, pk=id)

    if not disc.feed_url:
        raise Http404('The is no feed url for this course.')

    feed = feedparser.parse(disc.feed_url)

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
        ctx['next_url'] = reverse('portal.disciplines.views.get_news', args=[id, int(first + nresults), int(nresults),])
    if (first - nresults) >= 0:
        ctx['prev_url'] = reverse('portal.disciplines.views.get_news', args=[id, int(first - nresults), int(nresults),])

    return direct_to_template(request, 'news/list.html', ctx)

def get_discipline(request):
    codigo = request.POST['codigo']
    senha  = request.POST['senha']

    queryset = DisciplineMetadata.objects.filter(cod_turma=codigo,senha=senha)
    if not queryset.exists():
        return HttpResponse('{"status":"erro","mensagem":"Não foi possível localizar uma disciplina com os dados informados"}')

    discipline = queryset[0].discipline

    imagem = "<img style='float:left' src='%s' width='50px' heighth='50px'/>" % media_url('images/books.png')
    if discipline.picture:
        thumb  = Picture.get_thumbnail(discipline.picture, 50, 50)
        imagem = "<img style='float:left' src='/image/%d/' width='%dpx' heighth='%dpx'/>" % (thumb.id, thumb.width, thumb.height) 

    return HttpResponse(u'{"status":"ok","nome":"%s","id":"%s","imagem":"%s"}' % (discipline.name, discipline.id, imagem,))

@csrf_protect
@login_required
def register(request, inst_slug, course_slug, disc_slug):
    institution = get_object_or_404(Institution, slug__exact=inst_slug)
    course      = institution.course_set.get(slug__exact=course_slug)
    disc        = course.discipline_set.get(slug__exact=disc_slug)
    user_info   = request.user.get_profile()

    #Associando a disciplina ao aluno
    queryset = RelUserDiscipline.objects.filter(role=UserDisciplineRole.objects.student_role(), user=user_info, discipline=disc)
    if not queryset.exists():
        RelUserDiscipline(user=user_info, discipline=disc, role=UserDisciplineRole.objects.student_role()).save()

    #Associando o aluno ao curso
    queryset = RelUserCourse.objects.filter(role=UserCourseRole.objects.student_role(), user=user_info, course=disc.course)
    if not queryset.exists():
        RelUserCourse(role=UserCourseRole.objects.student_role(), user=user_info, course=disc.course).save()

    #Associando o aluno à instituição de ensino
    queryset = RelUserInstitution.objects.filter(role=UserInstitutionRole.objects.student_role(), user=user_info, institution=disc.course.institution)
    if not queryset.exists():
        RelUserInstitution(role=UserInstitutionRole.objects.student_role(), user=user_info, institution=disc.course.institution).save()

    return HttpResponseRedirect(reverse('portal.disciplines.views.detail', args=[inst_slug, course_slug, disc_slug,]))