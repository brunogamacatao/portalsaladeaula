# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.utils.translation import ugettext as _
from portal.models import Picture
from portal.album.models import Album, RelPictureAlbum
from portal.album.forms import AlbumForm, PictureForm
from portal.utils import get_class

@login_required
@csrf_protect
def save(request, class_name, slug):
    instance = get_class(class_name).objects.get(slug=slug)
    form = None

    if request.method == 'GET':
        initial = {
            'slug': slug,
        }

        form = AlbumForm(initial)
    else:
        form = AlbumForm(request.POST)
        if form.is_valid():
            data  = form.cleaned_data
            album = Album.create_album(title=data['title'], instance=instance)

            for picture_id in request.POST['picture_id'].split(','):
                album.add_picture(Picture.objects.get(pk=int(picture_id)))

            return HttpResponseRedirect(reverse('portal.album.views.detail', args=[class_name, slug, album.id,]))

    ctx = {
        'instance': instance,
        'form': form,
    }

    return direct_to_template(request, 'album/form.html', ctx)

def detail(request, class_name, slug, album_id):
    instance = get_class(class_name).objects.get(slug=slug)
    album = Album.objects.get(pk=album_id)

    ctx = {
        'instance': instance,
        'album': album,
    }

    return direct_to_template(request, 'album/detail.html', ctx)

@login_required
@csrf_protect
def add_picture(request, class_name, slug, album_id):
    instance = get_class(class_name).objects.get(slug=slug)
    album    = Album.objects.get(pk=album_id)
    form     = None

    if request.method == 'GET':
        form = PictureForm()
    else:
        form = PictureForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if request.FILES.has_key('picture'):
                picture = Picture()
                picture.picture = request.FILES['picture'].read()
                picture.save()

                rpa = RelPictureAlbum(picture=picture, album=album)

                if data.has_key('description'):
                    rpa.description = data['description']
                if data.has_key('is_cover'):
                    rpa.is_cover = True
                    
                rpa.save()

                return HttpResponseRedirect(reverse('portal.album.views.detail', args=[class_name, slug, album_id, ]))
            else:
                form.errors['picture'] = form.error_class([_('The picture is required.'),])

    ctx = {
        'instance': instance,
        'album': album,
        'form': form,
    }

    return direct_to_template(request, 'album/add_picture.html', ctx)