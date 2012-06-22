__author__ = 'brunocatao'

from django import template
from django.core.urlresolvers import reverse
from portal.models import Picture

register = template.Library()

def show_image(picture):
    return reverse('portal.views.image', args=(picture.id,))
register.filter('image', show_image)

def show_thumbnail(picture, size):
    size = size.lower().split('x')
    return show_image(Picture.get_thumbnail(picture, int(size[0]), int(size[1])))
register.filter('thumbnail', show_thumbnail)
