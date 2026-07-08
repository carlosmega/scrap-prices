#!/usr/bin/env bash
# ============================================================================
# dev.sh — Levanta ConstruScan completo en local con un solo comando.
#   Backend  Django + Ninja  ->  http://localhost:8800  (F023, puerto fijo)
#   Frontend Next.js         ->  http://localhost:3300
# Ctrl+C detiene AMBOS servidores.
# ============================================================================
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Setup del backend (una vez, síncrono): migraciones + seed idempotente ---
echo "▶ Preparando backend (migrate + seed demo)…"
( cd "$ROOT/backend" && uv run python manage.py migrate && uv run python manage.py seed )

# --- Ctrl+C / cierre: detiene todo el grupo de procesos (ambos servidores) ---
trap 'trap - INT TERM; echo; echo "⏹  Deteniendo servidores…"; kill 0' INT TERM

# --- Backend :8800 -----------------------------------------------------------
echo "▶ Backend  → http://localhost:8800   (API docs: /api/docs · admin: /admin)"
( cd "$ROOT/backend" && exec uv run python manage.py runserver 127.0.0.1:8800 ) &

# --- Frontend :3300 (pnpm dev ya está pineado a --port 3300) ------------------
echo "▶ Frontend → http://localhost:3300"
( cd "$ROOT/frontend" && exec pnpm dev ) &

echo "▶ Listo. Abre http://localhost:3300  ·  Ctrl+C para detener ambos."
wait
