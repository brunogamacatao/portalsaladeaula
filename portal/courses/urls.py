from django.conf.urls.defaults import *

urlpatterns = patterns('portal.courses.views',
    (r'^save/(?P<inst_slug>.+)/$', 'save'),
    (r'^edit/(?P<inst_slug>.+)/(?P<course_slug>.+)/$', 'save'),
    (r'^delete/(?P<inst_slug>.+)/(?P<course_slug>.+)/$', 'delete'),
    (r'^save_picture/(?P<id>\d+)/$', 'save_picture'),
    (r'^get_news/(?P<id>\d+)/(?P<first>\d+)/(?P<nresults>\d+)/$', 'get_news'),
    (r'^get_disciplines/(?P<id>\d+)/(?P<first>\d+)/(?P<nresults>\d+)/$', 'get_disciplines'),
    (r'^get_teachers/(?P<inst_slug>.+)/(?P<course_slug>.+)/$', 'get_teachers'),
    (r'^get_students/(?P<inst_slug>.+)/(?P<course_slug>.+)/$', 'get_students'),
    (r'^rebuild_caches/(?P<inst_slug>.+)/(?P<course_slug>.+)/$', 'rebuild_caches_view'),
)