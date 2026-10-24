"""
Django settings for HookRelay.
Everything that changes between environments comes from environment variables.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool) -> bool:
    """Read a True/False value from an environment variable."""
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------- Core
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = ["*"]  # fine for a local project; restrict in production

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party
    "rest_framework",
    "drf_spectacular",
    # our apps
    "accounts",
    "endpoints",
    "events",
    "deliveries",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

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

# ---------------------------------------------------------------- Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "hookrelay"),
        "USER": os.environ.get("POSTGRES_USER", "hookrelay"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "hookrelay"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# We replace Django's default User with our own (in the accounts app).
# This must be decided BEFORE the first migration.
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

# ---------------------------------------------------------------- i18n / static
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True  # always store timezone-aware datetimes
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------- Redis / Celery
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

CELERY_BROKER_URL = REDIS_URL
CELERY_TIMEZONE = "UTC"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# "acks_late" = the task is marked as done only AFTER it finishes.
# If a worker crashes mid-task, the task is run again. This is what gives us
# AT-LEAST-ONCE delivery (see DECISIONS.md later).
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
# Periodic jobs are added in phase 3.
CELERY_BEAT_SCHEDULE = {}

# ---------------------------------------------------------------- Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Authentication classes are added in phase 2 (API key auth).
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "HookRelay API",
    "DESCRIPTION": "Reliable webhook delivery service.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ---------------------------------------------------------------- HookRelay settings
# SSRF protection: when False, target URLs pointing to localhost / private IPs
# are rejected. Set True only for local demos.
HOOKRELAY_ALLOW_PRIVATE_URLS = env_bool("HOOKRELAY_ALLOW_PRIVATE_URLS", True)

# Rate limit for POST /api/events/ (phase 2)
HOOKRELAY_RATE_LIMIT_PER_MINUTE = 100

# Delivery behaviour (phase 3)
HOOKRELAY_DELIVERY_TIMEOUT_SECONDS = 5
HOOKRELAY_MAX_ATTEMPTS = 5
HOOKRELAY_RETRY_DELAYS_SECONDS = [60, 300, 1800, 7200, 21600]  # 1m, 5m, 30m, 2h, 6h
HOOKRELAY_CIRCUIT_BREAKER_THRESHOLD = 10  # consecutive failures before auto-disable
HOOKRELAY_RESPONSE_BODY_MAX_CHARS = 1000  # how much of the response we store

# Idempotency keys are remembered for this long (phase 2)
HOOKRELAY_IDEMPOTENCY_TTL_HOURS = 24