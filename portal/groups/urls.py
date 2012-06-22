from django.conf.urls.defaults import *

urlpatterns = patterns('portal.groups.views',
    (r'^$', 'index'),
)