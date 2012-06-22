__author__ = 'brunocatao'

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from portal.files.models import UploadedFile
from portal.files.forms import UploadedFileForm
from portal.utils import get_class, get_mime_type

from filetransfers.api import prepare_upload, serve_file

@csrf_protect
@login_required
def upload(request, class_name, id):
    form = None
    instance = get_class(class_name).objects.get(pk=id)
    view_url = reverse('portal.files.views.upload', args=[class_name, id, ])

    if request.method == 'POST':
        form = UploadedFileForm(request.POST, request.FILES)
        if form.is_valid():

            file = form.save(commit=False)
            file.content_type = ContentType.objects.get_for_model(instance)
            file.object_pk = force_unicode(instance._get_pk_val())
            file.user = request.user

            file.save()

            instance.notify_upload(request.user, file)
            
            return HttpResponseRedirect(instance.get_absolute_url())
    else:
        form = UploadedFileForm()

    upload_url, upload_data = prepare_upload(request, view_url)

    ctx = {
        'form': form,
        'upload_url': upload_url,
        'upload_data': upload_data,
    }

    return direct_to_template(request, 'files/form.html', ctx)

def download(request, id):
    uploaded_file = get_object_or_404(UploadedFile, pk=id)

    #Modificando o contador de downloads
    uploaded_file.downloads += 1
    uploaded_file.save()

    filename = uploaded_file.file.name
    
    return serve_file(request, uploaded_file.file, save_as=True, content_type=get_mime_type(filename))

def view(request, id, filename):
    return download(request, id)

def delete(request, id, next_url):
    uploaded_file = get_object_or_404(UploadedFile, pk=id)
    uploaded_file.delete()
    return HttpResponseRedirect(next_url)