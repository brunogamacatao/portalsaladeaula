# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.cache import cache_page

from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate

import re
import logging
from portal.models import Institution, Course, Discipline, Picture, \
    DisciplineMetadata, RelUserDiscipline, RelDisciplineOwner, RelUserCourse, \
    RelUserInstitution, UserInfo, UserDisciplineRole, UserCourseRole, \
    UserInstitutionRole, Update
from portal.accounts.forms import RegisterUserForm
from settings import DEFAULT_ENCODING, PERIODO_ATUAL

from portal.institutions.views import rebuild_caches as rebuild_caches_institution
from portal.courses.views import rebuild_caches as rebuild_caches_course

def autenticar(request, matricula, rowguid):
    aluno = PreInscricao.objects.get(matricula=matricula)

    try:
        user = aluno.user_info.user
        user = authenticate(username=matricula, password=rowguid)
        if not user:
            user = aluno.user_info.user
            user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        request.session['site_interno'] = True

        return HttpResponseRedirect(reverse('portal.accounts.views.user_info', args=[request.user.id,]))
    except:
        aluno_role = UserDisciplineRole.objects.student_role()
        User.objects.create_user(aluno.email, aluno.email, rowguid).save()
        user = authenticate(username=aluno.email, password=rowguid)
        user_info = UserInfo(name=aluno.nome,city=aluno.cidade,province=aluno.estado,email=aluno.email, user=user, birth_date=aluno.data_nasc)
        user_info.save()
        aluno.user_info = user_info
        aluno.save()
        login(request, user)

        institutions = set()
        courses      = set()

        for id_disc in aluno.disciplinas:
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

        request.session['site_interno'] = True
        return HttpResponseRedirect(reverse('portal.accounts.views.user_info', args=[request.user.id,]))

def get_atualizacoes(request, matricula):
    try:
        aluno = PreInscricao.objects.get(matricula=matricula)
        atualizacoes = Update.objects.for_model(aluno.user_info).count()
        return HttpResponse('%d' % atualizacoes)
    except:
        return HttpResponse('0')

@csrf_protect
def index(request):
    if request.session.has_key('site_interno'):
        del request.session['site_interno']

    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('portal.accounts.views.user_info', args=[request.user.id,]))

    ctx = {
        'institutions': Institution.objects.all(),
        'courses':      Course.objects.all(),
        'form':         RegisterUserForm(),
    }

    return direct_to_template(request, 'public_index.html', ctx)

@cache_page(60 * 5)
def image(request, picture_id):
    picture = Picture.objects.get(pk=picture_id)
    response = HttpResponse(picture.picture, mimetype="image/%s" % picture.format)
    response['Cache-Control'] = 'max-age=500, must-revalidate'
    return response

def trim(string):
    return re.sub(r'^\s+', '', re.sub(r'\s+$', '', string))

@csrf_protect
@login_required
def importar_disciplinas(request):
    if request.method == 'POST':
        erros   = ''
        course  = Course.objects.get(slug__exact=request.POST['course_slug'])
        arquivo = request.FILES['disciplinas'].readlines()

        for i in range(0, len(arquivo), 11):
            try:
                d_name  = trim(unicode(arquivo[i],      DEFAULT_ENCODING)[:-1])
                d_turno = trim(unicode(arquivo[i + 1],  DEFAULT_ENCODING)[:-1])
                d_turma = trim(unicode(arquivo[i + 2],  DEFAULT_ENCODING)[:-1])
                d_senha = trim(unicode(arquivo[i + 3],  DEFAULT_ENCODING)[:-1])
                d_seg   = trim(unicode(arquivo[i + 4],  DEFAULT_ENCODING)[:-1])
                d_ter   = trim(unicode(arquivo[i + 5],  DEFAULT_ENCODING)[:-1])
                d_qua   = trim(unicode(arquivo[i + 6],  DEFAULT_ENCODING)[:-1])
                d_qui   = trim(unicode(arquivo[i + 7],  DEFAULT_ENCODING)[:-1])
                d_sex   = trim(unicode(arquivo[i + 8],  DEFAULT_ENCODING)[:-1])
                d_sab   = trim(unicode(arquivo[i + 9],  DEFAULT_ENCODING)[:-1])
                d_sala  = trim(unicode(arquivo[i + 10], DEFAULT_ENCODING)[:-1])

                description = u'Página da disciplina %s' % d_name
                d_name = u'%s - %s' % (d_name, d_turno, )

                '''
                Caso já existam metadados cadastrados para esta turma, estes
                serão atualizados a partir dos valores informados no arquivo.
                Caso contrário um novo registro será criado no banco de dados.
                '''
                if DisciplineMetadata.objects.filter(cod_turma=d_turma, periodo=PERIODO_ATUAL).exists():
                    mdata = DisciplineMetadata.objects.filter(cod_turma=d_turma, periodo=PERIODO_ATUAL).all()[0]

                    #Checar se existe uma disciplina vinculada
                    if not mdata.discipline:
                        discipline = Discipline(name=d_name, description=description, course=course, period=PERIODO_ATUAL).save()
                        RelDisciplineOwner(discipline=discipline, owner=request.user.get_profile()).save()
                        mdata.discipline = discipline
                    #Mesmo que os metadados existam, atualiza os seus valores
                    mdata.cod_turma  = d_turma
                    mdata.periodo    = PERIODO_ATUAL
                    mdata.senha      = d_senha
                    mdata.segunda    = d_seg
                    mdata.terca      = d_ter
                    mdata.quarta     = d_qua
                    mdata.quinta     = d_qui
                    mdata.sexta      = d_sex
                    mdata.sabado     = d_sab
                    mdata.sala       = d_sala
                    mdata.save()
                else:
                    discipline = Discipline(name=d_name, description=description, course=course, period=PERIODO_ATUAL)
                    discipline.save()
                    RelDisciplineOwner(discipline=discipline, owner=request.user.get_profile()).save()
                    DisciplineMetadata(discipline=discipline,cod_turma=d_turma,periodo=PERIODO_ATUAL,senha=d_senha,
                                       segunda=d_seg,terca=d_ter,quarta=d_qua,quinta=d_qui,sexta=d_sex,
                                       sabado=d_sab,sala=d_sala).save()
            except:
                logging.error('Erro ao importar a disciplina %s' % arquivo[i])
                erros += '<p>Erro ao importar a disciplina %s - %s</p>' % (arquivo[i], arquivo[i + 2])

        return HttpResponse('<h1>Log de execucao:</h1><br/> %s' % erros)

    return direct_to_template(request, 'importar_disciplinas.html')

@csrf_protect
@login_required
def corrigir_disciplinas(request):
    log_execucao = '<h1>Log de execucao</h1><br/>'

    d_role = UserDisciplineRole.objects.student_role()
    c_role = UserCourseRole.objects.student_role()
    i_role = UserInstitutionRole.objects.student_role()

    for aluno in UserInfo.objects.filter():
        if not aluno.is_teacher or aluno.is_teacher == False:
            #Achei um aluno !
            if aluno.preinscricao_set.exists() and aluno.preinscricao_set.count() > 0:
                dados_aluno = aluno.preinscricao_set.all()[0]
                for d in dados_aluno.disciplinas:
                    if DisciplineMetadata.objects.filter(cod_turma=d).exists():
                        discipline = DisciplineMetadata.objects.get(cod_turma=d).discipline
                        if not RelUserDiscipline.objects.filter(user=aluno, discipline=discipline).exists():
                            RelUserDiscipline(user=aluno, discipline=discipline, role=d_role).save()
                            log_execucao += '<p>Adicionada a disciplina %s para o aluno %s</p>' % (discipline.name, aluno.name, )
                        if not RelUserCourse.objects.filter(user=aluno, course=discipline.course).exists():
                            RelUserCourse(user=aluno, course=discipline.course, role=c_role).save()
                            log_execucao += '<p>Adicionado o curso %s para o aluno %s</p>' % (discipline.course.name, aluno.name, )
                        if not RelUserInstitution.objects.filter(user=aluno, institution=discipline.course.institution).exists():
                            RelUserInstitution(user=aluno, institution=discipline.course.institution, role=i_role).save()
                            log_execucao += '<p>Adicionada a instituicao %s para o aluno %s</p>' % (discipline.course.institution.name, aluno.name, )
                    else:
                        log_execucao += '<p>ERRO - Nao foi possivel localizar a disciplina %s</p>' % d

    return HttpResponse(log_execucao)

import datetime
from portal.models import PreInscricao
@csrf_protect
@login_required
def importar_alunos(request):
    if request.method == 'POST':
        arquivo    = request.FILES['alunos'].readlines()
        aluno_role = UserDisciplineRole.objects.student_role()


        for i in range(0, len(arquivo), 13):
            matricula   = unicode(arquivo[i],      DEFAULT_ENCODING)[:-1]
            nome        = unicode(arquivo[i + 1],  DEFAULT_ENCODING)[:-1]
            cpf         = unicode(arquivo[i + 2],  DEFAULT_ENCODING)[:-1]
            sexo        = unicode(arquivo[i + 3],  DEFAULT_ENCODING)[:-1]
            email       = unicode(arquivo[i + 4],  DEFAULT_ENCODING)[:-1]
            data_nasc   = unicode(arquivo[i + 5],  DEFAULT_ENCODING)
            rua         = unicode(arquivo[i + 6],  DEFAULT_ENCODING)[:-1]
            numero      = unicode(arquivo[i + 7],  DEFAULT_ENCODING)[:-1]
            bairro      = unicode(arquivo[i + 8],  DEFAULT_ENCODING)[:-1]
            cidade      = unicode(arquivo[i + 9],  DEFAULT_ENCODING)[:-1]
            estado      = unicode(arquivo[i + 10], DEFAULT_ENCODING)[:-1]
            senha       = unicode(arquivo[i + 11], DEFAULT_ENCODING)[:-1]
            disciplinas = unicode(arquivo[i + 12], DEFAULT_ENCODING)[:-1]

            try:
                data_nasc = data_nasc.split('/')
                data_nasc = datetime.date(int(data_nasc[2]), int(data_nasc[1]), int(data_nasc[0]))
            except:
                data_nasc = datetime.date.today()

            disciplinas  = set(disciplinas.split(','))
            institutions = set()
            courses      = set()

            cria_pre_inscricao = False

            # Verificando se o aluno já está inscrito no sistema
            # Verificar se há pré-inscrição
            # Caso haja, verificar se o mesmo já se inscreveu no sistema
            if PreInscricao.objects.filter(matricula=matricula):
                dados_aluno = PreInscricao.objects.filter(matricula=matricula).all()[0]
                dados_aluno.disciplinas = disciplinas
                dados_aluno.save()
                # Verificando se o respectivo aluno realmente já se inscreveu no portal
#                try:
#                    dados_aluno.user_info
#                    logging.info("[INFO] ENCONTRAMOS O ALUNO: %s" % nome)
#                    user_info = dados_aluno.user_info
#
#                    #Neste caso, adicionar as suas novas disciplinas
#                    for id_disc in disciplinas:
#                        try:
#                            disciplina = DisciplineMetadata.objects.get(cod_turma=id_disc, periodo=PERIODO_ATUAL).discipline
#                            logging.info("    [INFO] ENCONTRADA A DISCIPLINA: %s" % id_disc)
#
#                            institutions.add(disciplina.course.institution.id)
#                            courses.add(disciplina.course.id)
#
#                            #Associando a disciplina ao aluno
#                            queryset = RelUserDiscipline.objects.filter(role=aluno_role, user=user_info, discipline=disciplina, period=PERIODO_ATUAL)
#                            if not queryset.exists():
#                                logging.info("        [INFO] CADASTRANDO O ALUNO NA DISCIPLINA: %s" % disciplina.name)
#                                RelUserDiscipline(user=user_info, discipline=disciplina, role=aluno_role, period=PERIODO_ATUAL).save()
#                            else:
#                                logging.info("        [INFO] O ALUNO JA ESTAVA CADASTRADO NA DISCIPLINA")
#
#                            #Associando o aluno ao curso
#                            queryset = RelUserCourse.objects.filter(role=UserCourseRole.objects.student_role(), user=user_info, course=disciplina.course, period=PERIODO_ATUAL)
#                            if not queryset.exists():
#                                logging.info("        [INFO] CADASTRANDO O ALUNO NO CURSO: %s" % disciplina.course.name)
#                                RelUserCourse(role=UserCourseRole.objects.student_role(), user=user_info, course=disciplina.course, period=PERIODO_ATUAL).save()
#                            else:
#                                logging.info("        [INFO] O ALUNO JA ESTAVA CADASTRADO NO CURSO")
#
#                            #Associando o aluno à instituição de ensino
#                            queryset = RelUserInstitution.objects.filter(role=UserInstitutionRole.objects.student_role(), user=user_info, institution=disciplina.course.institution, period=PERIODO_ATUAL)
#                            if not queryset.exists():
#                                logging.info("        [INFO] CADASTRANO O ALUNO NA INSTITUICAO: %s" % disciplina.course.institution.name)
#                                RelUserInstitution(role=UserInstitutionRole.objects.student_role(), user=user_info, institution=disciplina.course.institution, period=PERIODO_ATUAL).save()
#                            else:
#                                logging.info("        [INFO] O ALUNO JA ESTAVA CADASTRADO NA ISTITUICAO")
#                        except Exception, e:
#                            logging.exception(e)
#                            logging.error("[importar_alunos] - Nao foi possivel localizar a disciplina %s" % id_disc)
#
#                    #Para cada uma das instituicoes afetadas
#                    for inst in institutions:
#                        rebuild_caches_institution(inst) #Reconstroi a sua cache
#                    #Para cada um dos cursos afetados
#                    for course in courses:
#                        rebuild_caches_course(course)
#                except:
#                    #Caso o aluno não tenha ainda se inscrito no portal
#                    cria_pre_inscricao = True
            else:
                cria_pre_inscricao = True
                
            if cria_pre_inscricao:
                PreInscricao(matricula=matricula, nome=nome, cpf=cpf, sexo=sexo, email=email, data_nasc=data_nasc, rua=rua, numero=numero, bairro=bairro, cidade=cidade, estado=estado, senha=senha, disciplinas=disciplinas).save()

        return HttpResponse('Funcionou !')

    return direct_to_template(request, 'importar_alunos.html')

@login_required
def limpar(request):
    PreInscricao.objects.all().delete()
    RelUserDiscipline.objects.all().delete()
    RelDisciplineOwner.objects.all().delete()
    DisciplineMetadata.objects.all().delete()
    Discipline.objects.all().delete()
    RelUserCourse.objects.all().delete()
    RelUserInstitution.objects.all().delete()
    return HttpResponse('Funcionou !')

@login_required
def atualiza_informacao_periodo(request, periodo):
    for o in DisciplineMetadata.objects.all():
        o.periodo = periodo
        o.save()
    for o in Discipline.objects.all():
        o.period = periodo
        o.save()
    for o in RelUserCourse.objects.all():
        o.period = periodo
        o.save()
    for o in RelUserInstitution.objects.all():
        o.period = periodo
        o.save()
    for o in RelUserDiscipline.objects.all():
        o.period = periodo
        o.save()
    return HttpResponse('Funcionou !')
