# -*- coding: utf-8 -*-
import re
import datetime


def extract_html_text(html):
    return re.sub(r'<[^>]+>', '', html)

def tira_pontuacao(string):
    string = re.sub(r'[^\w]', '', string)
    string = re.sub(r'[_-]', '', string)
    return string

def tira_acentos(string):
    string = string.lower()
    string = re.sub(u'[áàäãâ]', u'a', string)
    string = re.sub(u'[éëê]',   u'e', string)
    string = re.sub(u'[íï]',    u'i', string)
    string = re.sub(u'[óöõô]',  u'o', string)
    string = re.sub(u'[úü]',    u'u', string)
    return string

def split_string(phrase):
    if phrase:
        phrase = extract_html_text(phrase)
        return [tira_pontuacao(tira_acentos(word)) for word in phrase.split()]
    return []

def get_hora_inicio_fim(string):
    duracao = int(string[4])
    horas   = int(string[:2])
    minutos = int(string[2:4])

    intervalo = (datetime.time(20, 10), datetime.time(20, 20))

    hora = datetime.datetime(1, 1, 1, horas, minutos)
    hora_fim = hora + datetime.timedelta(minutes=50 * duracao)

    if hora.time() < intervalo[0] and hora_fim.time() > intervalo[1]:
        hora_fim += datetime.timedelta(minutes=10) #Adicionar os dez minutos do intervalo

    return (hora.time(), hora_fim.time(), )


def formata_hora(string):
    horario = get_hora_inicio_fim(string)
    return 'das %02d:%02dhrs até as %02d:%02dhrs' % (horario[0].hour, horario[0].minute, horario[1].hour, horario[1].minute,)

def get_class(kls):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m

def get_mime_type(filename):
    extension = filename.split('.')[-1]

    if not extension:
        return 'application/x-download'

    content_types = {
        "doc": "application/msword",
        "dot": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "dotx": "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
        "docm": "application/vnd.ms-word.document.macroEnabled.12",
        "dotm": "application/vnd.ms-word.template.macroEnabled.12",
        "xls": "application/vnd.ms-excel",
        "xlt": "application/vnd.ms-excel",
        "xla": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xltx": "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
        "xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
        "xltm": "application/vnd.ms-excel.template.macroEnabled.12",
        "xlam": "application/vnd.ms-excel.addin.macroEnabled.12",
        "xlsb": "application/vnd.ms-excel.sheet.binary.macroEnabled.12",
        "ppt": "application/vnd.ms-powerpoint",
        "pot": "application/vnd.ms-powerpoint",
        "pps": "application/vnd.ms-powerpoint",
        "ppa": "application/vnd.ms-powerpoint",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "potx": "application/vnd.openxmlformats-officedocument.presentationml.template",
        "ppsx": "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
        "ppam": "application/vnd.ms-powerpoint.addin.macroEnabled.12",
        "pptm": "application/vnd.ms-powerpoint.presentation.macroEnabled.12",
        "potm": "application/vnd.ms-powerpoint.template.macroEnabled.12",
        "ppsm": "application/vnd.ms-powerpoint.slideshow.macroEnabled.12",
    }

    extension = extension.lower()
    mime_type = 'application/%s' % extension
    if content_types.has_key(extension):
        mime_type = content_types[extension]

    return mime_type