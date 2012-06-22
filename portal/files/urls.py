from django.conf.urls.defaults import *

urlpatterns = patterns('portal.files.views',
    (r'^upload/(?P<class_name>.+)/(?P<id>.+)/$', 'upload'),
    (r'^download/(?P<id>.+)/$', 'download'),
    (r'^view/(?P<id>[^/]+)/(?P<filename>.+)/$', 'view'),
    (r'^delete/(?P<id>[^/]+)/(?P<next_url>.+)/$', 'delete'),
)