import json
import os
from pathlib import Path
from urllib.parse import urlparse

import pymysql

pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_json_list(name: str, default: list[str] | None = None) -> list[str]:
    raw = os.getenv(name)
    if raw is None:
        return default or []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except Exception:
        pass
    return default or []


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me-django-secret")
DEBUG = _env_bool("DEBUG", True)
ALLOWED_HOSTS = _env_json_list("ALLOWED_HOSTS", ["*"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "app.apps.CoreAppConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "app.middleware.ExceptionLoggingMiddleware",
]

ROOT_URLCONF = "ss_ai_drf.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "ss_ai_drf.wsgi.application"
ASGI_APPLICATION = "ss_ai_drf.asgi.application"

_database_url = os.getenv("DATABASE_URL", "mysql+pymysql://ss_ai:ss_ai@db:3306/ss_ai")
_parsed_db = urlparse(_database_url)

if _parsed_db.scheme.startswith("mysql"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": (_parsed_db.path or "/ss_ai").lstrip("/") or "ss_ai",
            "USER": _parsed_db.username or "ss_ai",
            "PASSWORD": _parsed_db.password or "ss_ai",
            "HOST": _parsed_db.hostname or "db",
            "PORT": str(_parsed_db.port or 3306),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
APPEND_SLASH = False

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = _env_int("JWT_EXPIRE_MINUTES", 15)
JWT_REFRESH_EXPIRE_MINUTES = _env_int("JWT_REFRESH_EXPIRE_MINUTES", 43200)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TOKEN_BUDGET = _env_int("OPENAI_TOKEN_BUDGET", 128000)
OPENAI_USAGE_ENDPOINT = os.getenv("OPENAI_USAGE_ENDPOINT", "https://api.openai.com/v1/usage")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

CORS_ALLOWED_ORIGINS = _env_json_list("CORS_ALLOW_ORIGINS", [])
_cors_regex = os.getenv("CORS_ALLOW_ORIGIN_REGEX", r"^https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?$")
CORS_ALLOWED_ORIGIN_REGEXES = [_cors_regex] if _cors_regex else []
CORS_ALLOW_CREDENTIALS = _env_bool("CORS_ALLOW_CREDENTIALS", False)

CSRF_TRUSTED_ORIGINS = [origin for origin in CORS_ALLOWED_ORIGINS if origin.startswith("http")]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "app.auth_utils.BearerJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "EXCEPTION_HANDLER": "app.exceptions.custom_exception_handler",
}

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_BEAT_SCHEDULE = {
    "cron-quiz-job-every-5-minutes": {
        "task": "app.tasks.run_periodic_quiz_job",
        "schedule": 300.0,
    }
}
