from django.conf.urls.defaults import *

urlpatterns = patterns('portal.album.views',
    (r'^save/(?P<class_name>.+)/(?P<slug>.+)/$', 'save'),
    (r'^detail/(?P<class_name>.+)/(?P<slug>.+)/(?P<album_id>\d+)/$', 'detail'),
    (r'^add/(?P<class_name>.+)/(?P<slug>.+)/(?P<album_id>\d+)/$', 'add_picture'),
)