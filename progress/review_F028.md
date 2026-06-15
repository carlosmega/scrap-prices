# Review F028 — Seed: código real de tienda HD Monterrey (external_id 1333)

**Veredicto: APROBADO**

Capa única backend (no toca contrato). Verificación re-ejecutada por el reviewer
(no se aceptó el output del implementer como evidencia). `./init.sh` modo full,
SQLite/sin-Docker/sin-jq. Fase 5 (contrato) sin cambios.

## Criterios de la spec (specs/F028-seed-store-real-hd.md)

| # | Criterio | Estado | Evidencia (reviewer) |
|---|----------|--------|----------------------|
| 1 | Tras `seed`, la `RetailerLocation` de HD en Monterrey tiene `external_id="1333"` (no `store-2034`) | CUMPLE | `shell -c "...RetailerLocation.objects.get(retailer__slug='home-depot', city='Monterrey').external_id"` → `external_id = 1333` |
| 2 | **Idempotencia (CRÍTICO):** 2 corridas de `seed` → exactamente 1 RetailerLocation de HD (sin huérfana `store-2034`) | CUMPLE | Tras 2ª corrida: `RetailerLocation.objects.filter(retailer__slug='home-depot').count()` → `count HD = 1`. Caso legacy probado por el reviewer: insertada fila con `store-2034` → re-seed → `DESPUES count = 1 ext = ['1333']` (actualiza en sitio, no deja huérfana) |
| 3 | El test de idempotencia cubre el caso huérfano | CUMPLE | `test_seed.py:139-142`: `hd_locs.count() == 1` y `hd_locs.get().external_id == "1333"` dentro de `test_seed_es_idempotente` (2 corridas) |
| 4 | El `ZoneLocationMap` primario sigue apuntando a la location de HD | CUMPLE | `shell -c "...ZoneLocationMap.objects.get(is_primary=True)..."` → `primary -> home-depot | external_id 1333 | city Monterrey` |
| 5 | `ruff` limpio | CUMPLE | `uv run ruff check .` → `All checks passed!` (y Fase 3 de init.sh ✔) |
| 6 | `pytest` verde | CUMPLE | `uv run pytest apps/core/tests/test_seed.py -q` → 3 passed; suite completa verde en Fase 3 de init.sh |
| 7 | `makemigrations --check` limpio | CUMPLE | `uv run python manage.py makemigrations --check --dry-run` → `No changes detected` |
| 8 | Contrato OpenAPI sin cambios | CUMPLE | `git status`: `backend/openapi.json` no aparece; F028 no toca schemas/rutas; Fase 5 de init.sh ✔ tipos sincronizados |

## CHECKPOINTS.md

### Global
- `./init.sh` verde de punta a punta: CUMPLE (31 ok, 0 fallos, 4 pendientes esperados).
- Solo F028 pasó a revisión; ninguna otra cambió de estado: CUMPLE (`feature_list.json`: 1 `in_progress` = F028).
- Existe `progress/impl_F028_backend.md` con output real: CUMPLE.
- Cumple cada criterio de la spec uno por uno: CUMPLE (tabla arriba).

### Backend
- `pytest` pasa; trae tests que fallarían sin la implementación: CUMPLE. Git-stash mental: `test_seed.py:58` (`assert hd_loc.external_id == "1333"`) y `:142` fallarían con el placeholder `store-2034`. El test de idempotencia distingue "1 fila actualizada" de "1 huérfana + 1 nueva".
- `makemigrations --check` limpio: CUMPLE (F028 no toca modelos, correcto).
- `ruff check .` limpio: CUMPLE.
- Lógica de negocio en `services.py`, no en routers: CUMPLE (cambio confinado a `seed_demo` en `apps/core/services.py`).
- **Arquitectura:** `api.py` sin ORM: CUMPLE. Grep arroja solo decoradores `@router.delete(...)` (HTTP de Ninja) en `apps/lists/api.py:92,149`, falsos positivos que init.sh filtra; el grep filtrado da VACÍO.
- `corsheaders` desde env: N/A (F028 no toca config; verde en features previas).
- Contrato regenerado: N/A (no cambió).

### Higiene del arnés
- `feature_list.json` JSON válido con ≤1 `in_progress`: CUMPLE (1: F028).
- Toda feature `done` tiene review APROBADO: CUMPLE (Fase 1: "las 24 feature(s) 'done' tienen review APROBADO").
- Repo git inicializado: CUMPLE (Fase 0 ✔).

## Diff revisado (capa permitida)

`git status --short`:
```
 M backend/apps/core/services.py
 M backend/apps/core/tests/test_seed.py
?? progress/impl_F028_backend.md
```
Solo `backend/apps/core` + `progress/`. `backend/openapi.json` NO cambia. Diff total:
`services.py` +8 líneas (clave `update_or_create` re-keyeada a `(retailer, name)`,
`external_id="1333"` movido a `defaults`, comentario explicativo) y `test_seed.py`
+10 líneas (asserts de `1333`/city/state + caso idempotencia). Nada fuera de la capa
backend permitida.

## Greps de arquitectura (deterministas)

- ORM en routers (`grep -rnE "\.objects|\.save\(|\.filter\(|\.create\(|\.delete\(" backend/apps/*/api.py` + filtro de decoradores HTTP de init.sh): VACÍO.
- Frontend / e2e: N/A (F028 es capa única backend; no se tocó `frontend/` ni `e2e/`).

## Notas no bloqueantes

- La clave de lookup `(retailer, name)` no está respaldada por `unique_together` en
  `RetailerLocation` (el único `unique_together` del módulo geo es `(zone, retailer_location)`
  en `ZoneLocationMap`). Funciona porque el seed usa nombres únicos por retailer y la spec
  no exige constraint. El implementer lo documentó como deuda en `impl_F028_backend.md`.
  No bloquea F028.

## Output real de `./init.sh` (modo full)

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
  ✔ las 24 feature(s) 'done' tienen review APROBADO

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

## Verificaciones funcionales del seed (output real del reviewer)

```
=== external_id de HD Monterrey ===
external_id = 1333
=== count HD == 1 (tras 2 corridas) ===
count HD = 1
=== ZoneLocationMap primario ===
primary -> home-depot | external_id 1333 | city Monterrey
=== Escenario DB legacy (store-2034 -> re-seed) ===
ANTES count = 1 ext = store-2034
--- re-seed sobre DB legacy ---
  locations: 2
DESPUES count = 1 ext = ['1333']
=== pytest apps/core/tests/test_seed.py ===
3 passed
=== makemigrations --check ===
No changes detected
=== ruff check . ===
All checks passed!
```
