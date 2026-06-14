# Veredicto: APROBADO

Review de **F015 — API de búsqueda (`GET /api/search`)** contra
`specs/F015-api-busqueda.md` y `CHECKPOINTS.md` (Global + Backend + Contrato +
Frontend + Higiene). Todas las verificaciones fueron **re-ejecutadas por el
reviewer**; no se aceptó el output pegado por los implementers.

Capas tocadas: backend + frontend (sin e2e). `./init.sh` corrido en modo full
(NO `--e2e`). Fase 5 (contrato) **VERDE sin drift**.

---

## Criterios de aceptación de la spec (verificación propia)

Verificados con `seed` + `ninja.testing.TestClient(router)` en un test efímero
del reviewer (`apps/catalog/tests/test_zzz_reviewer_f015.py`, **creado, corrido y
eliminado**; git status confirmó que no quedó rastro). No se reusaron los tests
del implementer para juzgar comportamiento.

| # | Criterio (spec F015) | Estado | Evidencia |
|---|----------------------|--------|-----------|
| C1 | `GET /api/search?q=varilla&zone_id=<MTY>` (con seed) → canónicos de varilla, cada uno con Home Depot **y** Construrama, cada precio con `captured_at` | CUMPLE | Reviewer: `C1 num_resultados = 3`; `C1 retailers en item0 = ['construrama','home-depot']`; `C1 captured_at presente en todos los precios = OK` |
| C1b | Usa la **última** observación por retailer/zona (la más reciente por `captured_at`) | CUMPLE | Reviewer inyectó una obs antigua con `price=1.00` (captured_at 2000-01-01) para HD/3-8; la API devolvió `198.50` (la reciente real), NO `1.00`: `C1b usa ultima observacion = OK`. `services._ensamblar_precio` delega en `apps.prices.services.ultima_observacion` (`order_by("-captured_at").first()`) |
| C2a | `q` tolerante a acentos ("várilla" == "varilla") | CUMPLE | Reviewer: `C2a acentos: ids(varilla)==ids(varilla con acento) = True`. `services._normalizar` (NFKD + strip de diacríticos, `casefold`) |
| C2b | `sort=price` ordena por menor precio disponible | CUMPLE | Reviewer: `C2b sort=price menores = ['68.50','191.00','324.50'] | ordenado = True` |
| C2c | Retailer sin observación en la zona → `price=null`, `is_available=false` (y `captured_at=null`) | CUMPLE | Reviewer borró las obs de Construrama para 1/2 en MTY: `C2c retailer-sin-obs: price = None | is_available = False | captured_at = None`. Construrama sigue apareciendo en `prices` con `retailer_product_id` |
| C3a | `zone_id` inexistente → 404 | CUMPLE | Reviewer: `C3a zona inexistente status = 404` |
| C3b | `zone_id` de zona inactiva (`is_active=False`) → 404 | CUMPLE | Reviewer: `C3b zona inactiva status = 404`. `services.buscar` filtra `Zone.objects.filter(id=..., is_active=True)` → `None` → router lanza `HttpError(404)` |
| C4 | Router `apps/catalog/api.py` SIN ORM; lógica en `services.py`; `response=` explícito | CUMPLE | `grep -rnE '\.objects|\.save\(|\.filter\(|\.create\(|\.delete\(' backend/apps/*/api.py` → **VACÍO**. `api.py` solo importa `services` y `schemas`. `@router.get("/search", response=list[SearchResultOut])` (línea 16) |
| C5 | Tests: happy path, orden por precio, retailer-sin-precio, 404, acentos; fallarían sin la implementación | CUMPLE | `apps/catalog/tests/test_search.py` (9 tests) cubre los 5 casos. Acoplados a la implementación: aserciones de valores exactos (`"198.50"`, `"191.00"`), de `status_code == 404`, y de `price is None` que serían falsas con un router stub. Reviewer corrió `uv run pytest apps/catalog -q` → 18 passed |
| C6 | `openapi.json` contiene `/api/search`, `SearchResultOut`, `PriceByRetailerOut` (+ refs); contrato sin drift (`pnpm gen:api`, Fase 5 verde) | CUMPLE | `backend/openapi.json`: `/api/search` (línea 92, params `q`/`zone_id` required, `sort` default `price`), `SearchResultOut`, `PriceByRetailerOut`, `RetailerRefOut`, `CanonicalProductRefOut`. Drift: regen byte-idéntico (sha256 `2393c0f2…` == `2393c0f2…`); Fase 5 VERDE |
| C7 | Frontend: `fetch` solo en `client.ts`, cero `any`; tsc/lint/build/test:unit limpios | CUMPLE | `grep fetch( frontend/src` → solo `lib/api/client.ts:63`. `grep ': any|as any' frontend/src` → **VACÍO**. Fase 4 de init.sh: tsc/lint/vitest/build todos ✔ |
| C8 | `./init.sh` verde; ruff/pytest/tsc/lint/build limpios | CUMPLE | Ver output completo abajo: **31 ok, 0 fallos, 4 pendientes (VERDE)** |

---

## CHECKPOINTS.md punto por punto

### Global
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `./init.sh` verde de punta a punta | CUMPLE | 0 fallos (output abajo) |
| Solo la feature actual cambió de estado | CUMPLE | `feature_list.json`: F015 única `in_progress`; las 10 `done` previas intactas (Fase 1: "las 10 feature(s) 'done' tienen review APROBADO") |
| Existen `progress/impl_<id>_<capa>.md` por capa con output real | CUMPLE | `progress/impl_F015_backend.md` y `progress/impl_F015_frontend.md` con outputs (ruff/pytest/tsc/lint/build) |
| Cumple cada criterio de la spec | CUMPLE | Tabla de criterios arriba |

### Backend
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `pytest` pasa, tests nuevos que fallarían sin la impl | CUMPLE | Fase 3 ✔ pytest; `test_search.py` acoplado a la lógica |
| `makemigrations --check --dry-run` limpio | CUMPLE | Fase 3 ✔ "migraciones al día" |
| `ruff check .` limpio | CUMPLE | Fase 3 ✔ ruff |
| Lógica en `services.py`, no en routers | CUMPLE | `services.py` (búsqueda/ensamblado/orden); `api.py` solo delega |
| `api.py` sin ORM; regla de capas pasa | CUMPLE | Grep ORM VACÍO; Fase 3 ✔ "routers (api.py) sin llamadas al ORM" |
| `corsheaders` con `CORS_ALLOWED_ORIGINS` desde env | NO APLICA / sin regresión | F015 no toca config CORS; ya configurado en features previas; init.sh no reporta fallo |
| Si cambió el contrato: `openapi.json` regenerado | CUMPLE | `openapi.json` modificado con `/api/search` + schemas |

### Contrato
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `schema.d.ts` regenerado y sin drift | CUMPLE | Fase 5 ✔; regen byte-idéntico (sha256 igual) |
| Frontend no declara a mano tipos de la API | CUMPLE | `schema.d.ts` generado por `openapi-typescript`; `grep ': any'` VACÍO; sin tipos a mano |

### Frontend
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `tsc --noEmit` limpio | CUMPLE | Fase 4 ✔ tsc |
| `lint` limpio | CUMPLE | Fase 4 ✔ lint |
| `build` pasa | CUMPLE | Fase 4 ✔ build de producción |
| Componentes shadcn vía CLI en `src/components/ui/` | NO APLICA | F015 es solo contrato (sin UI; la UI es F020). impl_frontend no añadió componentes |
| Todo fetch maneja carga y error | NO APLICA | F015 no añade fetch/UI; `client.ts` (preexistente) maneja errores |
| Ningún `fetch(` fuera de `client.ts`; cero `any` | CUMPLE | Grep `fetch(` → solo `client.ts:63`; grep `any` VACÍO; Fase 4 ✔ "fetch solo en client.ts" |

### Higiene del arnés
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `feature_list.json` JSON válido, ≤1 `in_progress` | CUMPLE | Fase 1 ✔ "in_progress: 1 (máximo 1)" |
| `progress/current.md` refleja la sesión | CUMPLE | Existe (Fase 1 ✔) |
| Toda `done` tiene review APROBADO | CUMPLE | Fase 1 ✔ "las 10 feature(s) 'done' tienen review APROBADO" |
| Repo git inicializado | CUMPLE | Fase 0 ✔ "repositorio git inicializado" |

---

## Diff / alcance (git status — solo capas permitidas)

```
 M backend/config/api.py            (monta catalog_router → /api/search)
 M backend/openapi.json             (+/api/search + 4 schemas)
 M frontend/src/lib/api/schema.d.ts (regenerado)
?? backend/apps/catalog/api.py
?? backend/apps/catalog/schemas.py
?? backend/apps/catalog/services.py
?? backend/apps/catalog/tests/test_search.py
?? progress/impl_F015_backend.md
?? progress/impl_F015_frontend.md
```
Sin archivos fuera de `backend/` (catalog + config/api.py + openapi.json),
`frontend/` (schema.d.ts) y `progress/`. Conforme al alcance de la spec.

## Greps deterministas de arquitectura (independientes de git)

- ORM en `backend/apps/*/api.py`: **VACÍO** (correcto).
- `fetch(` fuera de `client.ts` en `frontend/src`: solo `lib/api/client.ts:63` (correcto).
- `: any` / `as any` en `frontend/src`: **VACÍO** (correcto).

## Drift de contrato (verificación propia)

```
ON-DISK : 2393c0f22cce0b52ab623a9a9589183cf7e4774525fc33cbc2774165264c2a34
REGEN   : 2393c0f22cce0b52ab623a9a9589183cf7e4774525fc33cbc2774165264c2a34
DRIFT: NONE (regenerated == on-disk)
```

---

## Output REAL de `./init.sh` (modo full, corrida del reviewer)

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
  ✔ las 10 feature(s) 'done' tienen review APROBADO

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

Los 4 pendientes (jq, docker, Fase 2, Fase 6) son esperados del entorno MVP
(SQLite / sin-Docker / sin-jq / sin `--e2e`), no fallos. **Fase 5 VERDE.**

## Verificación propia de criterios de la spec (test efímero del reviewer, ya eliminado)

```
Seed demo aplicado (idempotente).
  retailers: 2 | zones: 1 | canonical_products: 3 | retailer_products: 6 | observations: 18
C1 num_resultados = 3
C1 retailers en item0 = ['construrama', 'home-depot']
C1 captured_at presente en todos los precios = OK
C1b precio_actual(esperado, NO el viejo 1.00) = 198.50 | obs reciente real = 198.50
C1b usa ultima observacion = OK
C2a acentos: ids(varilla)==ids(varilla con acento) = True
C2b sort=price menores = ['68.50', '191.00', '324.50'] | ordenado = True
C2c retailer-sin-obs: price = None | is_available = False | captured_at = None
C3a zona inexistente status = 404
C3b zona inactiva status = 404

REVIEWER_F015_ALL_CRITERIA = PASS
```

---

## Notas (no bloqueantes)

- `sort` se acepta como string libre (no `Literal["price","name"]`); valores
  desconocidos caen en el comportamiento `price`. La spec no exige enum; queda
  como posible endurecimiento futuro.
- Búsqueda en SQLite itera canónicos en memoria para tolerar acentos; aceptable
  para el dataset MVP. Postgres FTS (`unaccent`/`SearchVector`) + paginación
  diferidos a M5, como indica la spec.
- Helper `fetchSearch` no añadido en frontend: correcto, el alcance de F015 es
  "solo contrato"; la UI y el soporte de query params en `client.ts` son F020.

**Veredicto final: APROBADO.** Todos los criterios de `specs/F015` y las
secciones aplicables de `CHECKPOINTS.md` se cumplen con evidencia ejecutable;
`./init.sh` VERDE con Fase 5 sin drift.
