"""Settings de Django para el proyecto ConstruScan.

Configuración por variables de entorno (django-environ) con defaults locales.
MVP: SQLite y sin Docker. Postgres/Redis del docker-compose son migración
posterior, no requerida ahora.
"""

from pathlib import Path

import environ
from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, "dev-insecure-key-change-me-in-production"),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    # MVP: SQLite por defecto, sin Docker.
    DATABASE_URL=(str, "sqlite:///db.sqlite3"),
    # Celery: solo esqueleto importable en MVP (no hay broker corriendo).
    REDIS_URL=(str, "redis://localhost:6379/0"),
    # CORS: el frontend de Next vive en :3300 y consume la API en :8800 (F023).
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3300"]),
    # --- Scraping (F024) ---------------------------------------------------
    # User-Agent HONESTO: identifica a ConstruScan y deja un contacto. NUNCA un
    # UA que imite a un navegador real para engañar (guardrail §2.3).
    SCRAPER_USER_AGENT=(str, "ConstruScan/0.1 (+https://construscan.example/contacto)"),
    # Delay mínimo entre 2 peticiones al MISMO dominio (cortesía / rate-limit).
    # Default conservador (≥ crawl-delay típico). En segundos.
    SCRAPER_MIN_DELAY_SECONDS=(float, 7.0),
    # Timeout de cada petición HTTP, en segundos.
    SCRAPER_TIMEOUT_SECONDS=(float, 30.0),
    # Concurrencia máxima simultánea por dominio (semáforo). 1 = estrictamente
    # secuencial por dominio (lo más respetuoso).
    SCRAPER_MAX_CONCURRENCY_PER_DOMAIN=(int, 1),
    # Reintentos para errores TRANSITORIOS (timeout/5xx/red). NO aplica a
    # bloqueos 403/429: ante bloqueo se detiene, no se reintenta (§2.3).
    SCRAPER_MAX_RETRIES=(int, 3),
    # --- Construrama / Algolia (F026) --------------------------------------
    # El precio de Construrama se sirve por Algolia (índice construrama_mx,
    # campo OSS7_priceValue_mxn_double). El App ID y el índice son PÚBLICOS
    # (viajan en el host/bundle del front), por eso llevan default. La search
    # key (search-only, pública) NO se hardcodea ni se commitea: default vacío;
    # se inyecta por env (o se re-obtiene de `get/algolia`). Los tests son
    # offline (MockTransport) y no la requieren.
    CONSTRURAMA_ALGOLIA_APP_ID=(str, "NJVY3EU5DW"),
    CONSTRURAMA_ALGOLIA_INDEX=(str, "construrama_mx"),
    CONSTRURAMA_ALGOLIA_SEARCH_KEY=(str, ""),
    # --- Búsqueda en vivo bajo demanda (F033) -------------------------------
    # TTL de frescura: si NINGUNA observación del término+zona es más fresca que
    # esto, la búsqueda dispara la corrida en vivo (live-on-miss).
    SEARCH_LIVE_TTL_HOURS=(int, 24),
    # Cooldown por término+zona+retailer: evita martillar términos sin
    # resultados; aplica aunque la corrida previa hallara 0 items.
    SEARCH_LIVE_COOLDOWN_MINUTES=(int, 15),
    # Presupuesto TOTAL de la corrida en vivo (ambos retailers). Al vencer se
    # responde con lo que haya (el retailer lento se reporta failed: timeout).
    SEARCH_LIVE_TIMEOUT_SECONDS=(float, 25.0),
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
    "apps.scraping",
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

# F033: la base de TEST de SQLite va en ARCHIVO (no ":memory:"). La búsqueda en
# vivo corre los retailers en hilos (ThreadPoolExecutor) y cada hilo abre su
# propia conexión: con el ":memory:" compartido de Django los escritores
# concurrentes chocan con locks de tabla (SQLITE_LOCKED, sin busy-timeout);
# en archivo aplican los locks normales con busy-timeout. `*.sqlite3` está en
# .gitignore y Django la crea/destruye en cada corrida de tests.
if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    DATABASES["default"].setdefault("TEST", {})["NAME"] = BASE_DIR / "test_db.sqlite3"

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
# El frontend identifica la sesión anónima con un header custom (F022); sin
# permitirlo en CORS, el navegador bloquea el preflight de /api/lists*.
CORS_ALLOW_HEADERS = (*default_headers, "x-session-key")

# --- Celery -----------------------------------------------------------------
# Solo esqueleto en MVP: no hay broker corriendo, no se ejercita ningún worker.
CELERY_BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TIMEZONE = TIME_ZONE

# --- Scraping (F024) --------------------------------------------------------
# Guardrails éticos del PRD §2.3 cableados como configuración. Los defaults son
# conservadores y honestos; el entorno solo los ajusta, nunca los desactiva
# para evadir defensas (eso sería violar el principio del proyecto).
SCRAPER_USER_AGENT = env("SCRAPER_USER_AGENT")
SCRAPER_MIN_DELAY_SECONDS = env.float("SCRAPER_MIN_DELAY_SECONDS")
SCRAPER_TIMEOUT_SECONDS = env.float("SCRAPER_TIMEOUT_SECONDS")
SCRAPER_MAX_CONCURRENCY_PER_DOMAIN = env.int("SCRAPER_MAX_CONCURRENCY_PER_DOMAIN")
SCRAPER_MAX_RETRIES = env.int("SCRAPER_MAX_RETRIES")

# --- Construrama / Algolia (F026) -------------------------------------------
# App ID e índice son públicos (default). La search key es pública (search-only)
# pero NO se commitea: se lee de env (default vacío) o se re-obtiene de
# `get/algolia`. Sin key, el adapter no hace la petición real (falla claro).
CONSTRURAMA_ALGOLIA_APP_ID = env("CONSTRURAMA_ALGOLIA_APP_ID")
CONSTRURAMA_ALGOLIA_INDEX = env("CONSTRURAMA_ALGOLIA_INDEX")
CONSTRURAMA_ALGOLIA_SEARCH_KEY = env("CONSTRURAMA_ALGOLIA_SEARCH_KEY")

# --- Búsqueda en vivo bajo demanda (F033) ------------------------------------
# Gatillo live-on-miss de /api/search: TTL de frescura, cooldown por término+
# zona+retailer y presupuesto total de la corrida. Env-overridables; los
# defaults son los de la spec F033 (24 h / 15 min / 25 s).
SEARCH_LIVE_TTL_HOURS = env.int("SEARCH_LIVE_TTL_HOURS")
SEARCH_LIVE_COOLDOWN_MINUTES = env.int("SEARCH_LIVE_COOLDOWN_MINUTES")
SEARCH_LIVE_TIMEOUT_SECONDS = env.float("SEARCH_LIVE_TIMEOUT_SECONDS")
