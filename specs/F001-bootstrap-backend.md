# F001 — Bootstrap backend: Django + Django Ninja + Celery (esqueleto)

## Contexto y objetivo
Crear el backend mínimo verificable sobre el que se construirá todo. El
objetivo no es funcionalidad: es que `./init.sh` pueda ejercer la Fase 3
de punta a punta.

## Alcance
**Incluye:** proyecto Django gestionado con `uv`, API Ninja montada,
endpoint de salud, pytest, ruff, settings por variables de entorno,
esqueleto de Celery.
**No incluye:** modelos de dominio, autenticación, despliegue.

## Stack y versiones (fijas)
- Python >= 3.12, gestionado con `uv` (pyproject.toml, sin requirements.txt)
- Django >= 5.1, django-ninja >= 1.3, celery[redis] >= 5.4
- pytest + pytest-django, ruff (lint + format), django-environ
- django-cors-headers (el frontend de Next en `:3000` consume la API en `:8000`)

## Configuración no negociable (so pena de fallo silencioso)
Estos puntos NO son obvios y rompen los comandos canónicos si se omiten:
- **`'ninja'` en `INSTALLED_APPS`**: sin él, `manage.py export_openapi_schema`
  no se registra como management command y la Fase 5 de contrato es imposible.
- **`DJANGO_SETTINGS_MODULE` para pytest**: `uv run pytest` NO pasa por
  `manage.py`, así que hay que fijarlo en `[tool.pytest.ini_options]` de
  `pyproject.toml` (`DJANGO_SETTINGS_MODULE = "config.settings"`). Sin esto
  `uv run pytest` falla con "Django settings not configured".
- **CORS**: `corsheaders` en `INSTALLED_APPS` + `CorsMiddleware` (lo más arriba
  posible), con `CORS_ALLOWED_ORIGINS` leído de env (default
  `http://localhost:3000`). Sin esto, el camino feliz client-side de F003/F005
  falla en el navegador aunque el backend esté arriba.

## Estructura esperada
```
backend/
├── CLAUDE.md            (ya existe, respetar)
├── pyproject.toml       # deps + [tool.pytest.ini_options] (DJANGO_SETTINGS_MODULE) + reglas de capas
├── manage.py
├── config/
│   ├── settings.py      # DATABASE_URL, REDIS_URL y CORS_ALLOWED_ORIGINS desde env;
│   │                    #   INSTALLED_APPS incluye 'ninja' y 'corsheaders'
│   ├── api.py           # instancia NinjaAPI llamada `api` + routers
│   ├── urls.py          # monta api en /api/
│   └── celery.py
└── apps/
    └── core/
        ├── api.py       # router con GET /health
        └── tests/test_health.py
```

## Arquitectura limpia (verificable)
- La lógica de negocio vive en `services.py`; los routers de `api.py` solo
  parsean/validan/delegan. **Ninguna llamada al ORM** (`.objects`, `.save(`,
  `.filter(`, `.create(`) dentro de `api.py`.
- Configura una regla de capas mecánica en `pyproject.toml`: `import-linter`
  (contrato que prohíbe `api` → `models`/`services`-internos fuera del patrón)
  **o**, como mínimo, `ruff` con `flake8-tidy-imports` (`banned-api`) para
  vetar imports prohibidos. La Fase 3 de `./init.sh` añade además un grep
  heurístico contra ORM en `api.py`.

## Contrato API
| Método | Ruta        | Response                | Errores |
| ------ | ----------- | ----------------------- | ------- |
| GET    | /api/health | `{"status": "ok"}`      | —       |

## Criterios de aceptación
- [ ] Backend: `uv run pytest` pasa con al menos un test del endpoint /api/health
      (con `DJANGO_SETTINGS_MODULE` configurado en `pyproject.toml`).
- [ ] Backend: `uv run python manage.py export_openapi_schema --api config.api.api`
      funciona (requiere `'ninja'` en `INSTALLED_APPS`).
- [ ] Backend: `uv run ruff check .` limpio; `makemigrations --check` limpio.
- [ ] Backend: el server arranca contra el Postgres de docker-compose con los defaults.
- [ ] Backend: `corsheaders` configurado; `CORS_ALLOWED_ORIGINS` desde env con
      default `http://localhost:3000`.
- [ ] Backend: regla de capas mecánica activa (import-linter o ruff banned-api);
      `api.py` no contiene llamadas al ORM.

## Plan de verificación
```bash
cd backend && uv sync && uv run pytest -q && uv run ruff check .
uv run python manage.py export_openapi_schema --api config.api.api   # no "Unknown command"
./init.sh   # Fase 3 debe pasar de PENDIENTE a verde
```
