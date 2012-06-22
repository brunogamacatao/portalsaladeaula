from django.conf.urls.defaults import *
from django.contrib import admin

handler500 = 'djangotoolbox.errorviews.server_error'

from django.contrib import admin
from django.contrib.auth.views import login, logout
import os

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
#    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'static')}),
    (r'^accounts/login/$', login),
    (r'^accounts/logout/$', logout, {'next_page': "/", }),
    (r'^accounts/', include('portal.accounts.urls')),
    (r'^comments/', include('django.contrib.comments.urls')),
    (r'^', include('portal.urls')),
)
