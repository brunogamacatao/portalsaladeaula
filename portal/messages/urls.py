from django.conf.urls.defaults import *

urlpatterns = patterns('portal.messages.views',
    (r'^post_message/$', 'post_message'),
    (r'^post_reply/$', 'post_reply'),
    (r'^attach_file/$', 'attach_file'),
    (r'^result_attach_file/(?P<id>[^/]+)/$', 'result_attach_file'),
    (r'^get_message/(?P<id>[^/]+)/$', 'get_message'),
    (r'^download_attachment/(?P<id>[^/]+)/$', 'download_attachment'),
)