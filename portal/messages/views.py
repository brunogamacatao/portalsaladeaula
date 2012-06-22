from portal.models import UserInfo

__author__ = 'brunocatao'

import logging, traceback
from django.db import models
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode

from portal.messages.models import Message, Attachment, ReplyRelationship
from portal.messages.forms import MessageForm, AttachmentForm
from portal.messages import signals
from portal.templatetags.text import sizify
from portal.utils import get_mime_type
from filetransfers.api import prepare_upload, serve_file

@login_required
@csrf_protect
@require_POST
def post_message(request):
    message, target = create_message(request)
    return HttpResponseRedirect(target.get_absolute_url())

@login_required
@csrf_protect
@require_POST
def post_reply(request):
    message = Message.objects.get(pk=request.POST['message_id'])
    reply, target = create_message(request, is_reply=True)
    ReplyRelationship(parent=message, child=reply).save()
    return HttpResponseRedirect(target.get_absolute_url())

def create_message(request, is_reply=False):
    data      = request.POST
    ctype     = data.get("content_type")
    object_pk = data.get("object_pk")

    model  = models.get_model(*ctype.split(".", 1))
    target = model._default_manager.get(pk=object_pk)

    form = MessageForm(target, data=data)
    message = form.get_message_object()
    message.author   = request.user
    message.is_reply = is_reply

    signals.message_will_be_posted.send(sender=message.__class__, message=message, request=message)
    message.save()

    #Attachment handling
    if data.has_key('attachment_id') and data['attachment_id']:
        try:
            attachment = Attachment.objects.get(pk=data['attachment_id'])
            attachment.message = message
            attachment.save()
        except:
            traceback.print_exc()

    signals.massage_was_posted.send(sender=message.__class__, message=message, request=message)

    return (message, target, )

@csrf_protect
@login_required
def attach_file(request):
    form = AttachmentForm(request.POST, request.FILES)
    attachment = form.save()
    return HttpResponseRedirect(reverse('portal.messages.views.result_attach_file', args=[attachment.id,]))

def result_attach_file(request, id):
    attachment = Attachment.objects.get(pk=id)
    filename   = attachment.file.name.split('/')[-1]
    size       = sizify(attachment.file.size)
    return HttpResponse('{"result":{"id":%s,"name":"%s","size":"%s"}}' % (id, filename, size))

def download_attachment(request, id):
    attachment = Attachment.objects.get(pk=id)
    return serve_file(request, attachment.file, save_as=True, content_type=get_mime_type(attachment.file.name))

def get_message(request, id):
    message = get_object_or_404(Message, pk=id)

    upload_url, upload_data = prepare_upload(request, reverse('portal.messages.views.attach_file'))
    instance = message.content_type.get_object_for_this_type(pk=message.object_pk)

    ctx = {
        'message'     : message,
        'msg_form'    : MessageForm(instance),
        'attach_form' : AttachmentForm(),
        'upload_url'  : upload_url,
        'upload_data' : upload_data,
        'content_type': '.'.join([message.content_type.app_label, message.content_type.model]),
        'object_pk'   : message.object_pk,
    }

    return direct_to_template(request, 'messages/detail.html', ctx)