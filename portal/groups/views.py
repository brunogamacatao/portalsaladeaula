# -*- coding: utf-8 -*-
from django.http import HttpResponse, Http404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template

import re
from time import mktime
from datetime import datetime
from feedparser import feedparser

from .forms import GroupForm
from .models import Group


def index(request):
    return HttpResponse('Funciona !')