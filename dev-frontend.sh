#!/usr/bin/env bash
# Levanta el frontend de ConstruScan en el puerto fijo local 3300 (F023).
# El script `dev` de package.json ya está pineado a --port 3300.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT/frontend"
exec pnpm dev
