# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F001** — Bootstrap backend (Django + Django Ninja + Celery esqueleto)
**Spec:** `specs/F001-bootstrap-backend.md`

## Plan F001

Orquestación: capa única `backend` → `implementer-backend` → `reviewer`.

Contexto/constraints que el implementer debe respetar (ya reflejados en la spec):
- **SQLite, sin Docker** (`DATABASE_URL` default `sqlite:///db.sqlite3`). NO configurar Postgres.
- `'ninja'` en `INSTALLED_APPS` (para `export_openapi_schema`).
- `[tool.pytest.ini_options]` con `DJANGO_SETTINGS_MODULE = "config.settings"`.
- `corsheaders` + `CORS_ALLOWED_ORIGINS` (default `http://localhost:3000`).
- Lógica en `services.py`; `api.py` sin ORM. Regla de capas (import-linter/ruff).
- Celery esqueleto: importable, NO se ejercita en MVP (no hay broker).
- Entorno: `jq` y `docker` ausentes a propósito; verificar con `uv run …` (pytest contra SQLite).

Criterios de cierre: `./init.sh` verde + `uv run pytest`/`ruff`/`makemigrations --check` limpios
+ `export_openapi_schema` funciona + review APROBADO.

**Estado:** F001 marcada `in_progress`. Lanzando `implementer-backend`.

## Historial de esta sesión (endurecimiento previo)
Auditoría + lote de fixes + estrategia de tests + pivote a SQLite/sin-Docker y
`init.sh` independiente de `jq` (usa node). Detalle en `progress/auditoria-arnes-2026-06-13.md`
y commits `d6c1734`, `f1baa4b`.
