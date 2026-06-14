# Veredicto: APROBADO

Review de **F016 — API detalle de producto + historial** (`GET /api/products/{id}`).
Capas: backend + frontend (contrato). No toca e2e. Entorno MVP: SQLite, sin Docker,
sin jq (Fase 0/2 reportan PENDIENTE, no fallo).

Toda la evidencia de abajo fue **regenerada por el reviewer**, no copiada de los
informes de implementer. `./init.sh` (modo full) terminó **VERDE: 0 fallos** y la
**Fase 5 (contrato) quedó verde sin drift**.

---

## Criterios de `specs/F016-api-detalle-producto.md`

| # | Criterio | Estado | Evidencia (comando / archivo) |
|---|----------|--------|-------------------------------|
| 1 | `GET /api/products/{id}?zone_id=<MTY>` devuelve canónico con `specs`, `prices` por retailer (última obs) e `history` con varias lecturas ordenadas `-captured_at` | **CUMPLE** | Probe vía `manage.py shell` con seed: `STATUS 200`, `KEYS ['canonical_product','history','prices']`, `SPECS {'calibre':'#3','diametro':'3/8"','longitud_m':12}`, `N_PRICES 2 SLUGS ['construrama','home-depot']`, `N_HISTORY 6`, `ORDER_DESC_OK True`. Implementación: `services.detalle_producto()` + `_historial()` (`order_by("-captured_at")[:n]`) en `backend/apps/catalog/services.py:123-195` |
| 2 | Producto inexistente → 404; zona inexistente/inactiva → 404 | **CUMPLE** | Probe: `404_PRODUCTO 404`, `404_ZONA 404`. Service devuelve `None` (zona inactiva: `Zone.objects.filter(id=..., is_active=True)`; canónico inactivo: `filter(id=..., is_active=True)`), router traduce a `HttpError(404)` en `backend/apps/catalog/api.py:40-42` |
| 3 | Router sin ORM; `response=` explícito; lógica en services | **CUMPLE** | Grep ORM en `backend/apps/*/api.py` → VACÍO (exit 1). `grep response=ProductDetailOut api.py` → `33:@router.get("/products/{id}", response=ProductDetailOut)`. Toda la lógica (querysets, ensamblado, orden) en `services.py` |
| 4 | Tests: happy path (detalle + history no vacío) + 404 producto + 404 zona; fallarían sin la implementación | **CUMPLE** | `uv run pytest apps/catalog/tests/test_detalle.py -v` → **5 passed**. Cubre happy path, 404 producto inexistente, 404 producto inactivo, 404 zona inexistente, 404 zona inactiva. No vacuos: aseveran precios sembrados exactos (`"198.50"`/`"191.00"`), set exacto de keys, `len(history)==6` y orden descendente — fallarían contra endpoint ausente o stub (regla del git-stash mental de `docs/verification.md`) |
| 5 | `openapi.json` contiene `/api/products/{id}`, `ProductDetailOut`, `PriceHistoryPointOut`; sin drift (Fase 5 verde; `pnpm gen:api` + `git diff` → sin cambios) | **CUMPLE** | `grep` en `backend/openapi.json`: `148: "/api/products/{id}"`, `381: CanonicalProductDetailOut`, `416: PriceHistoryPointOut`, `451: ProductDetailOut`. Drift: SHA256 de `schema.d.ts` idéntico antes/después de re-`gen:api` (`18ae78ed…f00cb6` == `18ae78ed…f00cb6`) → SIN DRIFT. Fase 5 de init.sh: `✔ tipos TS sincronizados con backend/openapi.json` |
| 6 | Frontend: `fetch` solo en client.ts, cero `any`; tsc/lint/build/test:unit limpios | **CUMPLE** | Grep `fetch(` fuera de `lib/api/client.ts` → VACÍO (exit 1). Grep `: any`/`as any` en `frontend/src` → VACÍO (exit 1). init.sh Fase 4: `✔ tsc --noEmit`, `✔ lint`, `✔ tests unitarios (vitest)`, `✔ build de producción` |

---

## CHECKPOINTS.md

### Global
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `./init.sh` verde de punta a punta | **CUMPLE** | Resumen: `✔ 31 ok ✘ 0 fallos ◌ 4 pendientes — VERDE` |
| Exactamente la feature actual `in_progress`; ninguna otra cambió | **CUMPLE** | `feature_list.json`: `in_progress count: 1`, `ids: F016`. Fase 1: `✔ features in_progress: 1` |
| `progress/impl_<id>_<capa>.md` por capa tocada, con output real | **CUMPLE** | `impl_F016_backend.md` + `impl_F016_frontend.md` presentes con outputs verificables (reproducidos por el reviewer) |
| Cumple su spec, criterio por criterio | **CUMPLE** | Tabla de spec arriba: 6/6 CUMPLE |

### Backend
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `uv run pytest` pasa; tests nuevos que fallarían sin la implementación | **CUMPLE** | init.sh Fase 3: `✔ pytest`. Suite F016: 5 passed; no vacuos (ver criterio 4) |
| `makemigrations --check --dry-run` limpio | **CUMPLE** | `No changes detected` (reviewer, independiente) |
| `ruff check .` limpio | **CUMPLE** | init.sh Fase 3: `✔ ruff check` |
| Lógica en `services.py`, no en routers | **CUMPLE** | `detalle_producto()`/`_historial()` en `services.py`; `api.py` solo parsea/delega |
| `api.py` sin ORM; regla de capas pasa | **CUMPLE** | Grep ORM → VACÍO. init.sh Fase 3: `✔ arquitectura: routers (api.py) sin llamadas al ORM` |
| `corsheaders`/`CORS_ALLOWED_ORIGINS` desde env | **NO APLICA** | F016 no toca configuración CORS (heredada de features previas) |
| Si cambió contrato: `openapi.json` regenerado y commiteado | **CUMPLE** | `openapi.json` modificado (en working tree); contiene los 3 schemas + path. Commit es responsabilidad del líder al cerrar |

### Contrato
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `schema.d.ts` regenerado con `pnpm gen:api`, sin drift contra `openapi.json` | **CUMPLE** | SHA256 idéntico antes/después de re-gen → sin drift. init.sh Fase 5: `✔` |
| Frontend no declara a mano tipos de respuesta de API | **CUMPLE** | Único cambio frontend: `schema.d.ts` (generado). `git status` confirma que no hay otros `.ts` tocados. Grep `: any`/`as any` → VACÍO |

### Frontend
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `tsc --noEmit` limpio | **CUMPLE** | init.sh Fase 4: `✔ tsc --noEmit` |
| `lint` limpio | **CUMPLE** | init.sh Fase 4: `✔ lint` |
| `build` pasa | **CUMPLE** | init.sh Fase 4: `✔ build de producción` |
| Componentes shadcn vía CLI/MCP | **NO APLICA** | Feature de contrato puro, sin UI (la UI es F021); ningún componente añadido |
| Todo fetch maneja carga/error | **NO APLICA** | Sin fetch nuevo (sin UI); regenera solo tipos |
| Ningún `fetch(` fuera de `client.ts`; cero `any` | **CUMPLE** | Ambos greps → VACÍO. init.sh Fase 4: `✔ arquitectura: fetch solo en src/lib/api/client.ts` |

### Higiene del arnés
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `feature_list.json` JSON válido, ≤ 1 `in_progress` | **CUMPLE** | Fase 1: `✔ feature_list.json es JSON válido (array)`, `✔ features in_progress: 1` |
| Repo git inicializado (diff ejecutable) | **CUMPLE** | `git rev-parse --is-inside-work-tree` → `true`. Fase 0: `✔ repositorio git inicializado` |

---

## Diff confinado a la capa permitida

`git status --short`:
```
 M backend/apps/catalog/api.py
 M backend/apps/catalog/schemas.py
 M backend/apps/catalog/services.py
 M backend/openapi.json
 M frontend/src/lib/api/schema.d.ts
?? backend/apps/catalog/tests/test_detalle.py
?? progress/impl_F016_backend.md
?? progress/impl_F016_frontend.md
```
Solo `backend/apps/catalog` + `backend/openapi.json` + `frontend/src/lib/api/schema.d.ts`
+ test nuevo + progress/. **Ningún archivo fuera de la capa permitida.**

## Greps deterministas (independientes de git)
```
ORM en backend/apps/*/api.py             -> VACÍO (exit 1)
fetch( fuera de lib/api/client.ts        -> VACÍO (exit 1)
: any | as any en frontend/src           -> VACÍO (exit 1)
```

## Control de drift (reviewer)
```
sha256 schema.d.ts ANTES : 18ae78ed12b2fd32e0457250d49b728799ef4ac5142abf8325e3b6b3d6f00cb6
pnpm exec openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts
sha256 schema.d.ts DESPUÉS: 18ae78ed12b2fd32e0457250d49b728799ef4ac5142abf8325e3b6b3d6f00cb6
=> SIN DRIFT: schema.d.ts idéntico tras re-generar
```

---

## Output REAL de `./init.sh` (modo full) — Fase 5 visible

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
  ✔ las 11 feature(s) 'done' tienen review APROBADO

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

## Output REAL de tests F016 (reviewer)
```
apps\catalog\tests\test_detalle.py .....                                 [100%]
============================== 5 passed in 0.50s ==============================
```

## Probe independiente del endpoint (reviewer, vía manage.py shell + seed)
```
STATUS 200
KEYS ['canonical_product', 'history', 'prices']
SPECS {'calibre': '#3', 'diametro': '3/8"', 'longitud_m': 12}
N_PRICES 2 SLUGS ['construrama', 'home-depot']
N_HISTORY 6
ORDER_DESC_OK True
404_PRODUCTO 404
404_ZONA 404
```

---

## Conclusión

Los 6 criterios de `specs/F016` y todas las secciones aplicables de `CHECKPOINTS.md`
(Global, Backend, Contrato, Frontend, Higiene) **CUMPLEN**, verificados con comandos
re-ejecutados por el reviewer. `./init.sh` VERDE (0 fallos), **Fase 5 sin drift**,
diff confinado a la capa permitida, greps de arquitectura todos VACÍOS, tests no
vacuos. **APROBADO.**
