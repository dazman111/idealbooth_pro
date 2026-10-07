"""
Django settings for booking project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'handlers': {
        'daily_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'app.log'),
            'when': 'midnight',
            'backupCount': 30,
            'formatter': 'verbose',
        },
    },

    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },

    'loggers': {
        'django': {
            'handlers': ['daily_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'app': {
            'handlers': ['daily_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}



# Security
STRIPE_WEBHOOK_SECRET = SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Applications
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Project apps
    'home',
    'accounts',
    'admin_panel',
    'photobooths',
    'reservations',
    'cart',
    'coupons',
    'blog',

    # Third-party apps
    'django_ckeditor_5',
    'django_crontab',
    'rest_framework',
    'rest_framework.authtoken',
]

AUTH_USER_MODEL = 'accounts.CustomUser'

# MySQL compatibility
import pymysql
pymysql.install_as_MySQLdb()

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # IMPORTANT pour les langues
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'booking.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'admin_panel.context_processors.admin_unread_messages',


                # Custom context processors
                'cart.context_processors.cart_count',
                'accounts.context_processors.unread_messages_count',
                'accounts.context_processors.auth_token',
                'coupons.context_processors.promo_message',
            ],
        },
    },
]

WSGI_APPLICATION = 'booking.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'fr'

LANGUAGES = [
    ('fr', _('Français')),
    ('en', _('English')),
    ('nl', _('Nederlands')),
]

TIME_ZONE = 'Europe/Brussels'
USE_I18N = True
USE_L10N = True
USE_TZ = False

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Login
LOGIN_REDIRECT_URL = '/home/'
LOGIN_URL = '/accounts/login/'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

# CKEditor
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_ALLOW_NONIMAGE_FILES = False

CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|', 'bold', 'italic', 'underline', 'link',
            '|', 'bulletedList', 'numberedList', 'blockQuote',
            '|', 'insertTable', 'mediaEmbed', 'undo', 'redo'
        ],
        'language': 'fr',
    }
}

# Cron jobs
CRONJOBS = [
    ('0 0 * * *', 'accounts.management.commands.delete_pending_users.Command.handle'),
]

# ModelTranslation
MODELTRANSLATION_DEFAULT_LANGUAGE = 'fr'
MODELTRANSLATION_LANGUAGES = ('fr', 'en', 'nl')
