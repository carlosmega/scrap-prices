Veredicto: APROBADO

# Review F003 — Pipeline de contrato OpenAPI → tipos TS

Feature: F003 (capas: backend + frontend; sin e2e).
Reviewer: re-ejecución determinista propia (no se confió en los informes de implementers).
Fecha: 2026-06-13.

## Resumen del veredicto

`./init.sh` (modo full) termina **VERDE** (31 ok · 0 fallos · 4 pendientes).
La **Fase 5 (Contrato) quedó VERDE**: `tipos TS sincronizados con backend/openapi.json`
(existen `backend/openapi.json` y `frontend/src/lib/api/schema.d.ts`, sin drift).
Los 4 pendientes son hechos del entorno (jq/docker ausentes → Fase 0/2; e2e fuera de
alcance de esta corrida), no defectos de la feature.

## Criterios de aceptación de specs/F003-contrato-tipos.md

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | `pnpm gen:api` regenera `schema.d.ts` idéntico al commiteado (sin drift) | CUMPLE | Fase 5 de `./init.sh`: `✔ tipos TS sincronizados con backend/openapi.json`. Verificación independiente: regeneré a `/tmp/schema.f003check.d.ts` con `pnpm exec openapi-typescript ../backend/openapi.json` y `diff -q` contra `src/lib/api/schema.d.ts` → `NO DRIFT (identical)`. Script real presente: `frontend/package.json:10` `"gen:api": "openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts"`; dep `openapi-typescript: ^7.13.0`. |
| 2 | Cero tipos de respuesta API declarados a mano (grep lo demuestra) | CUMPLE | `grep -rnE ": any\b\|as any" frontend/src` → VACÍO. Los tipos derivan de `paths` en `schema.d.ts`: `client.ts:14` `import type { paths } from "./schema"`; `apiGet` infiere `GetJson200<P>` del contrato (`client.ts:22-30,57-60`); `features/health/api.ts` no anota tipo de retorno (lo infiere de `apiGet("/api/health")`). `client.ts` usa `as GetJson200<P>` (cast al tipo generado, no `any`). |
| 3 | Home muestra "ok" con backend arriba y error amable cuando no | CUMPLE (parte verificable) | `HealthIndicator` (`health-indicator.tsx`) renderiza 3 estados: `loading` (`status==="loading"`), `error` amable (`"No se pudo conectar con el backend…"`) y `ok` (muestra `health.value`). `use-health.ts` mapea `fetchHealth().then→ok / .catch→error`. `client.ts:71-79` normaliza fallo de red a `ApiError(status 0)`. El camino "ok" real (backend arriba) se ejercita en el E2E de F004; aquí se verifica que el manejo de error y los 3 estados existen. Build prerendea `/` como estático porque el fetch es client-side (no depende del backend). |

## CHECKPOINTS.md — Global

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `./init.sh` verde de punta a punta | CUMPLE | Resumen: `VERDE — 31 ok · 0 fallos · 4 pendientes`. |
| Solo la feature actual cambió de estado (≤1 in_progress) | CUMPLE | `feature_list.json`: F003 `in_progress`; F001/F002 `done`; resto `pending`. Fase 1: `features in_progress: 1 (máximo 1)`. |
| Existe `progress/impl_<id>_<capa>.md` por capa con output real | CUMPLE | `progress/impl_F003_backend.md` y `progress/impl_F003_frontend.md` presentes, con outputs de verificación. |
| Cumple cada criterio de la spec | CUMPLE | Tabla de criterios arriba. |

## CHECKPOINTS.md — Backend (toca esta capa: openapi.json)

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `uv run pytest` pasa | CUMPLE | Fase 3: `✔ pytest`. |
| `makemigrations --check --dry-run` limpio | CUMPLE | Fase 3: `✔ migraciones al día (makemigrations --check)`. |
| `uv run ruff check .` limpio | CUMPLE | Fase 3: `✔ ruff check`. |
| `api.py` sin llamadas al ORM | CUMPLE | Fase 3: `✔ arquitectura: routers (api.py) sin llamadas al ORM`. Grep propio `\.objects\|\.save(\|\.filter(\|\.create(\|\.delete(` en `backend/apps/*/api.py` → VACÍO. |
| Si cambió el contrato: `backend/openapi.json` regenerado y commiteable | CUMPLE | `backend/openapi.json` presente (untracked, listo para commit). Contiene `paths: /api/health`, schema `HealthOut`. |

## CHECKPOINTS.md — Contrato

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `schema.d.ts` regenerado sin drift contra `openapi.json` | CUMPLE | Fase 5 VERDE + diff independiente `NO DRIFT (identical)`. |
| El frontend NO declara a mano tipos de respuesta de API | CUMPLE | Ver criterio #2; todo deriva de `paths`/`schema.d.ts`. |

## CHECKPOINTS.md — Frontend

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `tsc --noEmit` limpio | CUMPLE | Fase 4: `✔ tsc --noEmit`. |
| `pnpm lint` limpio | CUMPLE | Fase 4: `✔ lint`. |
| `pnpm build` pasa | CUMPLE | Fase 4: `✔ build de producción`. |
| shadcn en `src/components/ui/` vía CLI (no a mano) | CUMPLE / N/A | F003 no añadió componentes shadcn (reutiliza Card/Input/Button de F002). |
| Todo fetch maneja carga y error | CUMPLE | `use-health.ts` + `health-indicator.tsx` cubren loading/error/ok; `client.ts` normaliza errores de red y status no-2xx vía `ApiError`. |
| Ningún `fetch(` fuera de `client.ts`; cero `any` | CUMPLE | Fase 4: `✔ arquitectura: fetch solo en src/lib/api/client.ts`. Greps propios: `fetch(` fuera de client.ts → VACÍO; `: any`/`as any` → VACÍO. |

## CHECKPOINTS.md — Higiene del arnés

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `feature_list.json` JSON válido, ≤1 in_progress | CUMPLE | Fase 1: JSON válido + 1 in_progress. |
| Toda feature `done` con review APROBADO | CUMPLE | Fase 1: `las 2 feature(s) 'done' tienen review APROBADO`. |
| Repo inicializado como git | CUMPLE | Fase 0: `✔ repositorio git inicializado` (`git rev-parse --is-inside-work-tree` → true). |

## Diff fuera de capa permitida

`git status --porcelain` confina los cambios a capas permitidas: `backend/openapi.json`,
`frontend/` (`package.json`, `pnpm-lock.yaml`, `src/app/page.tsx`, `src/features/health/`,
`src/lib/api/client.ts`, `src/lib/api/schema.d.ts`) y `progress/`. **Sin archivos tocados
fuera de la capa permitida.**

## Observación menor (no bloqueante)

`frontend/src/app/page.tsx` conserva texto placeholder de F002 ("aún sin consumo de API",
"La búsqueda real se conecta al backend en F003") que ya no refleja el estado: la home SÍ
consume `/api/health` vía `<HealthIndicator />`. Es cosmético, no afecta ningún criterio de
aceptación ni checkpoint. No motiva rechazo.

## Output real de `./init.sh` (modo full, Fase 5 visible)

```
── Fase 0 · Herramientas ──
  ✔ git disponible
  ✔ node disponible
  ◌ jq no encontrado (opcional / al bootstrapear su capa)
  ✔ uv disponible
  ◌ docker no encontrado (opcional / al bootstrapear su capa)
  ✔ pnpm disponible
  ✔ repositorio git inicializado

── Fase 1 · Invariantes del arnés ──
  ✔ existe CLAUDE.md
  ✔ existe AGENTS.md
  ✔ existe CHECKPOINTS.md
  ✔ existe feature_list.json
  ✔ existe specs/TEMPLATE.md
  ✔ existe progress/current.md
  ✔ existe progress/history.md
  ✔ existe docs/architecture.md
  ✔ existe docs/verification.md
  ✔ feature_list.json es JSON válido (array)
  ✔ features in_progress: 1 (máximo 1)
  ✔ todos los status son válidos
  ✔ hook guard-feature.sh ejecutable
  ✔ las 2 feature(s) 'done' tienen review APROBADO

── Fase 2 · Infraestructura (Postgres + Redis — opcional, migración futura) ──
  ◌ Docker no usado en MVP (backend corre con SQLite); infra Postgres/Redis diferida

── Fase 3 · Backend (Django + Ninja) ──
  ✔ uv sync (dependencias)
  ✔ ruff check
  ✔ migraciones al día (makemigrations --check)
  ✔ pytest
  ✔ arquitectura: routers (api.py) sin llamadas al ORM

── Fase 4 · Frontend (Next.js + Tailwind + shadcn) ──
  ✔ pnpm install
  ✔ tsc --noEmit
  ✔ lint
  ✔ tests unitarios (vitest)
  ✔ build de producción
  ✔ arquitectura: fetch solo en src/lib/api/client.ts

── Fase 5 · Contrato OpenAPI → tipos TS ──
  ✔ tipos TS sincronizados con backend/openapi.json

── Fase 6 · E2E (Playwright) ──
  ◌ saltada (usa ./init.sh --e2e para correrla)

════════ Resumen ════════
  ✔ 31 ok   ✘ 0 fallos   ◌ 4 pendientes
  VERDE — el arnés está en estado consistente.
```

## Verificaciones deterministas adicionales (output real)

```
=== fetch( fuera de client.ts ===
VACIO
=== : any / as any en frontend/src ===
VACIO
=== ORM en backend/apps/*/api.py ===
VACIO
=== drift check independiente ===
NO DRIFT (identical)   # pnpm exec openapi-typescript ../backend/openapi.json -o /tmp -> diff -q vs src/lib/api/schema.d.ts
=== gen:api script + dep ===
frontend/package.json:10  "gen:api": "openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts"
frontend/package.json:38  "openapi-typescript": "^7.13.0"
```
