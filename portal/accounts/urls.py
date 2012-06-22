from django.conf.urls.defaults import *

urlpatterns = patterns('portal.accounts.views',
    (r'^register/$', 'register'),
    (r'^profile/$', 'profile'),
    (r'^user_info/(?P<user_id>\d+)/$', 'user_info'),
    (r'^fill_user_info/$', 'fill_user_info'),
    (r'^choose_profile/$', 'choose_profile'),
    (r'^set_picture/$', 'set_picture'),
    (r'^save_picture/$', 'save_picture'),
    (r'^adicionar_aluno/$', 'adicionar_aluno'),
    (r'^confirma_adicionar_aluno/$', 'confirma_adicionar_aluno'),
    (r'^confirma_adicionar_professor/$', 'confirma_adicionar_professor'),
    (r'^add_disciplines/$', 'add_disciplines'),
    (r'^reset_email/$', 'reset_email'),
)