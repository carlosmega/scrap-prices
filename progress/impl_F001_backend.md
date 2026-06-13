# Implementación F001 — Bootstrap backend (capa: backend)

Spec aplicada: `specs/F001-bootstrap-backend.md`.

## Spec aplicada + decisiones (máx. 5 líneas)
- Proyecto Django 6.0 + django-ninja 1.6 gestionado con `uv`; instancia `config.api.api`, router de `core` montado en `/api/`, endpoint estático `GET /api/health -> {"status":"ok"}` (no toca DB).
- SQLite sin Docker: `DATABASE_URL` default `sqlite:///db.sqlite3` vía django-environ; `CORS_ALLOWED_ORIGINS` default `http://localhost:3000`; `'ninja'` y `corsheaders` en INSTALLED_APPS; `CorsMiddleware` arriba del todo.
- `[tool.pytest.ini_options]` con `DJANGO_SETTINGS_MODULE = "config.settings"` en `pyproject.toml`. Celery solo esqueleto importable (`config/celery.py`), no se ejercita.
- Arquitectura limpia con DOBLE regla mecánica: ruff `flake8-tidy-imports` banned-api (TID251 prohíbe `django.db.models`/`django.http` en `api.py`) + import-linter (contrato `apps.*.api` no importa `apps.*.models`). Lógica en `services.py`, router delgado que delega.
- Decisión: NO se persiste `backend/openapi.json` en F001 (el pipeline de contrato es F003); la Fase 5 de `init.sh` marcaría `bad` si existiera `backend/openapi.json` sin su par `frontend/src/lib/api/schema.d.ts`, que aún no existe. El comando de export sí funciona (exigencia real de F001).

## Archivos creados/modificados
- `backend/pyproject.toml` (deps, dev-deps, pytest ini_options, ruff + banned-api, import-linter)
- `backend/manage.py`
- `backend/config/__init__.py` (expone celery_app)
- `backend/config/settings.py`
- `backend/config/api.py` (instancia `api`)
- `backend/config/urls.py`
- `backend/config/celery.py` (esqueleto)
- `backend/config/wsgi.py`, `backend/config/asgi.py`
- `backend/apps/__init__.py`
- `backend/apps/core/__init__.py`, `apps.py`, `schemas.py`, `services.py`, `api.py`, `models.py`, `tasks.py`
- `backend/apps/core/tests/__init__.py`, `backend/apps/core/tests/test_health.py`
- (generados por uv: `backend/uv.lock`, `backend/.venv/`, `backend/db.sqlite3` en ejecuciones — db ignorada por .gitignore vía .venv? db.sqlite3 NO está en .gitignore; ver deuda)

## ¿Cambió el contrato OpenAPI?
No (frente a estado previo no había backend). NO se commitea `backend/openapi.json` en F001:
el pipeline de contrato (regen + `frontend/src/lib/api/schema.d.ts` + `pnpm gen:api`) es responsabilidad de F003.
No se requiere disparar `pnpm gen:api` ahora (frontend aún sin bootstrapear, F002 pending).

## Output REAL de las verificaciones

### uv sync
```
Resolved 41 packages in 1ms
Audited 40 packages in 4ms
```

### uv run ruff check .
```
All checks passed!
```

### uv run python manage.py makemigrations --check --dry-run
```
No changes detected
```
(exit 0)

### uv run pytest -q
```
..                                                                       [100%]
```
(2 passed)

### uv run python manage.py export_openapi_schema --api config.api.api  (NO "Unknown command")
```
{"openapi": "3.1.0", "info": {"title": "ConstruScan API", "version": "0.1.0", "description": "API de ConstruScan (Django Ninja)."}, "paths": {"/api/health": {"get": {"operationId": "apps_core_api_health", "summary": "Health", "parameters": [], "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/HealthOut"}}}}}, ...}}}, "components": {"schemas": {"HealthOut": {"properties": {"status": {"title": "Status", "type": "string"}}, "required": ["status"], "title": "HealthOut", "type": "object"}}}}
```

### uv run lint-imports (regla de capas import-linter)
```
Routers (api) no importan models directamente; delegan en services KEPT
Contracts: 1 kept, 0 broken.
```

## Verificaciones extra (evidencia de que las reglas muerden)
- Test NO nace verde: con `status="ok"` cambiado a `"DOWN"` en services.py, `pytest` FALLA
  (`AssertionError: assert 'DOWN' == 'ok'`, 2 failed). Restaurado -> 2 passed.
- Regla de capas muerde: al inyectar `from django.db import models` en `apps/core/api.py`,
  `ruff` falla con `TID251 django.db.models is banned`. Restaurado -> ruff limpio.
- Grep heurístico de init.sh (`.objects|.save(|.filter(|.create(|.delete(`) sobre apps/*/api.py: limpio.
- `manage.py check`: System check identified no issues.
- `from config.celery import app` importa OK (app.main = "construscan").

## Deuda / seguimientos detectados
1. `backend/openapi.json` y `pnpm gen:api`: diferidos a F003 (pipeline de contrato). El líder NO necesita
   disparar `pnpm gen:api` para F001.
2. `backend/db.sqlite3` se crea al correr comandos de Django y NO está en `.gitignore` raíz. Sugerencia:
   añadir `db.sqlite3` / `*.sqlite3` al `.gitignore` (no lo toco: está fuera de `backend/`).
3. `SECRET_KEY` tiene default inseguro para dev; debe venir de env en cualquier despliegue (fuera de alcance MVP).
4. Celery es solo esqueleto importable (sin broker, sin tasks reales ni tests de worker), por diseño de F001.
