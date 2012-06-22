# -*- coding: utf-8 -*-
__author__ = 'brunocatao'

from django.utils.translation import ugettext as _

STATES_CHOICES = (
    ('', u'Selecione um estado'),
    ('AC', u'Acre'),
    ('AL', u'Alagoas'),
    ('AP', u'Amapá'),
    ('AM', u'Amazonas'),
    ('BA', u'Bahia'),
    ('CE', u'Ceará'),
    ('DF', u'Distrito Federal'),
    ('ES', u'Espírito Santo'),
    ('GO', u'Goiás'),
    ('MA', u'Maranhão'),
    ('MT', u'Mato Grosso'),
    ('MS', u'Mato Grosso do Sul'),
    ('MG', u'Minas Gerais'),
    ('PA', u'Pará'),
    ('PB', u'Paraíba'),
    ('PR', u'Paraná'),
    ('PE', u'Pernambuco'),
    ('PI', u'Piauí'),
    ('RR', u'Roraima'),
    ('RO', u'Rondônia'),
    ('RJ', u'Rio de Janeiro'),
    ('RN', u'Rio Grande do Norte'),
    ('RS', u'Rio Grande do Sul'),
    ('SC', u'Santa Catarina'),
    ('SP', u'São Paulo'),
    ('SE', u'Sergipe'),
    ('TO', u'Tocantins'),
)

MODERATE_REGISTRATION = 0
EVERYONE_CAN_REGISTER = 2
PUBLIC_ACCESS = 0

REGISTRATION_TYPE_CHOICES = (
    (0, _('Moderate registration')),
    (1, _('Users must be invited')),
    (2, _('Everyone can register')),
)

ACCESS_TYPE_CHOICES = (
    (0, _('Public access')),
    (1, _('Private access')),
)

