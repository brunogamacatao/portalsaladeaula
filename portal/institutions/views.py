# -*- coding: utf-8 -*-
import re
import logging
from time import mktime
from datetime import datetime

from django.http import HttpResponse, Http404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.template import Context
from django.template.loader import get_template

from google.appengine.ext import deferred
from feedparser import feedparser
from filetransfers.api import prepare_upload

from portal.album.models import Album
from portal.files.models import UploadedFile
from portal.messages.forms import MessageForm, AttachmentForm
from portal.institutions.forms import InstitutionForm
from portal.models import Address, Institution, Picture, RelInstitutionOwner

def index(request):
    return HttpResponse('Funciona !')

@csrf_protect
@login_required
def save(request, slug=None):
    form = None
    ctx  = dict()

    if request.method == 'GET':
        if slug:
            institution = get_object_or_404(Institution, slug__exact=slug)

            initial = dict()
            if (institution.address):
                initial = {
                    'address':      institution.address.address,
                    'number':       institution.address.number,
                    'neighborhood': institution.address.neighborhood,
                    'city':         institution.address.city,
                    'province':     institution.address.province,
                }

            ctx['picture'] = institution.picture
            form = InstitutionForm(instance=institution, initial=initial)
        else:
            form = InstitutionForm()
    else:
        if slug:
            institution = get_object_or_404(Institution, slug__exact=slug)
            form = InstitutionForm(request.POST, instance=institution)
        else:
            form = InstitutionForm(request.POST)

        if form.is_valid():
            inst = form.save(commit=False)

            if request.POST['picture_id']:
                picture = Picture.objects.get(pk=int(request.POST['picture_id']))
                inst.picture = picture

            data = form.cleaned_data
            address = Address(address=data['address'], number=data['number'], neighborhood=data['neighborhood'], city=data['city'], province=data['province'])
            address.save()
            inst.address = address
            
            inst.save()

            if not RelInstitutionOwner.objects.filter(institution=inst, owner=request.user.get_profile()).exists():
                RelInstitutionOwner(institution=inst, owner=request.user.get_profile()).save()

            return HttpResponseRedirect(reverse('portal.institutions.views.detail', args=[inst.slug,]))

    ctx['form'] = form

    return direct_to_template(request, 'institutions/form.html', ctx)

@csrf_protect
def delete(request, slug):
    inst = get_object_or_404(Institution, slug__exact=slug)
    inst.delete()
    return HttpResponseRedirect(reverse('portal.views.index'))

def detail(request, slug):
    inst = get_object_or_404(Institution, slug__exact=slug)

    msg_form = MessageForm(inst)
    upload_url, upload_data = prepare_upload(request, reverse('portal.messages.views.attach_file'))

    ctx = {
        'request'    : request,
        'institution': inst,
        'photo_count': 0,
        'files'      : UploadedFile.objects.for_model(inst).all(),
        'next'       : reverse('portal.institutions.views.detail', args=[slug,]),
        'msg_form'   : msg_form,
        'attach_form': AttachmentForm(),
        'upload_url' : upload_url,
        'upload_data': upload_data,
    }

    albums = Album.objects.for_model(inst)
    if albums.exists():
        ctx['albums'] = albums.all()
        qtd = 0
        for album in albums:
            qtd += album.picture_album_set.count()
        ctx['photo_count'] = qtd

    return direct_to_template(request, 'institutions/detail.html', ctx)

@csrf_protect
@login_required
def save_picture(request, slug):
    picture = Picture.objects.get(pk=request.POST['picture_id'])
    inst = get_object_or_404(Institution, slug__exact=slug)
    inst.picture = picture
    inst.save()

    return HttpResponse('{"result":{"picture_id":%s,"thumb_id":%s,"thumb_small_id":%s}}' % (str(picture.id), Picture.create_thumbnail(picture, 180, 180).id, Picture.create_thumbnail(picture, 50, 50).id), 'text/html', 200)

def get_news(request, slug, first=0, nresults=3):
    inst = get_object_or_404(Institution, slug__exact=slug)

    if not inst.feed_url:
        raise Http404('The is no feed url for this institution.')

    feed = feedparser.parse(inst.feed_url)

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
        ctx['next_url'] = reverse('portal.institutions.views.get_news', args=[slug, int(first + nresults), int(nresults),])
    if (first - nresults) >= 0:
        ctx['prev_url'] = reverse('portal.institutions.views.get_news', args=[slug, int(first - nresults), int(nresults),])

    return direct_to_template(request, 'news/list.html', ctx)

def get_updates(request, slug):
    inst = get_object_or_404(Institution, slug__exact=slug)
    ctx = {"update_list": inst.institutionupdatecache_set.order_by('-date_published')[:5],}
    return direct_to_template(request, 'updates/list.html', ctx)

def get_teachers(request, slug):
    inst = get_object_or_404(Institution, slug__exact=slug)
    return HttpResponse(inst.teachers_cache)

def get_students(request, slug):
    inst = get_object_or_404(Institution, slug__exact=slug)
    return HttpResponse(inst.students_cache)

def rebuild_students_cache(id):
    inst = Institution.objects.get(pk=id)
    logging.info('Rebuilding teachers cache for %s' % inst.slug)

    data = {
        'MEDIA_URL': '/media/',
        'institution': inst,
        'students': inst.get_students(),
    }

    inst.students_cache = get_template('institutions/students_list.html').render(Context(data))
    inst.save()
    logging.info('[DONE] - Rebuilding teachers cache for %s' % inst.slug)

def rebuild_teacher_cache(id):
    inst = Institution.objects.get(pk=id)
    logging.info('Rebuilding students cache for %s' % inst.slug)

    data = {
        'MEDIA_URL': '/media/', 
        'teachers': inst.get_teachers(),
    }

    inst.teachers_cache = get_template('institutions/teachers_list.html').render(Context(data))
    inst.save()
    logging.info('[DONE] - Rebuilding students cache for %s' % inst.slug)

def rebuild_caches(id):
    deferred.defer(rebuild_teacher_cache, id)
    deferred.defer(rebuild_students_cache, id)

def rebuild_caches_view(request, slug):
    inst = get_object_or_404(Institution, slug__exact=slug)
    rebuild_caches(inst.id)
    return HttpResponse('Caches reconstruidas com sucesso !')