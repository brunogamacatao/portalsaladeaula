# -*- coding: utf-8 -*-
import logging
from operator import attrgetter
from django.db import models
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from djangotoolbox.fields import BlobField, SetField

from django.template import Context
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives

from google.appengine.api import images

from portal.fields import AutoSlugField
from portal.constants import STATES_CHOICES, REGISTRATION_TYPE_CHOICES, ACCESS_TYPE_CHOICES, MODERATE_REGISTRATION, PUBLIC_ACCESS
from portal.utils import split_string, formata_hora
from portal.updates.models import Update
import datetime

from settings import PERIODO_ATUAL

class Indexable(models.Model):
    index          = SetField(blank=False)
    messages_cache = models.TextField(blank=True, null=True)
    updates_cache  = models.TextField(blank=True, null=True)
    teachers_cache = models.TextField(blank=True, null=True)
    students_cache = models.TextField(blank=True, null=True)

    def notify_upload(self, user, uploaded_file):
        return None

    def notify_new_student(self, user, student):
        return None

    def notify_new_teacher(self, user, teacher):
        return None

    def notify_comment(self, user, comment):
        return None

    def get_update_list(self):
        return None

    class Meta:
        abstract = True

class Picture(models.Model):
    picture  = BlobField(blank=False)
    filename = models.CharField(blank=False, max_length=200)
    width    = models.IntegerField(blank=True)
    height   = models.IntegerField(blank=True)
    format   = models.CharField(blank=True, max_length=10)
    parent   = models.ForeignKey('self', blank=True, null=True, related_name='thumb_set')
    '''
    The felds below are just for thumbnails. They store the requested width and
    height values as they can change according to the image's aspect ratio.
    '''
    intended_width  = models.IntegerField(blank=True, null=True)
    intended_height = models.IntegerField(blank=True, null=True)

    @classmethod
    def create_thumbnail(cls, parent, width, height):
        img = images.Image(parent.picture)
        img.resize(width=width, height=height)
        img.im_feeling_lucky()

        thumb = Picture()
        thumb.picture         = img.execute_transforms(output_encoding=images.JPEG)
        thumb.filename        = parent.filename.split('.')[0] + '_thumb.jpg'
        thumb.parent          = parent
        thumb.intended_width  = width
        thumb.intended_height = height
        thumb.save()

        return thumb

    @classmethod
    def get_thumbnail(cls, picture, width, height):
        if picture.thumb_set.filter(intended_width=width, intended_height=height).exists():
            return picture.thumb_set.filter(intended_width=width, intended_height=height)[0]
        return cls.create_thumbnail(picture, width, height)

#Here we automatically fill the width, height and format fields of a picture.
def fill_picture_fields(sender, instance, **kw):
    image = images.Image(instance.picture)
    instance.width  = image.width
    instance.height = image.height
    instance.format = instance.filename.split('.')[-1]

models.signals.pre_save.connect(fill_picture_fields, sender=Picture)

class UserInfo(Indexable):
    name           = models.CharField(_('Name'), blank=False, max_length=100)
    picture        = models.ForeignKey(Picture, blank=True, null=True)
    city           = models.CharField(_('City'), blank=False, max_length=100)
    province       = models.CharField(_('State or Province'), blank=False, max_length=2, choices=STATES_CHOICES)
    email          = models.EmailField(_('Email'), blank=False)
    user           = models.ForeignKey(User, unique=True)
    show_help_text = models.NullBooleanField(blank=True, null=True)
    is_teacher     = models.NullBooleanField(blank=True, null=True)
    birth_date     = models.DateField(blank=True, null=True)
    schedule_cache = models.TextField(blank=True, null=True)

    def get_absolute_url(self):
        return reverse('portal.accounts.views.user_info', args=[self.user.id],)

    def get_disciplines_studies(self):
        student_role  = UserDisciplineRole.objects.student_role()
        queryset = self.reluserdiscipline_set.filter(role=student_role, user=self, period=PERIODO_ATUAL)
        if queryset.exists():
            disciplines = []
            for rel in queryset.all():
                disciplines.append(rel.discipline)
            return disciplines
        return []

    def get_disciplines_teaches(self):
        teacher_role  = UserDisciplineRole.objects.teacher_role()
        queryset = self.reluserdiscipline_set.filter(role=teacher_role, user=self, period=PERIODO_ATUAL)
        if queryset.exists():
            disciplines = []
            for rel in queryset.all():
                disciplines.append(rel.discipline)
            return disciplines
        return []

    def get_courses_studies(self):
        student_role  = UserCourseRole.objects.student_role()
        queryset = self.relusercourse_set.filter(role=student_role, user=self, period=PERIODO_ATUAL)
        if queryset.exists():
            courses = []
            for rel in queryset.all():
                courses.append(rel.course)
            return courses
        return []

    def get_courses_teaches(self):
        teacher_role  = UserCourseRole.objects.teacher_role()
        queryset = self.relusercourse_set.filter(role=teacher_role, user=self, period=PERIODO_ATUAL)
        if queryset.exists():
            courses = []
            for rel in queryset.all():
                courses.append(rel.course)
            return courses
        return []

    def get_institutions_studies(self):
        student_role  = UserInstitutionRole.objects.student_role()
        queryset = self.reluserinstitution_set.filter(role=student_role, user=self, period=PERIODO_ATUAL)
        if queryset.exists():
            institutions = []
            for rel in queryset.all():
                institutions.append(rel.institution)
            return institutions
        return []

    def get_institutions_teaches(self):
        teacher_role  = UserInstitutionRole.objects.teacher_role()
        queryset = self.reluserinstitution_set.filter(role=teacher_role, user=self, period=PERIODO_ATUAL)
        if queryset.exists():
            institutions = []
            for rel in queryset.all():
                institutions.append(rel.institution)
            return institutions
        return []

    def get_update_list(self):
        updates = []

        if self.is_teacher:
            for discipline in self.get_disciplines_teaches():
                for update in Update.objects.for_model(discipline).order_by('-date_published')[:5]:
                    updates.append(update)
            for course in self.get_courses_teaches():
                for update in Update.objects.for_model(course).order_by('-date_published')[:5]:
                    updates.append(update)
            for institution in self.get_institutions_teaches():
                for update in Update.objects.for_model(institution).order_by('-date_published')[:5]:
                    updates.append(update)
        else:
            for discipline in self.get_disciplines_studies():
                for update in Update.objects.for_model(discipline).order_by('-date_published')[:5]:
                    updates.append(update)
            for course in self.get_courses_studies():
                for update in Update.objects.for_model(course).order_by('-date_published')[:5]:
                    updates.append(update)
            for institution in self.get_institutions_studies():
                for update in Update.objects.for_model(institution).order_by('-date_published')[:5]:
                    updates.append(update)

        return sorted(updates, key=attrgetter('date_published'), reverse=True)[:5]

    class Meta:
        verbose_name        = _('User Information')
        verbose_name_plural = _('User Information')

    def __unicode__(self):
        return self.name

def fill_user_index(sender, instance, **kw):
    index = []
    if instance.name:
        index += split_string(instance.name)
    instance.index = index

models.signals.pre_save.connect(fill_user_index, sender=UserInfo)

class PreInscricao(models.Model):
    matricula   = models.CharField(blank=False, max_length=50)
    nome        = models.CharField(blank=False, max_length=100)
    cpf         = models.CharField(blank=False, max_length=50)
    sexo        = models.CharField(blank=False, max_length=2)
    email       = models.EmailField(blank=True, max_length=200)
    data_nasc   = models.DateField(blank=True)
    rua         = models.CharField(blank=False, max_length=200)
    numero      = models.CharField(blank=False, max_length=10)
    bairro      = models.CharField(blank=False, max_length=100)
    cidade      = models.CharField(blank=False, max_length=100)
    estado      = models.CharField(blank=False, max_length=2)
    senha       = models.CharField(blank=False, max_length=50)
    disciplinas = SetField(blank=True, null=True)
    user_info   = models.ForeignKey(UserInfo, blank=True, null=True)

class Address(models.Model):
    address      = models.CharField(_('Address'), blank=False, max_length=200)
    number       = models.CharField(_('Number'), blank=False, max_length=10)
    neighborhood = models.CharField(_('Neighborhood'), blank=False, max_length=100)
    city         = models.CharField(_('City'), blank=False, max_length=100)
    province     = models.CharField(_('State or Province'), blank=False, max_length=2, choices=STATES_CHOICES)

    def get_index(self):
        index = []

        if self.address:
            index += split_string(self.address)
        if self.neighborhood:
            index += split_string(self.neighborhood)
        if self.city:
            index += split_string(self.city)
        
        return set(index)

    class Meta:
        verbose_name        = _('Address')
        verbose_name_plural = _('Addresses')

class Institution(Indexable):
    name        = models.CharField(_('Name'), blank=False, max_length=100)
    slug        = AutoSlugField(prepopulate_from=('acronym',), unique=True, blank=True, max_length=100)
    acronym     = models.CharField(_('Acronym'), blank=True, null=True, max_length=100)
    picture     = models.ForeignKey(Picture, blank=True, null=True)
    address     = models.ForeignKey(Address, blank=True, null=True)
    description = models.TextField(_('Description'))
    homepage    = models.URLField(_('Homepage'), blank=True, null=True)
    feed_url    = models.CharField(_('News Feed URL'), blank=True, null=True, max_length=512)
    twitter_id  = models.CharField(_('Twitter ID'), blank=True, null=True, max_length=100)
    '''
    ATENÇÃO !!!
    Pelo jeito, Django-nonrel não suporta campos ManyToMany
    '''

    '''
    Hora do brainstorm:
    Que outros campos devem vir aqui ?

    descrição ?
    endereço ?
    telefones ?
    página na internet ?

    Outras informações, tais como personalização, feeds e instituições parceiras, deverão ser
    adicionadas como módulos extra.

    Módulos extra:
    1. Personalização:
        a) Logomarca;
        b) Imagens de fundo (topo, meio, rodapé);
        c) Esquema de cores;
    2. Feeds (rss/atom/twitter) - Caso tenha um twitter, seria legal colocar um siga-nos;
    3. Instituições parceiras (do próprio portal);
    4. Links (com ou sem imagem)
    5. Vestibular
    6. Eventos
    7. Biblioteca (integrar com o Pergamum)
    8. IM (Google Talk Like)
    9. Álbum de fotos
    10. Arquivos (área de upload/download)
    11. Comentários
    '''

    class Meta:
        verbose_name        = _('Institution')
        verbose_name_plural = _('Institutions')

    def get_students(self):
        student_role  = UserInstitutionRole.objects.student_role()
        queryset = self.reluserinstitution_set.filter(role=student_role, institution=self)
        if queryset.exists():
            students = []
            for rel in queryset.all():
                try:
                    students.append(rel.user)
                except:
                    logging.error("[get_students] Not able to find an user for RelUserInstitution %s" % rel.id)
            return students
        return None

    def get_student_count(self):
        student_role  = UserInstitutionRole.objects.student_role()
        return self.reluserinstitution_set.filter(role=student_role, institution=self).count()

    def get_teachers(self):
        teacher_role  = UserInstitutionRole.objects.teacher_role()

        queryset = self.reluserinstitution_set.filter(role=teacher_role, institution=self)
        if queryset.exists():
            teachers = []
            for rel in queryset.all():
                try:
                    teachers.append(rel.user)
                except:
                    logging.error("[get_teachers] Not able to find an user for RelUserInstitution %s" % rel.id)
            return teachers
        return None

    def get_update_list(self):
        updates = []
        for update in Update.objects.for_model(self).order_by('-date_published')[:5]:
            updates.append(update)
        for course in self.course_set.all():
            for update in Update.objects.for_model(course).order_by('-date_published')[:5]:
                updates.append(update)
            for discipline in course.discipline_set.all():
                for update in Update.objects.for_model(discipline).order_by('-date_published')[:5]:
                    updates.append(update)

        return sorted(updates, key=attrgetter('date_published'), reverse=True)[:5]

    def get_class_name(self):
        return 'portal.models.Institution'

    def get_absolute_url(self):
        return reverse('portal.institutions.views.detail', args=[self.slug,])

    def __unicode__(self):
        return self.name

#If the acronym field is not filled, it will receive the value from name field.
def fill_acronym(sender, instance, **kw):
    if not instance.acronym or instance.acronym == '':
        instance.acronym = instance.name

models.signals.pre_save.connect(fill_acronym, sender=Institution)

def fill_institution_index(sender, instance, **kw):
    index = []
    if instance.name:
        index += split_string(instance.name)
    if instance.acronym:
        index += split_string(instance.acronym)
    if instance.description:
        index += split_string(instance.description)
    if instance.address:
        index += instance.address.get_index()

    instance.index = index

models.signals.pre_save.connect(fill_institution_index, sender=Institution)

class InstitutionUpdateCache(models.Model):
    text           = models.CharField(blank=False, max_length=100)
    link           = models.CharField(blank=False, max_length=512)
    date_published = models.DateTimeField(default=datetime.datetime.now)
    author         = models.ForeignKey(User, blank=False)
    institution    = models.ForeignKey(Institution, blank=True, null=True)

class RelInstitutionOwner(models.Model):
    owner       = models.ForeignKey(UserInfo, blank=True, null=True, related_name='owner_set')
    institution = models.ForeignKey(Institution, blank=True, null=True, related_name='owner_set')

class PhoneNumber(models.Model):
    region_code = models.CharField(_('Region Code'), blank=False, max_length=5)
    telephone   = models.CharField(_('Telephone'), blank=False, max_length=20)
    description = models.CharField(_('Description'), blank=False, max_length=50)
    institution = models.ForeignKey(Institution, blank=False)
    
class Course(Indexable):
    name        = models.CharField(_('Name'), blank=False, max_length=100)
    slug        = AutoSlugField(prepopulate_from=('acronym',), parent_name='institution', unique=True, blank=True, max_length=100)
    acronym     = models.CharField(_('Acronym'), blank=True, null=True, max_length=100)
    picture     = models.ForeignKey(Picture, blank=True, null=True)
    description = models.TextField(_('Description'))
    feed_url    = models.CharField(_('News Feed URL'), blank=True, null=True, max_length=512)
    twitter_id  = models.CharField(_('Twitter ID'), blank=True, null=True, max_length=100)
    institution = models.ForeignKey(Institution, blank=False)

    def get_students(self):
        student_role  = UserCourseRole.objects.student_role()
        queryset = self.relusercourse_set.filter(role=student_role, course=self)
        if queryset.exists():
            students = []
            for rel in queryset.all():
                try:
                    students.append(rel.user)
                except:
                    logging.error("[get_students] Not able to find an user for RelUserInstitution %s" % rel.id)
            return students
        return None

    def get_teachers(self):
        teacher_role  = UserCourseRole.objects.teacher_role()
        queryset = self.relusercourse_set.filter(role=teacher_role, course=self)
        if queryset.exists():
            teachers = []
            for rel in queryset.all():
                try:
                    teachers.append(rel.user)
                except:
                    logging.error("[get_teachers] Not able to find an user for RelUserInstitution %s" % rel.id)
            return teachers
        return None

    class Meta:
        verbose_name        = _('Course')
        verbose_name_plural = _('Courses')

    def get_class_name(self):
        return 'portal.models.Course'

    def get_absolute_url(self):
        return reverse('portal.courses.views.detail', args=[self.institution.slug, self.slug,])

    def get_update_list(self):
        updates = []
        for update in Update.objects.for_model(self).order_by('-date_published')[:5]:
            updates.append(update)
        for discipline in self.discipline_set.all():
            for update in Update.objects.for_model(discipline).order_by('-date_published')[:5]:
                updates.append(update)
        return sorted(updates, key=attrgetter('date_published'), reverse=True)[:5]

    def __unicode__(self):
        return self.name

models.signals.pre_save.connect(fill_acronym, sender=Course)

def fill_course_index(sender, instance, **kw):
    index = []
    if instance.name:
        index += split_string(instance.name)
    if instance.acronym:
        index += split_string(instance.acronym)
    if instance.description:
        index += split_string(instance.description)
    if instance.institution:
        index += instance.institution.index

    instance.index = index

models.signals.pre_save.connect(fill_course_index, sender=Course)

class RelCourseOwner(models.Model):
    owner  = models.ForeignKey(UserInfo, blank=True, null=True, related_name='course_owner_set')
    course = models.ForeignKey(Course, blank=True, null=True, related_name='course_owner_set')

class Discipline(Indexable):
    name              = models.CharField(_('Name'), blank=False, max_length=100)
    slug              = AutoSlugField(prepopulate_from=('acronym',), parent_name='course', unique=True, blank=True, max_length=100)
    acronym           = models.CharField(_('Acronym'), blank=True, null=True, max_length=100)
    picture           = models.ForeignKey(Picture, blank=True, null=True)
    description       = models.TextField(_('Description'))
    feed_url          = models.CharField(_('News Feed URL'), blank=True, null=True, max_length=512)
    twitter_id        = models.CharField(_('Twitter ID'), blank=True, null=True, max_length=100)
    course            = models.ForeignKey(Course, blank=False)
    registration_type = models.IntegerField(_('Registration type'), blank=False,
                                            default=MODERATE_REGISTRATION,
                                            choices=REGISTRATION_TYPE_CHOICES)
    access_type       = models.IntegerField(_('Access type'), blank=False,
                                            default=PUBLIC_ACCESS,
                                            choices=ACCESS_TYPE_CHOICES)
    period            = models.CharField(_('Period'), blank=True, null=True, max_length=5)

    class Meta:
        verbose_name        = _('Discipline')
        verbose_name_plural = _('Disciplines')

    def get_students(self):
        student_role  = UserDisciplineRole.objects.student_role()
        queryset = self.reluserdiscipline_set.filter(role=student_role, discipline=self)
        if queryset.exists():
            students = []
            for rel in queryset.all():
                try:
                    students.append(rel.user)
                except:
                    logging.error("[get_students] Not able to find an user for RelUserInstitution %s" % rel.id)
            return students
        return None

    def get_teachers(self):
        teacher_role  = UserDisciplineRole.objects.teacher_role()
        queryset = self.reluserdiscipline_set.filter(role=teacher_role, discipline=self)
        if queryset.exists():
            teachers = []
            for rel in queryset.all():
                try:
                    teachers.append(rel.user)
                except:
                    logging.error("[get_teachers] Not able to find an user for RelUserInstitution %s" % rel.id)
            return teachers
        return None

    def get_horario(self):
        not_empty = lambda x: (x and len(x.lstrip()) > 0 and x != 'null') or False

        if self.disciplinemetadata_set.exists():
            m_data = self.disciplinemetadata_set.all()[0]
            horario = u''
            if not_empty(m_data.segunda):
                horario += u'Segunda-feira '  + unicode(formata_hora(m_data.segunda), 'utf-8')
            if not_empty(m_data.terca):
                horario += u'\nTerça-feira '  + unicode(formata_hora(m_data.terca),   'utf-8')
            if not_empty(m_data.quarta):
                horario += u'\nQuarta-feira ' + unicode(formata_hora(m_data.quarta),  'utf-8')
            if not_empty(m_data.quinta):
                horario += u'\nQuinta-feira ' + unicode(formata_hora(m_data.quinta),  'utf-8')
            if not_empty(m_data.sexta):
                horario += u'\nSexta-feira '  + unicode(formata_hora(m_data.sexta),   'utf-8')
            if not_empty(m_data.sabado):
                horario += u'\nSábado '       + unicode(formata_hora(m_data.sabado),  'utf-8')
            return horario
        return None

    def get_sala(self):
        if self.disciplinemetadata_set.exists():
            return self.disciplinemetadata_set.all()[0].sala
        return None

    def get_class_name(self):
        return 'portal.models.Discipline'

    def get_absolute_url(self):
        return reverse('portal.disciplines.views.detail', args=[self.course.institution.slug, self.course.slug, self.slug,])

    def get_update_list(self):
        return Update.objects.for_model(self).order_by('-date_published')[:5]

    def notify_upload(self, user, uploaded_file):
        text = u'%s postou um novo material didático <a href="%s">%s</a>' % (user.get_profile().name, self.get_absolute_url(), uploaded_file.description, )
        link = self.get_absolute_url()

        update = Update.createUpdate(user, text, link, self)

        ctx = {
            'mensagem': update.text,
            'link': 'http://www.portalsaladeaula.com%s' % update.link,
        }

        subject      = 'Novo Material Didático'
        from_email   = 'Portal Sala de Aula <gerencia@portalsaladeaula.com>'
        text_content = get_template('emails/update.txt').render(Context(ctx))
        html_content = get_template('emails/update.html').render(Context(ctx))

        if self.get_students():
            for student in self.get_students():
                msg = EmailMultiAlternatives(subject, text_content, from_email, [student.email,])
                msg.attach_alternative(html_content, "text/html")

                try:
                    msg.send()
                except:
                    logging.error('Não foi possível enviar o email')
        if self.get_teachers():
            for teacher in self.get_teachers():
                if teacher != uploaded_file.user:
                    msg = EmailMultiAlternatives(subject, text_content, from_email, [teacher.email,])
                    msg.attach_alternative(html_content, "text/html")

                    try:
                        msg.send()
                    except:
                        logging.error('Não foi possível enviar o email')


    def __unicode__(self):
        return self.name

models.signals.pre_save.connect(fill_acronym, sender=Discipline)

def fill_discipline_index(sender, instance, **kw):
    index = []
    if instance.name:
        index += split_string(instance.name)
    if instance.acronym:
        index += split_string(instance.acronym)
    if instance.description:
        index += split_string(instance.description)
    if instance.course:
        index += instance.course.index

    instance.index = index

models.signals.pre_save.connect(fill_discipline_index, sender=Discipline)

class DisciplineMetadata(models.Model):
    cod_turma  = models.CharField(blank=False, max_length=50)
    periodo    = models.CharField(blank=False, max_length=50)
    senha      = models.CharField(blank=False, max_length=50)
    discipline = models.ForeignKey(Discipline, blank=True, null=True)
    segunda    = models.CharField(blank=True, null=True, max_length=5)
    terca      = models.CharField(blank=True, null=True, max_length=5)
    quarta     = models.CharField(blank=True, null=True, max_length=5)
    quinta     = models.CharField(blank=True, null=True, max_length=5)
    sexta      = models.CharField(blank=True, null=True, max_length=5)
    sabado     = models.CharField(blank=True, null=True, max_length=5)
    sala       = models.CharField(blank=True, null=True, max_length=5)

class RelDisciplineOwner(models.Model):
    owner      = models.ForeignKey(UserInfo, blank=True, null=True, related_name='discipline_owner_set')
    discipline = models.ForeignKey(Discipline, blank=True, null=True, related_name='discipline_owner_set')

#To speedup the system, these roles will be queried just once
INSTITUTION_STUDENT_ROLE     = None
INSTITUTION_TEACHER_ROLE     = None
INSTITUTION_COORDINATOR_ROLE = None
INSTITUTION_MANAGER_ROLE     = None

class ManagerUserInstitutionRole(models.Manager):
    def student_role(self):
        global INSTITUTION_STUDENT_ROLE
        if INSTITUTION_STUDENT_ROLE:
            return INSTITUTION_STUDENT_ROLE
        queryset = self.filter(slug='student')
        if queryset.exists():
            INSTITUTION_STUDENT_ROLE = queryset.all()[0]
            return INSTITUTION_STUDENT_ROLE
        INSTITUTION_STUDENT_ROLE = UserInstitutionRole(name='Student', slug='student')
        INSTITUTION_STUDENT_ROLE.save()
        return INSTITUTION_STUDENT_ROLE

    def teacher_role(self):
        global INSTITUTION_TEACHER_ROLE
        if INSTITUTION_TEACHER_ROLE:
            return INSTITUTION_TEACHER_ROLE
        queryset = self.filter(slug='teacher')
        if queryset.exists():
            INSTITUTION_TEACHER_ROLE = queryset.all()[0]
            return INSTITUTION_TEACHER_ROLE
        INSTITUTION_TEACHER_ROLE = UserInstitutionRole(name='Teacher', slug='teacher')
        INSTITUTION_TEACHER_ROLE.save()
        return INSTITUTION_TEACHER_ROLE

    def coordinator_role(self):
        global INSTITUTION_COORDINATOR_ROLE
        if INSTITUTION_COORDINATOR_ROLE:
            return INSTITUTION_COORDINATOR_ROLE
        queryset = self.filter(slug='coordinator')
        if queryset.exists():
            INSTITUTION_COORDINATOR_ROLE = queryset.all()[0]
            return INSTITUTION_COORDINATOR_ROLE
        INSTITUTION_COORDINATOR_ROLE = UserInstitutionRole(name='Coordinator', slug='coordinator')
        INSTITUTION_COORDINATOR_ROLE.save()
        return INSTITUTION_COORDINATOR_ROLE

    def manager_role(self):
        global INSTITUTION_MANAGER_ROLE
        if INSTITUTION_MANAGER_ROLE:
            return INSTITUTION_MANAGER_ROLE
        queryset = self.filter(slug='manager')
        if queryset.exists():
            INSTITUTION_MANAGER_ROLE = queryset.all()[0]
            return INSTITUTION_MANAGER_ROLE
        INSTITUTION_MANAGER_ROLE = UserInstitutionRole(name='Manager', slug='manager')
        INSTITUTION_MANAGER_ROLE.save()
        return INSTITUTION_MANAGER_ROLE

class UserInstitutionRole(models.Model):
    name = models.CharField(_('Role Name'), blank=False, max_length=100)
    slug = AutoSlugField(prepopulate_from=('name',), unique=True, blank=True, max_length=100)

    objects = ManagerUserInstitutionRole()

    class Meta:
        verbose_name        = _('Role for User/Institution Relationship')
        verbose_name_plural = _('Roles for User/Institution Relationship')

    def __unicode__(self):
        return self.name

class RelUserInstitution(models.Model):
    user        = models.ForeignKey(UserInfo, blank=False)
    institution = models.ForeignKey(Institution, blank=False)
    role        = models.ForeignKey(UserInstitutionRole, blank=False)
    period      = models.CharField(_('Period'), blank=True, null=True, max_length=5)

#To speedup the system, these roles will be queried just once
COURSE_STUDENT_ROLE     = None
COURSE_TEACHER_ROLE     = None
COURSE_COORDINATOR_ROLE = None
COURSE_SECRETARY_ROLE   = None

class ManagerUserCourseRole(models.Manager):
    def student_role(self):
        global COURSE_STUDENT_ROLE
        if COURSE_STUDENT_ROLE:
            return COURSE_STUDENT_ROLE
        queryset = self.filter(slug='student')
        if queryset.exists():
            COURSE_STUDENT_ROLE = queryset.all()[0]
            return COURSE_STUDENT_ROLE
        COURSE_STUDENT_ROLE = UserCourseRole(name='Student', slug='student')
        COURSE_STUDENT_ROLE.save()
        return COURSE_STUDENT_ROLE

    def teacher_role(self):
        global COURSE_TEACHER_ROLE
        if COURSE_TEACHER_ROLE:
            return COURSE_TEACHER_ROLE
        queryset = self.filter(slug='teacher')
        if queryset.exists():
            COURSE_TEACHER_ROLE = queryset.all()[0]
            return COURSE_TEACHER_ROLE
        COURSE_TEACHER_ROLE = UserCourseRole(name='Teacher', slug='teacher')
        COURSE_TEACHER_ROLE.save()
        return COURSE_TEACHER_ROLE

    def coordinator_role(self):
        global COURSE_COORDINATOR_ROLE
        if COURSE_COORDINATOR_ROLE:
            return COURSE_COORDINATOR_ROLE
        queryset = self.filter(slug='coordinator')
        if queryset.exists():
            COURSE_COORDINATOR_ROLE = queryset.all()[0]
            return COURSE_COORDINATOR_ROLE
        COURSE_COORDINATOR_ROLE = UserCourseRole(name='Coordinator', slug='coordinator')
        COURSE_COORDINATOR_ROLE.save()
        return COURSE_COORDINATOR_ROLE

    def secretary_role(self):
        global COURSE_SECRETARY_ROLE
        if COURSE_SECRETARY_ROLE:
            return COURSE_SECRETARY_ROLE
        queryset = self.filter(slug='secretary')
        if queryset.exists():
            COURSE_SECRETARY_ROLE = queryset.all()[0]
            return COURSE_SECRETARY_ROLE
        COURSE_SECRETARY_ROLE = UserCourseRole(name='Secretary', slug='secretary')
        COURSE_SECRETARY_ROLE.save()
        return COURSE_SECRETARY_ROLE

class UserCourseRole(models.Model):
    name = models.CharField(_('Role Name'), blank=False, max_length=100)
    slug = AutoSlugField(prepopulate_from=('name',), unique=True, blank=True, max_length=100)

    objects = ManagerUserCourseRole()

    class Meta:
        verbose_name        = _('Role for User/Course Relationship')
        verbose_name_plural = _('Roles for User/Course Relationship')

    def __unicode__(self):
        return self.name

class RelUserCourse(models.Model):
    user   = models.ForeignKey(UserInfo, blank=False)
    course = models.ForeignKey(Course, blank=False)
    role   = models.ForeignKey(UserCourseRole, blank=False)
    period = models.CharField(_('Period'), blank=True, null=True, max_length=5)

#To speedup the system, these roles will be queried just once
DISCIPLINE_STUDENT_ROLE = None
DISCIPLINE_TEACHER_ROLE = None

class ManagerUserDisciplineRole(models.Manager):
    def student_role(self):
        global DISCIPLINE_STUDENT_ROLE
        if DISCIPLINE_STUDENT_ROLE:
            return DISCIPLINE_STUDENT_ROLE
        queryset = self.filter(slug='student')
        if queryset.exists():
            DISCIPLINE_STUDENT_ROLE = queryset.all()[0]
            return DISCIPLINE_STUDENT_ROLE
        DISCIPLINE_STUDENT_ROLE = UserDisciplineRole(name='Student', slug='student')
        DISCIPLINE_STUDENT_ROLE.save()
        return DISCIPLINE_STUDENT_ROLE

    def teacher_role(self):
        global DISCIPLINE_TEACHER_ROLE
        if DISCIPLINE_TEACHER_ROLE:
            return DISCIPLINE_TEACHER_ROLE
        queryset = self.filter(slug='teacher')
        if queryset.exists():
            DISCIPLINE_TEACHER_ROLE = queryset.all()[0]
            return DISCIPLINE_TEACHER_ROLE
        DISCIPLINE_TEACHER_ROLE = UserDisciplineRole(name='Teacher', slug='teacher')
        DISCIPLINE_TEACHER_ROLE.save()
        return DISCIPLINE_TEACHER_ROLE

class UserDisciplineRole(models.Model):
    name = models.CharField(_('Role Name'), blank=False, max_length=100)
    slug = AutoSlugField(prepopulate_from=('name',), unique=True, blank=True, max_length=100)

    objects = ManagerUserDisciplineRole()

    class Meta:
        verbose_name        = _('Role for User/Discipline Relationship')
        verbose_name_plural = _('Roles for User/Discipline Relationship')

    def __unicode__(self):
        return self.name

class RelUserDiscipline(models.Model):
    user       = models.ForeignKey(UserInfo, blank=False)
    discipline = models.ForeignKey(Discipline, blank=False)
    role       = models.ForeignKey(UserDisciplineRole, blank=False)
    period     = models.CharField(_('Period'), blank=True, null=True, max_length=5)

def invalidate_reluserdiscipline_cache(sender, instance, **kw):
    if instance.user:
        instance.user.schedule_cache = None
        instance.user.save()

models.signals.pre_save.connect(invalidate_reluserdiscipline_cache, sender=RelUserDiscipline)
