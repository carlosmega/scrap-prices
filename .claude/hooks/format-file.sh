#!/usr/bin/env bash
# ============================================================================
# format-file.sh — Hook PostToolUse (Edit|Write|MultiEdit)
#
# Formatea automáticamente el archivo recién editado para que el estilo
# nunca sea tema de discusión entre agentes. Nunca bloquea (siempre exit 0):
# si el formateador no está instalado todavía, simplemente no hace nada.
# ============================================================================
set -uo pipefail

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -z "$FILE" ] || [ ! -f "$FILE" ] && exit 0

case "$FILE" in
  *.py)
    if command -v uv >/dev/null 2>&1 && [ -f "${CLAUDE_PROJECT_DIR:-.}/backend/pyproject.toml" ]; then
      (cd "${CLAUDE_PROJECT_DIR:-.}/backend" && uv run ruff format "$FILE" >/dev/null 2>&1) || true
    fi
    ;;
  *.ts|*.tsx|*.css|*.json)
    if [ -f "${CLAUDE_PROJECT_DIR:-.}/frontend/package.json" ]; then
      (cd "${CLAUDE_PROJECT_DIR:-.}/frontend" && pnpm exec prettier --write "$FILE" >/dev/null 2>&1) || true
    fi
    ;;
esac

exit 0
