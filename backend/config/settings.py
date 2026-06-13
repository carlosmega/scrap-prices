"""Settings de Django para el proyecto ConstruScan.

Configuración por variables de entorno (django-environ) con defaults locales.
MVP: SQLite y sin Docker. Postgres/Redis del docker-compose son migración
posterior, no requerida ahora.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, "dev-insecure-key-change-me-in-production"),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    # MVP: SQLite por defecto, sin Docker.
    DATABASE_URL=(str, "sqlite:///db.sqlite3"),
    # Celery: solo esqueleto importable en MVP (no hay broker corriendo).
    REDIS_URL=(str, "redis://localhost:6379/0"),
    # CORS: el frontend de Next vive en :3000 y consume la API en :8000.
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000"]),
)

# Lee un .env de la raíz del backend si existe (no requerido).
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# --- Aplicaciones -----------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros
    # 'ninja' es obligatorio: sin él, el management command
    # export_openapi_schema no se registra y el flujo de contrato es imposible.
    "ninja",
    "corsheaders",
    # Apps del dominio
    "apps.core",
    "apps.common",
    "apps.geo",
    "apps.catalog",
    "apps.prices",
    "apps.lists",
]

# --- Middleware -------------------------------------------------------------
# CorsMiddleware lo más arriba posible (antes de CommonMiddleware) para que
# las cabeceras CORS se apliquen incluso en respuestas tempranas.
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Base de datos ----------------------------------------------------------
# MVP: SQLite vía DATABASE_URL. env.db() parsea la URL a la config de Django.
DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# --- Validación de contraseñas ----------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internacionalización ---------------------------------------------------
LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

# --- Archivos estáticos -----------------------------------------------------
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- CORS -------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")

# --- Celery -----------------------------------------------------------------
# Solo esqueleto en MVP: no hay broker corriendo, no se ejercita ningún worker.
CELERY_BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TIMEZONE = TIME_ZONE
