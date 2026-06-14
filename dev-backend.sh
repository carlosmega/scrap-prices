#!/usr/bin/env bash
# Levanta el backend de ConstruScan en el puerto fijo local 8800 (F023).
# Aplica migraciones y siembra datos demo (idempotente) antes de servir.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT/backend"
uv run python manage.py migrate
uv run python manage.py seed
exec uv run python manage.py runserver 127.0.0.1:8800
