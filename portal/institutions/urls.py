from django.conf.urls.defaults import *

urlpatterns = patterns('portal.institutions.views',
    (r'^$', 'index'),
    (r'^save/$', 'save'),
    (r'^delete/(?P<slug>.+)/$', 'delete'),
    (r'^edit/(?P<slug>.+)/$', 'save'),
    (r'^get_news/(?P<slug>.+)/(?P<first>\d+)/(?P<nresults>\d+)/$', 'get_news'),
    (r'^get_updates/(?P<slug>.+)/$', 'get_updates'),
    (r'^get_teachers/(?P<slug>.+)/$', 'get_teachers'),
    (r'^get_students/(?P<slug>.+)/$', 'get_students'),
    (r'^save_picture/(?P<slug>.+)/$', 'save_picture'),
    (r'^rebuild_caches/(?P<slug>.+)/$', 'rebuild_caches_view'),
)