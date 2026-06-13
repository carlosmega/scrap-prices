# backend/CLAUDE.md — Reglas operativas de esta capa

Estás trabajando dentro del backend (Django + Django Ninja + Celery).
Las convenciones completas viven en `../docs/conventions-backend.md`;
esto es lo no negociable:

1. Lógica de negocio en `services.py`, nunca en routers.
2. Todo endpoint con `response=` y schema explícito en `schemas.py`.
3. Migraciones commiteadas junto al modelo que las causa.
4. Si tocaste schemas o rutas: regenera el contrato antes de terminar:
   `uv run python manage.py export_openapi_schema --api config.api.api --indent 2 --output openapi.json`
5. Verificación local mínima antes de reportar:
   `uv run ruff check . && uv run python manage.py makemigrations --check --dry-run && uv run pytest -q`

Postgres y Redis vienen del docker-compose de la raíz (`docker compose up -d`).
