__author__ = 'brunocatao'

from django.test import TestCase
from google.appengine.ext import db
from google.appengine.api import images
import logging

from portal.models import Picture
class PictureTestCase(TestCase):
    PICTURE_FILE_NAME = '/Users/brunocatao/Pictures/foto.jpg'

    def setUp(self):
        logging.info('reading the image file ...')
        self.picture_file = file(PictureTestCase.PICTURE_FILE_NAME).read()

    def testCreatePicture(self):
        logging.info('creating a picture ...')

        picture = Picture()
        picture.picture  = db.Blob(self.picture_file)
        picture.filename = PictureTestCase.PICTURE_FILE_NAME
        picture.save()

        self.assertEquals(193, picture.width)
        self.assertEquals(237, picture.height)
        self.assertEquals('jpg', picture.format)

    def testCreateThumbnail(self):
        picture = Picture()
        picture.picture  = db.Blob(self.picture_file)
        picture.filename = PictureTestCase.PICTURE_FILE_NAME
        picture.save()

        thumb = Picture.create_thumbnail(picture, 32, 32)
        self.assertTrue(thumb is not None)

    def testGetThumbnail(self):
        picture = Picture()
        picture.picture  = db.Blob(self.picture_file)
        picture.filename = PictureTestCase.PICTURE_FILE_NAME
        picture.save()

        pre_thumb = Picture.create_thumbnail(picture, 32, 32)
        self.assertTrue(pre_thumb is not None)

        thumb = Picture.get_thumbnail(picture, 32, 32)
        self.assertTrue(thumb is not None)
        self.assertEquals(pre_thumb.id, thumb.id) # It should not create a new thumbnail
        self.assertTrue(thumb.width <= 32)
        self.assertTrue(thumb.height <= 32)
        self.assertEquals('jpg', thumb.format)

        thumb = Picture.get_thumbnail(picture, 64, 64)
        self.assertTrue(thumb is not None)
        self.assertTrue(thumb.id != pre_thumb.id)

        thumb = Picture.get_thumbnail(picture, 128, 128)
        self.assertTrue(thumb is not None)
        self.assertTrue(thumb.id != pre_thumb.id)

# Load the tests from portal.accounts module
from portal.accounts.tests import RegisterUserTestCase
# Load the tests from portal.album module
from portal.album.tests import AlbumTestCase
# Load the tests from portal.polls module
from portal.polls.tests import PollTestCase