# Veredicto: APROBADO

Review de **F018 — API de retailers (interno, `GET /api/retailers`)** contra
`specs/F018-api-retailers.md` y `CHECKPOINTS.md` (Global + Backend + Contrato +
Frontend + Higiene). Capas tocadas: backend + frontend (no e2e). Verificación
re-ejecutada por el reviewer; el output de `./init.sh` (modo full) es el de esta
corrida, no el del implementer.

## Criterios de la spec

| # | Criterio | Estado | Evidencia (comando/archivo) |
|---|----------|--------|------------------------------|
| 1 | `GET /api/retailers` con `seed` devuelve Home Depot y Construrama como `RetailerOut[]` con `scraper_status`, `pricing_model`, `is_active`, orden por `name` | **CUMPLE** | `seed_demo()` + `TestClient(router).get('/retailers')` → STATUS 200, COUNT 2, NAMES_ORDER `['Construrama', 'Home Depot']` (orden por name), cada item con keys `id, is_active, name, pricing_model, scraper_status, slug`. Home Depot=`zone_cookie`/`active`, Construrama=`distributor_subpath`/`active`. Seed: `backend/apps/core/services.py:92-110` |
| 2 | Router `apps/geo/api.py` SIN ORM (lógica en services); `response=` explícito | **CUMPLE** | `backend/apps/geo/api.py:22-25` → `@router.get("/retailers", response=list[RetailerOut])` delega en `services.listar_retailers()`. ORM (`Retailer.objects.order_by("name")`) vive en `services.py:50-58`. Grep ORM en `apps/*/api.py` (patrón corregido) → VACIO. Fase 3 init.sh: "arquitectura: routers (api.py) sin llamadas al ORM" ✔ |
| 3 | Test del endpoint (≥2 retailers, campos, orden); fallaría sin la implementación | **CUMPLE** | `backend/apps/geo/tests/test_retailers_api.py` (2 tests): `test_listar_retailers_todos_ordenados_por_nombre` (3 retailers incl. inactivo, orden por name) y `test_listar_retailers_shape_y_valores` (shape exacto + valores). `uv run pytest apps/geo/tests/test_retailers_api.py` → 2 passed. Stash mental: TestClient sobre ruta inexistente lanza `Exception: Cannot resolve "/..."` (sin ruta el test no llega a 200); sin `order_by("name")` falla el assert de orden. Test significativo. |
| 4 | `openapi.json` contiene `/api/retailers` y `RetailerOut`; sin drift (Fase 5 verde; `pnpm gen:api` + diff schema.d.ts sin cambios de hash) | **CUMPLE** | `backend/openapi.json:59` (`"/api/retailers"` GET → array `$ref RetailerOut`), `:677-715` (`RetailerOut`, required `[id,name,slug,pricing_model,scraper_status,is_active]`, tipos string/boolean). `frontend/src/lib/api/schema.d.ts:47,261-274`. `pnpm gen:api` antes/después → SHA-256 idéntico (`f7eadda…454f5`). Fase 5 init.sh: "tipos TS sincronizados con backend/openapi.json" ✔ |
| 5 | Frontend: `fetch` solo en client.ts, cero `any`; tsc/lint/build/test:unit limpios | **CUMPLE** | Grep `\bfetch\(` fuera de client.ts → VACIO; grep `: any`/`as any` en frontend/src → VACIO. `frontend/src/features/retailers/api.ts` envuelve `apiGet("/api/retailers")` (tipo inferido del contrato). Fase 4 init.sh: tsc ✔, lint ✔, vitest ✔, build ✔, "fetch solo en src/lib/api/client.ts" ✔ |

## CHECKPOINTS.md

### Global
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `./init.sh` verde de punta a punta | **CUMPLE** | Resumen: 31 ok, 0 fallos, 4 pendientes (Fase 0 jq/docker, Fase 2 infra, Fase 6 e2e) → VERDE |
| Exactamente la feature actual `in_progress`; ninguna otra cambió | **CUMPLE** | `feature_list.json`: F018 `in_progress` (único); Fase 1: "features in_progress: 1 (máximo 1)" ✔ |
| `progress/impl_<id>_<capa>.md` por capa, con output real | **CUMPLE** | `progress/impl_F018_backend.md`, `progress/impl_F018_frontend.md` presentes con outputs |
| Cumple cada criterio de la spec | **CUMPLE** | Tabla de criterios arriba |

### Backend
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `uv run pytest` pasa; tests nuevos que fallarían sin la impl | **CUMPLE** | Fase 3: pytest ✔; test nuevo verificado (criterio 3) |
| `makemigrations --check --dry-run` limpio | **CUMPLE** | Fase 3: "migraciones al día (makemigrations --check)" ✔ (sin migración nueva: `is_active`/campos heredados de modelos existentes) |
| `ruff check .` limpio | **CUMPLE** | Fase 3: "ruff check" ✔ |
| Lógica en `services.py`, no en routers | **CUMPLE** | `services.py:38-58` (`_retailer_to_out`, `listar_retailers`); router delega |
| `api.py` sin ORM; regla de capas | **CUMPLE** | Grep ORM VACIO; Fase 3 arquitectura ✔ |
| Si cambió contrato: `openapi.json` regenerado | **CUMPLE** | `openapi.json` con `/api/retailers` + `RetailerOut`; modificado en git status |

### Contrato
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `schema.d.ts` regenerado sin drift | **CUMPLE** | SHA-256 idéntico tras `pnpm gen:api`; Fase 5 ✔ |
| Frontend no declara tipos de API a mano | **CUMPLE** | `features/retailers/api.ts` infiere de `apiGet`; `schema.d.ts:261` deriva `RetailerOut` del contrato |

### Frontend
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `tsc --noEmit` limpio | **CUMPLE** | Fase 4 ✔ |
| `lint` limpio | **CUMPLE** | Fase 4 ✔ |
| `build` pasa | **CUMPLE** | Fase 4 ✔ |
| shadcn por CLI (no a mano) | **NO APLICA** | F018 no añade componentes UI (alcance: solo paso de contrato) |
| Todo fetch maneja carga/error | **NO APLICA** | Sin UI; el único fetch (client.ts) ya normaliza red/status a `ApiError` |
| Ningún `fetch(` fuera de client.ts; cero `any` | **CUMPLE** | Greps VACIO; Fase 4 arquitectura ✔ |

### Higiene del arnés
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `feature_list.json` JSON válido, ≤1 `in_progress` | **CUMPLE** | Fase 1 ✔ |
| Toda feature `done` tiene review APROBADO | **CUMPLE** | Fase 1: "las 13 feature(s) 'done' tienen review APROBADO" ✔ |
| Repo git inicializado | **CUMPLE** | Fase 0: "repositorio git inicializado" ✔ |

## Diff confinado a la capa permitida

`git status --short` muestra solo:
```
 M backend/apps/geo/api.py
 M backend/apps/geo/schemas.py
 M backend/apps/geo/services.py
 M backend/openapi.json
 M frontend/src/lib/api/schema.d.ts
?? backend/apps/geo/tests/test_retailers_api.py
?? frontend/src/features/retailers/
?? progress/impl_F018_backend.md
?? progress/impl_F018_frontend.md
```
Todo dentro de `backend/` (apps/geo + openapi.json), `frontend/` (schema.d.ts +
features/retailers) y `progress/`. Ningún archivo fuera de la capa permitida.

## Greps deterministas (independientes de git)

```
ORM en apps/*/api.py (patrón corregido)  → VACIO
fetch( fuera de client.ts                → VACIO
: any / as any en frontend/src           → VACIO
```

## Verificación manual del endpoint (seed + TestClient)

```
STATUS 200
COUNT 2
NAMES_ORDER ['Construrama', 'Home Depot']
ITEM {"id": "...", "name": "Construrama", "slug": "construrama", "pricing_model": "distributor_subpath", "scraper_status": "active", "is_active": true}
ITEM {"id": "...", "name": "Home Depot", "slug": "home-depot", "pricing_model": "zone_cookie", "scraper_status": "active", "is_active": true}
KEYS ['id', 'is_active', 'name', 'pricing_model', 'scraper_status', 'slug']
```

## Control de drift (pnpm gen:api)

```
before: f7eadda1b4d8620c518b1149c4026e4207023d470a690f7680c4235e599454f5
after:  f7eadda1b4d8620c518b1149c4026e4207023d470a690f7680c4235e599454f5
→ hash idéntico tras regenerar = SIN DRIFT
```

## Output REAL de `./init.sh` (modo full, sin --e2e)

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
  ✔ las 13 feature(s) 'done' tienen review APROBADO

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

## Conclusión

Todos los criterios de la spec y todas las secciones aplicables de
`CHECKPOINTS.md` se cumplen. `./init.sh` VERDE (0 fallos); **Fase 5 (contrato)
verde sin drift** (hash idéntico tras `pnpm gen:api`). Greps de arquitectura
VACIOS. Diff confinado a las capas permitidas. Las pendientes (jq/docker, infra
Postgres/Redis, e2e) son esperadas en MVP (SQLite/sin-Docker/sin-jq) y no
constituyen fallos. **APROBADO.**
