"""
Django settings for atlas project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

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
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

TEMPLATE_DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# 2021-08-21 KWS Need to set this to None, otherwise default is 1000.
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

ALLOWED_HOSTS = ['*']

INTERNAL_IPS = [
    '127.0.0.1',
]

ROOT_URLCONF = 'atlas.urls'

WSGI_APPLICATION = 'atlas.wsgi.application'

# 2016-11-07 KWS Fixed the authentication issues by setting cookie names
CSRF_COOKIE_NAME = 'csrf_' + os.environ.get('DJANGO_MYSQL_DBNAME')
SESSION_COOKIE_NAME = 'session_' + os.environ.get('DJANGO_MYSQL_DBNAME')

# 2017-10-03 KWS Had to add this setting because of SSL proxy.
CSRF_TRUSTED_ORIGINS = ['https://star.pst.qub.ac.uk', 'https://psweb.mp.qub.ac.uk']


CSRF_FAILURE_VIEW = 'atlas.views.csrf_failure'

LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DJANGO_DB_ENGINE', 'django.db.backends.mysql'),
        'NAME': os.environ.get('DJANGO_MYSQL_DBNAME'),
        'USER': os.environ.get('DJANGO_MYSQL_DBUSER'),
        'PASSWORD': os.environ.get('DJANGO_MYSQL_DBPASS'),
        'HOST': os.environ.get('DJANGO_MYSQL_DBHOST'),
        'PORT': int(os.environ.get('DJANGO_MYSQL_DBPORT')),
        'TEST': {
            'NAME': os.environ.get('DJANGO_MYSQL_TEST_DBNAME'),
            'PORT': os.environ.get('DJANGO_MYSQL_TEST_DBPORT'),
            'USER': os.environ.get('DJANGO_MYSQL_TEST_DBUSER'),
            'PASSWORD': os.environ.get('DJANGO_MYSQL_TEST_DBPASS'),
        }
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
    }
}


DJANGO_LOG_LEVEL = os.environ.get('DJANGO_LOG_LEVEL', 'WARNING')
LOGGING = {
    "version": 1,  # the dictConfig format version
    "disable_existing_loggers": False,  # retain the default loggers
    "formatters": {
        "verbose": {
            "format": "{name} {levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },

    "handlers": {
        # The different log handlers are defined here. We have a file logger and 
        # a stderr logger - which reroutes to the error_log file managed by wsgi.  
        "file": {
            "class": "logging.FileHandler",
            "filename": "django-default.log",
            "level": DJANGO_LOG_LEVEL,
            "formatter": "verbose",
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "level": DJANGO_LOG_LEVEL,
            "formatter": "verbose",
            "stream": "ext://sys.stderr",
        }
    },
    # Implement the stderr logger as the default logger.
    "loggers": {
        "": {
            "handlers": ["stderr","file"],
            "level": DJANGO_LOG_LEVEL,
            "propagate": True,
        },
    }

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
# Introduce Pan-STARRS API
PANSTARRS_TOKEN = os.environ.get('DJANGO_PANSTARRS_TOKEN')
PANSTARRS_BASE_URL = os.environ.get('DJANGO_PANSTARRS_BASE_URL')

DUSTMAP_LOCATION = os.environ.get('DJANGO_DUSTMAP_LOCATION')

# 2024-02-21 KWS Added new Virtual Research Assistant settings.
VRA_ADD_ROW = True
VRA_DEBUG = False

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

ROOT_URLCONF = 'atlas.urls'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django_registration',
    'atlas',
    'accounts',
    'django_tables2',
    'rest_framework',
    'rest_framework.authtoken',
]

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'atlasapi.throttling.UserAdminRateThrottle',    # Allow admin users unlimited rate, otherwise use the default rate 
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/hour',       # The only anonymous endpoint is the token refresh endpoint
        'user': '100/hour',      # Limit regular authenticated users to 100 requests per hour
        'admin': '100000/hour',  # Allow admin users (basically) unlimited rate
    }
}

# Token expiry time in days, default 1 day (24*60*60 seconds)
TOKEN_EXPIRY = int(os.environ.get("API_TOKEN_EXPIRY") or 86400) # seconds

# Variables for the django_registration app
ACCOUNT_ACTIVATION_DAYS = int(os.environ.get("ACCOUNT_ACTIVATION_DAYS") or 7)
REGISTRATION_OPEN = True

if DEBUG:
    INSTALLED_APPS = [
        *INSTALLED_APPS,
        "debug_toolbar",
    ]
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        *MIDDLEWARE,
    ]
    DEBUG_TOOLBAR_CONFIG = {
        # Always show the toolbar in debug mode
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
    }
