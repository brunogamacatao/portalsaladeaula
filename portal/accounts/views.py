# -*- coding: utf-8 -*-
import re
import random
import logging
import datetime

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

from filetransfers.api import prepare_upload
from mediagenerator.utils import media_url

from portal.models import UserInfo, Picture, PreInscricao, Institution
from portal.models import Discipline, DisciplineMetadata
from portal.models import RelUserDiscipline, UserDisciplineRole, RelUserCourse, UserCourseRole
from portal.models import RelUserInstitution, UserInstitutionRole
from portal.accounts.forms import RegisterUserForm, UserInfoForm
from portal.utils import get_hora_inicio_fim
from portal.messages.forms import MessageForm, AttachmentForm
from portal.institutions.views import rebuild_caches as rebuild_caches_institution
from portal.courses.views import rebuild_caches as rebuild_caches_course

from settings import PERIODO_ATUAL

@csrf_protect
def register(request):
    form  = None

    if request.method == 'GET':
        form = RegisterUserForm()
    else:
        form = RegisterUserForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            username   = data['email']
            email      = data['email']
            password   = data['password']

            User.objects.create_user(username, email, password).save()
            user = authenticate(username=username, password=password)
            login(request, user)
            
            return HttpResponseRedirect(reverse('portal.accounts.views.fill_user_info'))

    ctx = {
        'form': form,
    }

    return direct_to_template(request, 'registration/form.html', ctx)

@csrf_protect
@login_required
def fill_user_info(request):
    form  = None

    if request.method == 'GET':
        if UserInfo.objects.filter(user=request.user).exists():
            form = UserInfoForm(instance=request.user.get_profile())
        else:
            form = UserInfoForm()
    else:
        if UserInfo.objects.filter(user=request.user).exists():
            form = UserInfoForm(request.POST, instance=request.user.get_profile())
        else:
            form = UserInfoForm(request.POST)

        if form.is_valid():
            user_info = form.save(commit=False)
            user_info.user  = request.user
            user_info.email = request.user.email

            if request.POST['picture_id']:
                picture = Picture.objects.get(pk=int(request.POST['picture_id']))
                user_info.picture = picture
            
            user_info.save()

            user = request.user
            user.first_name = user_info.name.split()[0]
            user.last_name  = ' '.join(user_info.name.split()[1:])
            user.save()

            return HttpResponseRedirect(reverse('portal.views.index'))

    ctx = {
        'form': form,
    }

    try:
        if request.user.get_profile().picture:
            ctx['picture'] = request.user.get_profile().picture
    except:
        pass

    return direct_to_template(request, 'registration/register.html', ctx)

@csrf_protect
@login_required
def set_picture(request):
    picture = Picture()
    picture.picture = request.FILES['picture'].read()
    picture.save()
    request.session['picture_id'] = picture.id
    thumb       = Picture.create_thumbnail(picture, 200, 200)
    thumb_small = Picture.create_thumbnail(picture, 50, 50)

    return HttpResponse('{"result":{"picture_id":%s,"thumb_id":%s,"width":%d,"height":%d,"thumb_small_id":%s}}' % (str(picture.id), thumb.id, thumb.width, thumb.height, thumb_small.id), 'text/html', 200)

@csrf_protect
@login_required
def save_picture(request):
    picture = Picture.objects.get(pk=request.POST['picture_id'])
    user_info = request.user.get_profile()
    user_info.picture = picture
    user_info.save()

    thumb       = Picture.create_thumbnail(picture, 180, 180)
    thumb_small = Picture.create_thumbnail(picture, 50, 50)

    return HttpResponse('{"result":{"picture_id":%s,"thumb_id":%s,"width":%d,"height":%d,"thumb_small_id":%s}}' % (str(picture.id), thumb.id, thumb.width, thumb.height, thumb_small.id), 'text/html', 200)

@login_required
def choose_profile(request):
    #Mostrar aqui a tela de escolha: você é professor ou aluno ?
    return direct_to_template(request, 'registration/choose_profile.html')

@login_required
def profile(request):
    return HttpResponseRedirect(reverse('portal.accounts.views.user_info', args=[request.user.id,]))

def user_info(request, user_id):
    user      = User.objects.get(pk=user_id)
    user_info = user.get_profile()

    horario_tbl = None

    if user_info.schedule_cache:
        horario_tbl = user_info.schedule_cache
    else:
        dias      = ('segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado')
        cores     = ('#BFCFF2', '#F1c8c8', '#FFCBB6', '#FFFFAA', '#D7BCF2', '#BBBBFF', '#A1EDB2', '#BBFFFF', '#FFF7D7')
        cor_atual = 0
        horarios  = []

        if user_info.is_teacher or user_info.get_disciplines_studies():
            disciplinas = []

            if user_info.is_teacher:
                disciplinas = [d.disciplinemetadata_set.all()[0] for d in user_info.get_disciplines_teaches() if d.disciplinemetadata_set.exists()]
            else:
                disciplinas = [d.disciplinemetadata_set.all()[0] for d in user_info.get_disciplines_studies() if d.disciplinemetadata_set.exists()]

            horario_tbl = u'<h2>Horário</h2>'
            horario_tbl += u'<table id="horario_table">\n'
            horario_tbl += u'<thead><tr><th>&nbsp;</th><th>Segunda</th><th>Terça</th><th>Quarta</th><th>Quinta</th><th>Sexta</th><th>Sábado</th></tr></thead>\n'
            horario_tbl += u'<tbody>\n'

            for d in disciplinas:
                for dia in range(0, 6):
                    if d.__dict__[dias[dia]] and d.__dict__[dias[dia]] != 'null':
                        horarios += get_hora_inicio_fim(d.__dict__[dias[dia]])
            horarios = set(horarios)
            horarios = list(horarios)
            horarios.sort()

            rowspan_map     = {}
            rowspan_app_map = {}

            for hora in horarios:
                for dia in range(0, 6):
                    for d in disciplinas:
                        if d.__dict__[dias[dia]] and d.__dict__[dias[dia]] != 'null':
                            horario = get_hora_inicio_fim(d.__dict__[dias[dia]])
                            if hora >= horario[0] and hora < horario[1]:
                                key = (dia, d)
                                qtd = 0
                                if rowspan_map.has_key(key): qtd = rowspan_map[key]
                                rowspan_map[key] = qtd + 1

            for i in range(len(horarios)):
                hora = horarios[i]
                qtd_hora = 0

                if i < len(horarios) - 1:
                    hora_fim = horarios[i + 1]
                    horario_tmp = u'<tr><th>%02d:%02d<br/>%02d:%02d</th>' % (hora.hour, hora.minute,hora_fim.hour, hora_fim.minute)
                else:
                    horario_tmp = u'<tr><th>%02d:%02d</th>' % (hora.hour, hora.minute)

                for dia in range(0, 6):
                    qtd_dia = 0
                    for d in disciplinas:
                        if d.__dict__[dias[dia]] and d.__dict__[dias[dia]] != 'null':
                            horario = get_hora_inicio_fim(d.__dict__[dias[dia]])

                            if hora >= horario[0] and hora < horario[1]:
                                qtd_dia  += 1
                                qtd_hora += 1

                                key = (dia, d)

                                if not rowspan_app_map.has_key(key):
                                    rowspan_app_map[key] = True

                                    tooltip = u''

                                    if d.discipline.picture:
                                        tooltip += u"<img src='/image/%d/'/>" % Picture.get_thumbnail(d.discipline.picture, 50, 50).id
                                    else:
                                        tooltip += u"<img src='%s' width='50px' height='50px'/>" % media_url('images/books.png')
                                    tooltip += u'%s<br/>'% d.discipline.name
                                    tooltip += u'<b>Sala:</b> %s<br/>' % d.discipline.get_sala()
                                    tooltip += u'<b>Horário:</b> %s' % d.discipline.get_horario().replace('\n', '<br/>')

                                    link = reverse('portal.disciplines.views.detail', args=[d.discipline.course.institution.slug, d.discipline.course.slug, d.discipline.slug])

                                    img = None
                                    if d.discipline.picture:
                                        img = u"<img src='/image/%d/'/>" % Picture.get_thumbnail(d.discipline.picture, 10, 10).id
                                    else:
                                        img = u"<img src='%s' width='10px' height='10px'/>" % media_url('images/books.png')
                                    horario_tmp += u'<td rowspan="%d" class="filled" style="background-color:%s" title="%s"><div>%s<a href="%s">%s</a></div></td>' % (rowspan_map[key], cores[cor_atual], tooltip, img, link, d.discipline.name.split('-')[0])
                                    cor_atual = (cor_atual + 1) % len(cores)
                                break;
                    if qtd_dia == 0:
                        horario_tmp += u'<td>&nbsp;</td>'
                horario_tmp += u'</tr>\n'
                if qtd_hora > 0:
                    horario_tbl += horario_tmp
            horario_tbl += u'</tbody></table>'
        if len(horarios) == 0:
            horario_tbl = ''
            disciplinas = []

            if user_info.is_teacher:
                disciplinas = user_info.get_disciplines_teaches()
            else:
                disciplinas = user_info.get_disciplines_studies()

            if len(disciplinas) > 0:
                horario_tbl += '<h2>Disciplinas</h2>'
                horario_tbl += '<ul class="item_list">'

                for d in disciplinas:
                    horario_tbl += '<li>'
                    horario_tbl += '<a href="%s">' % reverse('portal.disciplines.views.detail', args=[d.course.institution.slug, d.course.slug, d.slug])
                    if d.picture:
                        horario_tbl += '<img src="/image/%d/"/>' % Picture.get_thumbnail(d.picture, 50, 50).id
                    else:
                        horario_tbl += '<img src="%s" width="50px" height="50px"/>' % media_url('images/books.png')
                    horario_tbl += '<p>%s</p>' % d.name
                    horario_tbl += '</a>'
                    horario_tbl += '</li>'

                horario_tbl += '</ul>'
        user_info.schedule_cache = horario_tbl
        user_info.save()

    msg_form = MessageForm(user.get_profile())
    upload_url, upload_data = prepare_upload(request, reverse('portal.messages.views.attach_file'))

    ctx = {
        'user_obj'   : user,
        'profile'    : user.get_profile(),
        'horario'    : horario_tbl,
        'msg_form'   : msg_form,
        'attach_form': AttachmentForm(),
        'upload_url' : upload_url,
        'upload_data': upload_data,
        'next'       : request.get_full_path(),
    }

    return direct_to_template(request, 'registration/profile.html', ctx)

@csrf_protect
def adicionar_aluno(request):
    logging.info('adicionar_aluno')

    matricula = request.POST['matricula']
    cpf       = re.sub(r'[\.-]', '', request.POST['cpf'])
    queryset  = PreInscricao.objects.filter(matricula=matricula, cpf=cpf)

    if not queryset.exists():
        logging.error(u'[adicionar_aluno] - O usuário (matrícula: %s, cpf: %s) não foi encontrado' % (matricula, cpf,))
        return HttpResponse('{"status":"erro","mensagem":"Não foi possível localizar um aluno com os dados informados"}')

    try:
        if queryset[0].user_info:
            logging.error(u'[adicionar_aluno] - O usuário (matrícula: %s, cpf: %s) já está cadastrado' % (matricula, cpf,))
            return HttpResponse('{"status":"erro","mensagem":"Você já está cadastrado no portal, faça o login normalmente"}')
    except:
        pass

    try:
        if UserInfo.objects.filter(email=queryset[0].email).exists():
            logging.error(u'[adicionar_aluno] - O usuário (matrícula: %s, cpf: %s) já está cadastrado' % (matricula, cpf,))
            return HttpResponse('{"status":"erro","mensagem":"Você já está cadastrado no portal, faça o login normalmente"}')
    except:
        pass

    dados_aluno = queryset[0]
    data_nasc   = '%02d/%02d/%04d' % (dados_aluno.data_nasc.day,dados_aluno.data_nasc.month,dados_aluno.data_nasc.year)

    return HttpResponse('{"status":"ok","nome":"%s","email":"%s","data_nasc":"%s"}' % (dados_aluno.nome, dados_aluno.email,data_nasc,))

@csrf_protect
def confirma_adicionar_aluno(request):
    logging.info('confirma_adicionar_aluno')

    matricula   = request.POST['matricula']
    cpf         = re.sub(r'[\.-]', '', request.POST['cpf'])
    nome        = request.POST['nome']
    email       = request.POST['email']
    queryset    = PreInscricao.objects.filter(matricula=matricula, cpf=cpf)
    senha       = request.POST['senha']
    aluno_role  = UserDisciplineRole.objects.student_role()
    dados_aluno = queryset[0]

    data_nasc = request.POST['data_nasc']
    data_nasc = data_nasc.split('/')
    data_nasc = datetime.date(int(data_nasc[2]), int(data_nasc[1]), int(data_nasc[0]))

    if User.objects.filter(username=email).exists():
        User.objects.filter(username=email).delete()
    User.objects.create_user(email, email, senha).save()
    user = authenticate(username=email, password=senha)

    if UserInfo.objects.filter(email=email).exists():
        #Caso ja exista um usuario, exclui ele do banco
        for u in UserInfo.objects.filter(email=email):
            for r in RelUserInstitution.objects.filter(user__id=u.id):
                r.delete()
            for r in RelUserCourse.objects.filter(user__id=u.id):
                r.delete()
            for r in RelUserDiscipline.objects.filter(user__id=u.id):
                r.delete()
            u.delete()

    user_info = UserInfo(name=nome,city=dados_aluno.cidade,province=dados_aluno.estado,email=email, user=user, birth_date=data_nasc)
    user_info.save()

    dados_aluno.data_nasc = data_nasc
    dados_aluno.nome      = nome
    dados_aluno.email     = email
    dados_aluno.user_info = user_info
    dados_aluno.save()

    login(request, user)
    institutions = set()
    courses      = set()

    for id_disc in dados_aluno.disciplinas:
        try:
            disciplina = DisciplineMetadata.objects.get(cod_turma=id_disc, periodo=PERIODO_ATUAL).discipline

            institutions.add(disciplina.course.institution.id)
            courses.add(disciplina.course.id)

            #Associando a disciplina ao aluno
            queryset = RelUserDiscipline.objects.filter(role=aluno_role, user=user_info, discipline=disciplina, period=PERIODO_ATUAL)
            if not queryset.exists():
                RelUserDiscipline(user=user_info, discipline=disciplina, role=aluno_role, period=PERIODO_ATUAL).save()

            #Associando o aluno ao curso
            queryset = RelUserCourse.objects.filter(role=UserCourseRole.objects.student_role(), user=user_info, course=disciplina.course, period=PERIODO_ATUAL)
            if not queryset.exists():
                RelUserCourse(role=UserCourseRole.objects.student_role(), user=user_info, course=disciplina.course, period=PERIODO_ATUAL).save()

            #Associando o aluno à instituição de ensino
            queryset = RelUserInstitution.objects.filter(role=UserInstitutionRole.objects.student_role(), user=user_info, institution=disciplina.course.institution, period=PERIODO_ATUAL)
            if not queryset.exists():
                RelUserInstitution(role=UserInstitutionRole.objects.student_role(), user=user_info, institution=disciplina.course.institution, period=PERIODO_ATUAL).save()
        except Exception, e:
            logging.exception(e)            
            logging.error("[confirma_adicionar_aluno] - Nao foi possivel localizar a disciplina %s" % id_disc)

    #Para cada uma das instituicoes afetadas
    for inst in institutions:
        rebuild_caches_institution(inst) #Reconstroi a sua cache
    #Para cada um dos cursos afetados
    for course in courses:
        rebuild_caches_course(course)

    return HttpResponseRedirect(reverse('portal.views.index'))

@csrf_protect
def confirma_adicionar_professor(request):
    nome        = request.POST['nome']
    email       = request.POST['email']
    data_nasc   = request.POST['data_nasc']
    data_nasc   = data_nasc.split('/')
    data_nasc   = datetime.date(int(data_nasc[2]), int(data_nasc[1]), int(data_nasc[0]))
    senha       = request.POST['senha']
    disciplinas = request.POST['disciplinas'] != '' and request.POST['disciplinas'].split(',') or []
    instituicao = Institution.objects.get(slug=request.POST['instituicao'])

    if User.objects.filter(username=email).exists():
        User.objects.filter(username=email).delete()

    User.objects.create_user(email, email, senha).save()
    user = authenticate(username=email, password=senha)
    user_info = UserInfo(name=nome, email=email, is_teacher=True, birth_date=data_nasc, user=user)
    user_info.save()

    #Associando o professor à instituição de ensino
    queryset = RelUserInstitution.objects.filter(role=UserInstitutionRole.objects.teacher_role(), user=user_info, institution=instituicao)
    if not queryset.exists():
        RelUserInstitution(role=UserInstitutionRole.objects.teacher_role(), user=user_info, institution=instituicao).save()
    rebuild_caches_institution(instituicao.id)

    login(request, user)
    institutions = set()
    courses      = set()

    for d in disciplinas:
        discipline = Discipline.objects.get(pk=d)

        institutions.add(discipline.course.institution.id)
        courses.add(discipline.course.id)

        #Associando a disciplina ao professor
        queryset = RelUserDiscipline.objects.filter(user=user_info, discipline=discipline, role=UserDisciplineRole.objects.teacher_role())
        if not queryset.exists():
            RelUserDiscipline(user=user_info, discipline=discipline, role=UserDisciplineRole.objects.teacher_role()).save()

        #Associando o professor ao curso
        queryset = RelUserCourse.objects.filter(role=UserCourseRole.objects.teacher_role(), user=user_info, course=discipline.course)
        if not queryset.exists():
            RelUserCourse(role=UserCourseRole.objects.teacher_role(), user=user_info, course=discipline.course).save()

        #Associando o professor à instituição de ensino
        queryset = RelUserInstitution.objects.filter(role=UserInstitutionRole.objects.teacher_role(), user=user_info, institution=discipline.course.institution)
        if not queryset.exists():
            RelUserInstitution(role=UserInstitutionRole.objects.teacher_role(), user=user_info, institution=discipline.course.institution).save()

    #Para cada uma das instituicoes afetadas
    for inst in institutions:
        rebuild_caches_institution(inst) #Reconstroi a sua cache
    #Para cada um dos cursos afetados
    for course in courses:
        rebuild_caches_course(course)

    return HttpResponseRedirect(reverse('portal.views.index'))

@csrf_protect
@login_required
def add_disciplines(request):
    disciplinas = request.POST['disciplinas'].split(',')
    user_info   = request.user.get_profile()

    for d in disciplinas:
        discipline = Discipline.objects.get(pk=d)

        #Associando a disciplina ao professor
        queryset = RelUserDiscipline.objects.filter(user=user_info, discipline=discipline, role=UserDisciplineRole.objects.teacher_role(), period=PERIODO_ATUAL)
        if not queryset.exists():
            RelUserDiscipline(user=user_info, discipline=discipline, role=UserDisciplineRole.objects.teacher_role(), period=PERIODO_ATUAL).save()

        #Associando o curso ao professor
        queryset = RelUserCourse.objects.filter(role=UserCourseRole.objects.teacher_role(), user=user_info, course=discipline.course, period=PERIODO_ATUAL)
        if not queryset.exists():
            RelUserCourse(role=UserCourseRole.objects.teacher_role(), user=user_info, course=discipline.course, period=PERIODO_ATUAL).save()

        #Associando o professor à instituição de ensino
        queryset = RelUserInstitution.objects.filter(role=UserInstitutionRole.objects.teacher_role(), user=user_info, institution=discipline.course.institution, period=PERIODO_ATUAL)
        if not queryset.exists():
            RelUserInstitution(role=UserInstitutionRole.objects.teacher_role(), user=user_info, institution=discipline.course.institution, period=PERIODO_ATUAL).save()


    #Limpando a cache de disciplinas do professor
    user_info.schedule_cache = None
    user_info.save()

    return HttpResponseRedirect(reverse('portal.views.index'))

def genPassword(length=6):
	vogais = 'aeiou'
	consoantes = 'bcdfghjlmnpqrstvxz'
	str = ''
	for i in range(length/2):
		str += consoantes[random.randint(0, len(consoantes) - 1)]
		str += vogais[random.randint(0, len(vogais) - 1)]
	return str

@csrf_protect
def reset_email(request):
    try:
        user = User.objects.get(email=request.POST['email'])

        password = genPassword()
        user.set_password(password)
        user.save()

        subject    = 'Sua nova senha no portal'
        from_email = 'Portal Sala de Aula <gerencia@portalsaladeaula.com>'
        message    = 'Como você solicitou, foi gerada uma nova senha para acesso ao Portal Sala de Aula\n'
        message   += 'Sua nova senha é: %s' % (password,)

        try:
            user.email_user(subject, message, from_email)
        except:
            logging.error('Não foi possível enviar o email com a senha %s' % password)
    except:
        logging.error('Nào foi possível encontrar o aluno')

    return HttpResponseRedirect(reverse('portal.views.index'))

#Funcoes responsaveis pelo novo fluxo de cadastro do portal