# Initialize App Engine and import the default settings (DB backend, etc.).
# If you want to use a different backend you have to remove all occurences
# of "djangoappengine" from this file.
from djangoappengine.settings_base import *
import os

SECRET_KEY = '=r-$b*8hglm+858&9t043hlm6-&6-3d3vfc4((7yd0dbrakhvi'

TIME_ZONE = 'America/Recife'
LANGUAGE_CODE = 'pt-br'

MIDDLEWARE_CLASSES = (
    "mediagenerator.middleware.MediaMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.doc.XViewMiddleware",
    'django.middleware.csrf.CsrfViewMiddleware',
#    'profiling.middleware.ProfileMiddleware',
)

INSTALLED_APPS = (
    'djangoappengine',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.comments',
    'djangotoolbox',
    'filetransfers',
    'portal',
    'portal.album',
    'portal.files',
    'portal.updates',
    'portal.messages',
    'portal.groups',
    'portal.polls',
    'mediagenerator',
)

AUTH_PROFILE_MODULE = 'portal.UserInfo'

# This test runner captures stdout and associates tracebacks with their
# corresponding output. Helps a lot with print-debugging.
TEST_RUNNER = 'djangotoolbox.test.CapturingTestSuiteRunner'

ADMIN_MEDIA_PREFIX = '/media/admin/'
STATICFILES_ROOT = os.path.join(os.path.dirname(__file__), '_generated_media')
STATICFILES_DIRS = (
    os.path.join(os.path.dirname(__file__), 'static'),
)
STATICFILES_URL = '/media/'
MEDIA_URL = '/media/'
TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'),)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
)

ROOT_URLCONF = 'urls'

SITE_ID = 1

#Setup the cache
CACHE_BACKEND  = 'memcached://?timeout=30'

#Media generator configuration
# Get project root folder
_project_root = os.path.dirname(__file__)

# Set global media search paths
GLOBAL_MEDIA_DIRS = (
    os.path.join(_project_root, 'static'),
)

# Set media URL (important: don't forget the trailing slash!).
# PRODUCTION_MEDIA_URL is used when running manage.py generatemedia
MEDIA_DEV_MODE       = True # True for Development mode and False for Production
DEV_MEDIA_URL        = '/devmedia/'
PRODUCTION_MEDIA_URL = '/media/'

YUICOMPRESSOR_PATH    = os.path.join(_project_root, 'yuicompressor-2.4.6.jar')
CLOSURE_COMPILER_PATH = '/Users/brunocatao/PycharmProjects/portalsaladeaula/compiler.jar'

ROOT_MEDIA_FILTERS = {
    #'js': 'mediagenerator.filters.yuicompressor.YUICompressor',
    'js' : 'mediagenerator.filters.closure.Closure',
    'css': 'mediagenerator.filters.yuicompressor.YUICompressor',
}

# Media bundles definition
BASE_BUNDLE_CSS = (
    'css/main.css',
    'css/sexybuttons.css',
    'css/jquery-ui-1.8.9.custom.css',
)

BASE_BUNDLE_JS = (
    'js/jquery-1.4.2.js',
    'js/jquery-ui-1.8.9.custom.min.js',
    'js/jquery.clearfield.packed.js',
)

MEDIA_BUNDLES = (
    # General bundles, for the base area of the portal
    ('base.css', ) + BASE_BUNDLE_CSS,
    ('base.js', ) + BASE_BUNDLE_JS,
    ('home.js', ) + BASE_BUNDLE_JS + (
        'js/jquery.form.js',
    ),
    ('public_site.css', ) + BASE_BUNDLE_CSS + (
        'css/validationEngine.jquery.css',
    ),
    ('public_site.js', ) + BASE_BUNDLE_JS + (
        'js/jquery.validationEngine-pt.js',
        'js/jquery.validationEngine.js',
        'js/jquery.maskedinput-1.2.2.min.js',
    ),
    ('form.css', ) + BASE_BUNDLE_CSS + (
        'css/forms.css',
        'css/validationEngine.jquery.css',
    ),
    ('form.js', ) + BASE_BUNDLE_JS + (
        'js/jquery.validationEngine-pt.js',
        'js/jquery.validationEngine.js',
        'js/jquery.maskedinput-1.2.2.min.js',
        'js/jquery.form.js',
    ),
    ('jquery.hoverbox.min.js', 'js/jquery.hoverbox.min.js', ),
    # Albums bundles
    ('album_detail.css', ) + BASE_BUNDLE_CSS + (
        'css/album.css',
        'css/galleriffic/galleriffic-2.css',
    ),
    ('album_detail.js', ) + BASE_BUNDLE_JS + (
        'js/jquery.galleriffic.js',
        'js/jquery.opacityrollover.js',
    ),
    ('album_form.css', ) + BASE_BUNDLE_CSS + (
        'css/album.css',
    ),
    # Internal, general bundles
    ('internal_detail.css', ) + BASE_BUNDLE_CSS + (
        'css/jquery.rating.css',
        'css/skins/ie7/skin.css',
        'css/news.css',
        'css/jquery.twit.0.2.0.css',
        'css/bx_styles/bx_styles.css',
        'css/messages.css',
        'css/validationEngine.jquery.css',
    ),
    ('internal_detail.js', ) + BASE_BUNDLE_JS + (
        'js/jquery.form.js',
        'js/jquery.validationEngine-pt.js',
        'js/jquery.validationEngine.js',
#        'js/jquery.jcarousel.js',
        'js/jquery.twit.0.2.0.min.js',
        'js/jquery.bxSlider.min.js',
        'js/jquery.rating.pack.js',
        'js/images.js',
    ),
    # Polls bundles
    ('poll_answer.css', ) + BASE_BUNDLE_CSS + (
        'css/polls/style.css',
        'css/validationEngine.jquery.css',
    ),
    ('poll_answer.js', ) + BASE_BUNDLE_JS + (
        'js/jquery.validationEngine-pt.js',
        'js/jquery.validationEngine.js',
    ),
    # Registrations bundles
    ('registration_profile.css', ) + BASE_BUNDLE_CSS + (
        'css/profile.css',
        'css/messages.css',
        'css/validationEngine.jquery.css',
    ),
    ('registration_profile.js', ) + BASE_BUNDLE_JS + (
        'js/jquery.form.js',
        'js/jquery.hoverbox.min.js',
        'js/jquery.corner.js',
        'js/jquery.validationEngine-pt.js',
        'js/jquery.validationEngine.js',
    ),
    ('registration_register.js', ) + BASE_BUNDLE_JS + (
        'js/jquery.form.js',
    ),
    # Search bundles
    ('search.css', ) + BASE_BUNDLE_CSS + (
        'css/search.css',
    ),
)

# CUSTOM SETTINGS
#The application's default encoding
DEFAULT_ENCODING = 'utf-8'
PERIODO_ATUAL    = '20112'

# Activate django-dbindexer if available
try:
    import dbindexer
    DATABASES['native'] = DATABASES['default']
    DATABASES['default'] = {'ENGINE': 'dbindexer', 'TARGET': 'native'}
    INSTALLED_APPS += ('dbindexer',)
except:
    pass

