#!/usr/bin/env bash
# ============================================================================
# init.sh — Verificación ejecutable del arnés fullstack
#
# El arnés no se fía de lo que diga el agente: este script ES la prueba.
# Capas no bootstrapeadas todavía (features F001-F004 pending) se reportan
# como PENDIENTE sin romper el resto.
#
# Uso:
#   ./init.sh           verificación completa (sin E2E)
#   ./init.sh --quick   rápida: sin docker, sin pnpm build
#   ./init.sh --e2e     completa + suite Playwright
# ============================================================================
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

MODE="full"
case "${1:-}" in
  --quick) MODE="quick" ;;
  --e2e)   MODE="e2e" ;;
  "")      ;;
  *) echo "Uso: ./init.sh [--quick|--e2e]"; exit 1 ;;
esac

# --- helpers ----------------------------------------------------------------
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; NC='\033[0m'
PASS=0; FAIL=0; PEND=0
ok()   { printf "  ${GREEN}✔${NC} %s\n" "$1"; PASS=$((PASS+1)); }
bad()  { printf "  ${RED}✘${NC} %s\n" "$1"; FAIL=$((FAIL+1)); }
pend() { printf "  ${YELLOW}◌${NC} %s\n" "$1"; PEND=$((PEND+1)); }
fase() { printf "\n${BLUE}── %s ──${NC}\n" "$1"; }

run() { # run "descripcion" comando...
  local desc="$1"; shift
  if out=$("$@" 2>&1); then
    ok "$desc"
  else
    bad "$desc"
    echo "$out" | tail -n 15 | sed 's/^/      /'
  fi
}

# --- Fase 0: herramientas ----------------------------------------------------
fase "Fase 0 · Herramientas"
# Obligatorias: git (repo) y node (parseo JSON del arnés; siempre en el stack).
for t in git node; do
  command -v "$t" >/dev/null 2>&1 && ok "$t disponible" || bad "$t es obligatorio para el arnés"
done
# Opcionales: jq (node lo cubre), docker (MVP usa SQLite), uv/pnpm (al bootstrapear su capa).
for t in jq uv docker pnpm; do
  command -v "$t" >/dev/null 2>&1 && ok "$t disponible" || pend "$t no encontrado (opcional / al bootstrapear su capa)"
done
# El binario git no basta: el reviewer y el criterio de contrato necesitan un REPO.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  ok "repositorio git inicializado"
else
  bad "no es un repositorio git (corre 'git init && git add -A && git commit' — el diff del reviewer y 'commiteado' dependen de ello)"
fi

# --- Fase 1: invariantes del arnés -------------------------------------------
fase "Fase 1 · Invariantes del arnés"
for f in CLAUDE.md AGENTS.md CHECKPOINTS.md feature_list.json specs/TEMPLATE.md \
         progress/current.md progress/history.md docs/architecture.md docs/verification.md; do
  [ -f "$f" ] && ok "existe $f" || bad "falta $f"
done

# feature_list.json: validación tolerante a herramientas (jq si está; si no, node).
fl_array=0; IN_PROGRESS=0; BAD_STATUS=0; DONE_IDS=""
if command -v jq >/dev/null 2>&1; then
  jq -e 'type == "array"' feature_list.json >/dev/null 2>&1 && fl_array=1
  IN_PROGRESS=$(jq '[.[] | select(.status=="in_progress")] | length' feature_list.json 2>/dev/null)
  BAD_STATUS=$(jq -r '[.[] | select(.status != "pending" and .status != "in_progress" and .status != "done")] | length' feature_list.json 2>/dev/null)
  DONE_IDS=$(jq -r '.[] | select(.status=="done") | .id' feature_list.json 2>/dev/null)
elif command -v node >/dev/null 2>&1; then
  fl_array=$(node -e "try{process.stdout.write(Array.isArray(require('./feature_list.json'))?'1':'0')}catch(e){process.stdout.write('0')}")
  IN_PROGRESS=$(node -e "try{const a=require('./feature_list.json');process.stdout.write(String(a.filter(f=>f.status==='in_progress').length))}catch(e){process.stdout.write('0')}")
  BAD_STATUS=$(node -e "try{const a=require('./feature_list.json');const ok=['pending','in_progress','done'];process.stdout.write(String(a.filter(f=>!ok.includes(f.status)).length))}catch(e){process.stdout.write('0')}")
  DONE_IDS=$(node -e "try{const a=require('./feature_list.json');process.stdout.write(a.filter(f=>f.status==='done').map(f=>f.id).join('\n'))}catch(e){}")
fi

if [ "$fl_array" = "1" ]; then
  ok "feature_list.json es JSON válido (array)"
  if [ "${IN_PROGRESS:-0}" -le 1 ]; then
    ok "features in_progress: $IN_PROGRESS (máximo 1)"
  else
    bad "hay $IN_PROGRESS features in_progress; el arnés exige una a la vez"
  fi
  [ "${BAD_STATUS:-0}" -eq 0 ] && ok "todos los status son válidos" || bad "$BAD_STATUS feature(s) con status inválido"
else
  bad "feature_list.json no es JSON válido (ni jq ni node pudieron leerlo)"
fi

[ -x .claude/hooks/guard-feature.sh ] && ok "hook guard-feature.sh ejecutable" || bad "hook guard-feature.sh no ejecutable (chmod +x)"

# Gate done <- review: toda feature 'done' exige su review APROBADO (mecánico).
# El veredicto debe aparecer cerca del inicio del informe (primeras líneas), tolerando
# un título de markdown antes (p.ej. "# Review F010" en la línea 1, veredicto en la 3).
miss=0; ndone=0
for id in $DONE_IDS; do
  ndone=$((ndone+1))
  if [ -f "progress/review_${id}.md" ] && head -n 6 "progress/review_${id}.md" | grep -qiE "Veredicto:[[:space:]]*APROBADO"; then
    :
  else
    bad "feature $id está 'done' sin 'Veredicto: APROBADO' en las primeras líneas de progress/review_${id}.md"
    miss=$((miss+1))
  fi
done
if [ "$ndone" -eq 0 ]; then
  ok "sin features 'done' que auditar todavía"
elif [ "$miss" -eq 0 ]; then
  ok "las $ndone feature(s) 'done' tienen review APROBADO"
fi

# --- Fase 2: infraestructura --------------------------------------------------
# El MVP corre con SQLite y SIN Docker (decisión del equipo). Esta fase NO
# levanta Docker ni lo exige: Postgres/Redis vía docker-compose.yml son el
# DESTINO de una migración futura, no parte del ciclo de verificación del MVP.
# Por eso Fase 2 NUNCA produce ROJO — a lo sumo queda 'pendiente' (amarillo).
# (Intentar `docker compose up` aquí daba falsos rojos cuando los puertos
# 5432/6379 estaban ocupados por otros proyectos o el daemon no corría, pese a
# que la infra ni se usa en el MVP.)
fase "Fase 2 · Infraestructura (Postgres + Redis — opcional, migración futura)"
pend "Docker no usado en el MVP (backend corre con SQLite); infra Postgres/Redis diferida a una migración futura"

# --- Fase 3: backend -----------------------------------------------------------
fase "Fase 3 · Backend (Django + Ninja)"
if [ -f backend/manage.py ]; then
  cd backend
  run "uv sync (dependencias)" uv sync --quiet
  run "ruff check" uv run ruff check .
  run "migraciones al día (makemigrations --check)" \
      uv run python manage.py makemigrations --check --dry-run
  run "pytest" uv run pytest -q
  # Arquitectura limpia: ninguna llamada al ORM en los routers (api.py).
  # Nota: `.delete()` del ORM (parens vacíos) se distingue del decorador Ninja
  # `@router.delete("/ruta")`; además se filtran las líneas de decoradores HTTP
  # (get/post/put/patch/delete) para no dar falsos positivos. import-linter es la
  # garantía autoritativa (api no importa models); este grep es backup heurístico.
  api_files=$(find apps -name api.py 2>/dev/null)
  if [ -n "$api_files" ]; then
    orm_hits=$(echo "$api_files" | xargs grep -nE '\.objects\b|\.save\(|\.filter\(|\.create\(|\.delete\(\s*\)' 2>/dev/null \
      | grep -vE '@?(router|api)\.(get|post|put|patch|delete)\(' || true)
    if [ -n "$orm_hits" ]; then
      bad "arquitectura: posible llamada al ORM en apps/*/api.py (la lógica va en services.py)"
      echo "$orm_hits" | tail -n 10 | sed 's/^/      /'
    else
      ok "arquitectura: routers (api.py) sin llamadas al ORM"
    fi
  fi
  cd "$ROOT"
else
  pend "backend sin bootstrapear (feature F001 pending)"
fi

# --- Fase 4: frontend -----------------------------------------------------------
fase "Fase 4 · Frontend (Next.js + Tailwind + shadcn)"
if [ -f frontend/package.json ]; then
  cd frontend
  run "pnpm install" pnpm install --silent
  run "tsc --noEmit" pnpm exec tsc --noEmit
  run "lint" pnpm lint
  # Unit tests de frontend (vitest), solo si el script test:unit está definido.
  if node -e "process.exit(((require('./package.json').scripts)||{})['test:unit']?0:1)" 2>/dev/null; then
    run "tests unitarios (vitest)" pnpm test:unit
  else
    pend "sin script test:unit todavía (lo añade F002)"
  fi
  if [ "$MODE" != "quick" ]; then
    run "build de producción" pnpm build
  else
    pend "build saltado en modo --quick"
  fi
  # Arquitectura limpia: ningún fetch fuera de src/lib/api/client.ts.
  if [ -d src ]; then
    stray=$(grep -rnE "\bfetch\(" src --include=*.ts --include=*.tsx 2>/dev/null | grep -v "lib/api/client.ts" || true)
    if [ -n "$stray" ]; then
      bad "arquitectura: hay fetch( fuera de src/lib/api/client.ts"
      echo "$stray" | tail -n 10 | sed 's/^/      /'
    else
      ok "arquitectura: fetch solo en src/lib/api/client.ts"
    fi
  fi
  cd "$ROOT"
else
  pend "frontend sin bootstrapear (feature F002 pending)"
fi

# --- Fase 5: contrato ------------------------------------------------------------
fase "Fase 5 · Contrato OpenAPI → tipos TS"
if [ -f backend/openapi.json ] && [ -f frontend/package.json ]; then
  if [ -f frontend/src/lib/api/schema.d.ts ]; then
    cd frontend
    if pnpm exec openapi-typescript ../backend/openapi.json -o /tmp/schema.check.d.ts >/dev/null 2>&1 \
       && diff -q /tmp/schema.check.d.ts src/lib/api/schema.d.ts >/dev/null 2>&1; then
      ok "tipos TS sincronizados con backend/openapi.json"
    else
      bad "drift de contrato: corre 'pnpm gen:api' en frontend y commitea"
    fi
    cd "$ROOT"
  else
    bad "existe backend/openapi.json pero no frontend/src/lib/api/schema.d.ts (corre pnpm gen:api)"
  fi
else
  pend "pipeline de contrato sin configurar (feature F003 pending)"
fi

# --- Fase 6: E2E -----------------------------------------------------------------
fase "Fase 6 · E2E (Playwright)"
if [ "$MODE" != "e2e" ]; then
  pend "saltada (usa ./init.sh --e2e para correrla)"
elif [ -f e2e/package.json ]; then
  cd e2e
  run "pnpm install" pnpm install --silent
  run "suite Playwright" pnpm test:e2e
  cd "$ROOT"
else
  pend "e2e sin bootstrapear (feature F004 pending)"
fi

# --- Resumen ----------------------------------------------------------------------
printf "\n${BLUE}════════ Resumen ════════${NC}\n"
printf "  ${GREEN}✔ %d ok${NC}   ${RED}✘ %d fallos${NC}   ${YELLOW}◌ %d pendientes${NC}\n" "$PASS" "$FAIL" "$PEND"
if [ "$FAIL" -eq 0 ]; then
  printf "  ${GREEN}VERDE${NC} — el arnés está en estado consistente.\n\n"
  exit 0
else
  printf "  ${RED}ROJO${NC} — corrige los fallos antes de continuar. Nada está 'hecho' en rojo.\n\n"
  exit 1
fi
