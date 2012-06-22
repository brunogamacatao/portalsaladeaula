# -*- coding: utf-8 -*-
__author__ = 'brunocatao'

import datetime
from django import template

register = template.Library()

def break_text(text, nchars=80):
    words = []
    count = 0
    
    for word in text.split(' '):
        while len(word) + count > nchars:
            words.append(word[:nchars])
            word = word[nchars:]
        if len(word) > 0:
            words.append(word)

    return ' '.join(words)


register.filter('break_text', break_text)

def sizify(value):
    """
    Simple kb/mb/gb size snippet for templates:

    {{ product.file.size|sizify }}
    """
    #value = ing(value)
    if value < 512000:
        value = value / 1024.0
        ext = 'kb'
    elif value < 4194304000:
        value = value / 1048576.0
        ext = 'mb'
    else:
        value = value / 1073741824.0
        ext = 'gb'
    return '%s %s' % (str(round(value, 2)), ext)

register.filter('sizify', sizify)

def filename(value):
    return value.split('/')[-1]
register.filter('filename', filename)

def format_date(date):
    if date.date() == datetime.date.today():
        return 'Hoje às %02d:%02d' % (date.hour, date.minute,)
    return '%02d/%02d/%04d' % (date.day, date.month, date.year,)
register.filter('format_date', format_date)

def format_period(value):
    return '%s.%s' % (value[:4], value[4:], )
register.filter('format_period', format_period)