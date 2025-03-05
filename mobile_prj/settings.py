import logging
import sentry_sdk.integrations.django
import helpers.cloudflare.settings

from pathlib import Path
from datetime import timedelta
from decouple import config
from sentry_sdk.integrations.django import DjangoIntegration

TWILIO_ACCOUNT_SID = config("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = config("TWILIO_AUTH_TOKEN")
TWILIO_VERIFY_SERVICE_SID = config("TWILIO_VERIFY_SERVICE_SID")
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-#uied7d2d4va9@h&-q^qo)v^$o#5mmgx^_8nn8%fw@!b)n@)0k"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "m.foxminded.space"]
CSRF_TRUSTED_ORIGINS = ["https://m.foxminded.space"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "mobile_rest.apps.MobileRestConfig",
    "drf_yasg",
    "fcm_django",
]

FCM_DJANGO_SETTINGS = {
    "FCM_SERVER_KEY": "YOUR_SERVER_KEY",  # Секретный ключ FCM из Firebase
    "ONE_DEVICE_PER_USER": False,  # Разрешить несколько устройств на пользователя
    "DELETE_INACTIVE_DEVICES": True,  # Удалять неактивные устройства
}

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}
AUTH_USER_MODEL = "mobile_rest.CustomUser"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mobile_prj.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mobile_prj.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": config("POSTGRES_DB"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD"),
        "HOST": config("POSTGRES_HOST"),
        "PORT": config("POSTGRES_PORT"),
    }
}

STATIC_URL = "static/"

STORAGES = {
    "default": {
        "BACKEND": "helpers.cloudflare.storages.MediaFileStorage",
        "OPTIONS": helpers.cloudflare.settings.CLOUDFLARE_R2_CONFIG_OPTIONS,
    },
    "staticfiles": {
        "BACKEND": "helpers.cloudflare.storages.StaticFileStorage",
        "OPTIONS": helpers.cloudflare.settings.CLOUDFLARE_R2_CONFIG_OPTIONS,
    },
}

logging.basicConfig(level=logging.INFO)

sentry_sdk.init(
    dsn=config("SENTRY_DSN"),
    debug=True,
    integrations=[
        DjangoIntegration(middleware_spans=True, signals_spans=True, ),
    ],
    environment="development",
    traces_sample_rate=1.0,
    send_default_pii=True,
    auto_session_tracking=True
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "sentry": {
            "level": "ERROR",
            "class": "sentry_sdk.integrations.logging.SentryHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["sentry"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Almaty"

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
