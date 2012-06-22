__author__ = 'brunocatao'

from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from google.appengine.ext import db
import logging

from portal.models import Picture, Institution
from portal.album.models import Album, RelPictureAlbum

class AlbumTestCase(TestCase):
    PICTURE_FILE_NAME = '/Users/brunocatao/Pictures/foto.jpg'

    def setUp(self):
        logging.info('reading the image file ...')
        self.picture_file = file(AlbumTestCase.PICTURE_FILE_NAME).read()

    def testSomething(self):
        picture = Picture()
        picture.picture  = db.Blob(self.picture_file)
        picture.filename = AlbumTestCase.PICTURE_FILE_NAME
        picture.save()

        institution = Institution(name='Institution', picture=picture, description='Description', homepage='http://www.homepage.com')
        institution.save()

        album = Album.create_album(title='Some party', instance=institution)
        album.add_picture(picture)

        logging.info('Institution albums: %s' % str(Album.objects.for_model(institution)))

        for rpa in album.picture_album_set.all():
            logging.info('Picture - %s [%d x %d]' % (rpa.picture.filename, rpa.picture.width, rpa.picture.height))