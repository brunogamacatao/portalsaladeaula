from django.conf.urls.defaults import *

urlpatterns = patterns('portal.disciplines.views',
    (r'^save/(?P<inst_slug>.+)/(?P<course_slug>.+)/$', 'save'),
    (r'^edit/(?P<inst_slug>.+)/(?P<course_slug>.+)/(?P<disc_slug>.+)/$', 'save'),
    (r'^delete/(?P<inst_slug>.+)/(?P<course_slug>.+)/(?P<disc_slug>.+)/$', 'delete'),
    (r'^save_picture/(?P<id>\d+)/$', 'save_picture'),
    (r'^get_news/(?P<id>\d+)/(?P<first>\d+)/(?P<nresults>\d+)/$', 'get_news'),
    (r'^get_discipline/$', 'get_discipline'),
    (r'^register/(?P<inst_slug>.+)/(?P<course_slug>.+)/(?P<disc_slug>.+)/$', 'register'),
)