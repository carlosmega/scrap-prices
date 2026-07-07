#!/usr/bin/env bash
# ============================================================================
# guard-feature.sh — Hook PreToolUse (Edit|Write|MultiEdit)
#
# Hace cumplir DOS invariantes del arnés por mecánica, no por prompt:
#   1. No se toca código de backend/, frontend/ ni e2e/ a menos que exista
#      EXACTAMENTE una feature "in_progress" en feature_list.json.
#   2. Solo se editan capas DENTRO del alcance de esa feature: si la feature
#      in_progress no declara la capa en sus 'capas', se bloquea (separación
#      de capas: el implementer-backend no toca frontend/, etc.).
#
# Estrategia: se detecta si el archivo pertenece a una CAPA de código por su
# segmento de ruta (*/backend/*, */frontend/*, */e2e/*), insensible a la forma
# de la ruta (Windows '\' vs POSIX '/').
#   - Si NO es de una capa -> es archivo del arnés (specs/, docs/, progress/,
#     raíz, .claude/, y los CLAUDE.md por capa) -> siempre editable.
#   - Si SÍ es de una capa -> aplica los dos invariantes.
# Cierra el hueco de 'backend/docs/x.py' (la allowlist anclada anterior fallaba
# por desajuste de forma de ruta entre CLAUDE_PROJECT_DIR y file_path).
#
# Diseño defensivo:
#   - FAIL-CLOSED: si no se puede evaluar feature_list.json (jq ausente Y JSON
#     inválido), se BLOQUEA (exit 2), nunca se permite en silencio.
#   - Extracción de file_path sin depender de jq (fallback sed).
#
# LÍMITE CONOCIDO: solo intercepta Edit|Write|MultiEdit. Una escritura vía Bash
# (echo>, tee, sed -i, cp, mv) NO la cubre; ahí la defensa es el set de Bash
# permitido en settings.json + la revisión del reviewer. No es una sandbox.
#
# Protocolo de hooks: exit 0 = permitir; exit 2 = bloquear (stderr -> Claude).
# ============================================================================
set -uo pipefail

INPUT=$(cat)

# --- Extraer file_path SIN depender de jq (para poder fallar-cerrado) --------
if command -v jq >/dev/null 2>&1; then
  FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
else
  FILE=$(printf '%s' "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)
fi

# Sin ruta detectable -> no es una edición de archivo; no bloqueamos.
[ -z "$FILE" ] && exit 0

# Normalizar separadores Windows '\' -> '/' (bs aislado para no pelear con el escape).
bs='\'
F=$(printf '%s' "$FILE" | tr "$bs" '/' 2>/dev/null | tr -s '/')

# --- ¿Pertenece a una CAPA de código? (detección por segmento) ---------------
CAPA=""
case "$F" in
  */backend/CLAUDE.md|*/frontend/CLAUDE.md|*/e2e/CLAUDE.md)
    exit 0 ;;                       # reglas operativas de la capa: archivo del arnés
  */backend/*)  CAPA="backend" ;;
  */frontend/*) CAPA="frontend" ;;
  */e2e/*)      CAPA="e2e" ;;
esac

# No es código de una capa -> archivo del arnés (specs/docs/progress/raíz/.claude):
# siempre editable, el líder abre el alcance antes de que exista una feature.
[ -z "$CAPA" ] && exit 0

# --- A partir de aquí ES código de una capa: aplican los invariantes ---------
LIST="${CLAUDE_PROJECT_DIR:-.}/feature_list.json"
if [ ! -f "$LIST" ]; then
  groot=$(git -C "$(dirname "$FILE")" rev-parse --show-toplevel 2>/dev/null || true)
  [ -n "$groot" ] && LIST="$groot/feature_list.json"
fi
[ -f "$LIST" ] || exit 0

# Contar features in_progress (fail-CLOSED si no se puede evaluar).
if command -v jq >/dev/null 2>&1; then
  N=$(jq '[.[] | select(.status=="in_progress")] | length' "$LIST" 2>/dev/null)
  [ -z "$N" ] && N="X"   # jq falló -> JSON inválido
else
  N=$(grep -oE '"status"[[:space:]]*:[[:space:]]*"in_progress"' "$LIST" 2>/dev/null | wc -l | tr -d ' ')
fi

if [ "$N" = "X" ]; then
  echo "BLOQUEADO por el arnés: no se pudo evaluar feature_list.json (¿jq instalado?, ¿JSON válido?). Se bloquea por seguridad (fail-closed); no se permite editar '$FILE'." >&2
  exit 2
fi

if [ "$N" != "1" ]; then
  echo "BLOQUEADO por el arnés: hay $N features in_progress en feature_list.json (se exige exactamente 1) y estás intentando editar '$FILE'. El líder debe marcar UNA feature como in_progress y actualizar progress/current.md antes de tocar código." >&2
  exit 2
fi

# Validar que la CAPA del archivo esté en las 'capas' de la feature in_progress.
if command -v jq >/dev/null 2>&1; then
  if ! jq -e --arg c "$CAPA" '[.[] | select(.status=="in_progress")][0].capas // [] | index($c)' "$LIST" >/dev/null 2>&1; then
    echo "BLOQUEADO por el arnés: la feature in_progress no declara la capa '$CAPA' en sus 'capas', y estás intentando editar '$FILE'. Solo se editan las capas dentro del alcance de la feature actual (separación de capas)." >&2
    exit 2
  fi
fi

exit 0
