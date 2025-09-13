# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from dotenv import load_dotenv

# import forcephot

load_dotenv(override=True)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PATHPREFIX = os.environ.get('WSGI_PREFIX')

SITE_ID = 1

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = False

# 2021-08-21 KWS Need to set this to None, otherwise default is 1000.
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

ALLOWED_HOSTS = ['*']

ROOT_URLCONF = 'psdb.urls'

WSGI_APPLICATION = 'psdb.wsgi.application'

# 2016-11-07 KWS Fixed the authentication issues by setting cookie names
CSRF_COOKIE_NAME = 'csrf_' + os.environ.get('DJANGO_MYSQL_DBNAME')
SESSION_COOKIE_NAME = 'session_' + os.environ.get('DJANGO_MYSQL_DBNAME')

# 2017-10-03 KWS Had to add this setting because of SSL proxy.
CSRF_TRUSTED_ORIGINS = ['https://star.pst.qub.ac.uk', 'https://psweb.mp.qub.ac.uk']

CSRF_FAILURE_VIEW = 'psdb.views.csrf_failure'

LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DJANGO_MYSQL_DBNAME'),
        'USER': os.environ.get('DJANGO_MYSQL_DBUSER'),
        'PASSWORD': os.environ.get('DJANGO_MYSQL_DBPASS'),
        'HOST': os.environ.get('DJANGO_MYSQL_DBHOST'),
        'PORT': int(os.environ.get('DJANGO_MYSQL_DBPORT')),
    }
}


DAEMONS = {
    'tns': {
        'host': os.environ.get('DJANGO_TNS_DAEMON_SERVER'),
        'port': int(os.environ.get('DJANGO_TNS_DAEMON_PORT')),
        'test': False
    },
    'mpc': {
        'host': os.environ.get('DJANGO_MPC_DAEMON_SERVER'),
        'port': int(os.environ.get('DJANGO_MPC_DAEMON_PORT')),
        'test': False
    },
    'psnames': {
        'host': os.environ.get('DJANGO_NAME_DAEMON_SERVER'),
        'port': int(os.environ.get('DJANGO_NAME_DAEMON_PORT')),
        'test': False
    }
}

SURVEY_FIELDS = {
    'RINGS': os.environ.get('DJANGO_SURVEY_FIELD'),
    'FGSS': '3F',
    'MD01': '01',
    'MD02': '02',
    'MD03': '03',
    'MD04': '04',
    'MD05': '05',
    'MD06': '06',
    'MD07': '07',
    'MD08': '08',
    'MD09': '09',
    'MD10': '10',
    'M31': '31',
}


LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LASAIR_TOKEN = os.environ.get('DJANGO_LASAIR_TOKEN')
NAMESERVER_TOKEN = os.environ.get('DJANGO_NAMESERVER_TOKEN')
NAMESERVER_API_URL = os.environ.get('DJANGO_NAMESERVER_API_URL')
NAMESERVER_MULTIPLIER = os.environ.get('DJANGO_NAMESERVER_MULTIPLIER')
# Introduce ATLAS API
ATLAS_TOKEN = os.environ.get('DJANGO_ATLAS_TOKEN')
ATLAS_BASE_URL = os.environ.get('DJANGO_ATLAS_BASE_URL')

DISPLAY_AGNS = os.environ.get('DJANGO_DISPLAY_AGNS') in ('true', '1', 't', 'True', 'TRUE', 'T')

# 2021-05-06 KWS New settings means that if we edit a static file we MUST rerun the collectstatic
#                code to deploy the modified file.

STATIC_URL = PATHPREFIX + '/static/'

# STATICFILES_DIRS tells collectstatic where MY static files are.
STATICFILES_DIRS = (
  os.path.join(BASE_DIR, 'site_media'),
)

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# MEDIA is DIFFERENT from static files.  It's serving up files from a mounted filesystem for example.
# These files are NOT covered by collectstatic, but the webserver DOES need to know where they are!
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = PATHPREFIX + '/media/'

# All below copied from PS1 web app.

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
            os.path.join(BASE_DIR, 'templates'),

        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.request",
                "django.template.context_processors.static",
                "django.template.context_processors.request",
            ],
        },
    },
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

ROOT_URLCONF = 'psdb.urls'

# 2024-09-19 KWS Added Django Rest Framework
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'psdb',
    'django_tables2',
    'rest_framework',
    'rest_framework.authtoken',
]
