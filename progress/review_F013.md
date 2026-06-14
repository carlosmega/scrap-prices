# Veredicto: APROBADO

Review de **F013 — Seed de datos demo (Monterrey Metro · varilla)**.
Capa única: backend. Verificación re-ejecutada por el reviewer (no parafraseada).

Entorno MVP: SQLite / sin Docker / sin jq. Fases 0/2 con pendientes esperados
(no fallos). Fase 5 (contrato) VERDE sin cambios: F013 no añade endpoints.

---

## Tabla criterio → estado → evidencia

### Criterios de `specs/F013-seed-datos-demo.md`

| # | Criterio | Estado | Evidencia (comando / archivo) |
|---|----------|--------|-------------------------------|
| 1 | `manage.py seed` corre limpio y es **idempotente** (2ª corrida no duplica) | **CUMPLE** | Dos corridas reales (abajo): conteos idénticos, `observations_created: 0` en ambas (DB ya sembrada). El test `test_seed_es_idempotente` prueba `primera == segunda` sobre DB limpia. |
| 2 | Conteos: 2 Retailer, ≥2 RetailerLocation, 1 Zone "Monterrey Metro", ZoneLocationMap, 1 Category, ≥3 CanonicalProduct, RetailerProduct ambos retailers, ≥2 PriceObservation por rp×zona | **CUMPLE** | Salida `seed`: retailers=2, locations=2, zones=1, zone_maps=2, categories=1, canonical_products=3, retailer_products=6, observations=18 (= 6 rp × 3 capturas → 3 ≥ 2 por rp×zona). `test_seed_crea_el_grafo_de_la_spec` asserta cada uno. |
| 3 | Test ejecuta `call_command("seed")`, verifica conteos + `services.ultima_observacion` (la más reciente) + idempotencia; fallaría sin el command | **CUMPLE** | `apps/core/tests/test_seed.py` (3 tests). Prueba "git stash mental" ejecutada: con `seed.py` movido, los 3 tests fallan con `CommandError: Unknown command: 'seed'` (salida abajo). `test_seed_crea_historial_y_ultima_observacion` asserta `ultima == obs.last()`. |
| 4 | `ruff check` limpio; `makemigrations --check --dry-run` limpio (no modelos nuevos) | **CUMPLE** | `ruff check .` → "All checks passed!"; `makemigrations --check --dry-run` → "No changes detected" (exit 0). |
| 5 | `PriceObservation` sembrado: `raw_payload={"seed": true}`, price Decimal, currency MXN | **CUMPLE** | `services.py` L185-199: `price=base+delta` (Decimal), `currency="MXN"`, `source=XHR`, `raw_payload={"seed": True}`, `is_available=True`. `test_...ultima_observacion` asserta `isinstance(price, Decimal)`, `currency=="MXN"`, `raw_payload=={"seed": True}`. |
| 6 | No cambia el contrato OpenAPI (sin endpoints) | **CUMPLE** | `git status` no lista `backend/openapi.json` ni `schema.d.ts`. Fase 5 de init.sh VERDE sin drift. |

### Sección Backend de `CHECKPOINTS.md`

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `uv run pytest` pasa; tests nuevos fallarían sin la implementación | **CUMPLE** | `pytest -q` → 40 passed. Prueba de mutación (mover `seed.py`) → 3 fallos. |
| `makemigrations --check --dry-run` limpio | **CUMPLE** | "No changes detected", exit 0. |
| `ruff check .` limpio | **CUMPLE** | "All checks passed!" |
| Lógica de negocio en `services.py`, no en routers | **CUMPLE** | `seed_demo()` vive en `apps/core/services.py`; el command (`seed.py`) es delgado: solo invoca y reporta. `api.py` no tocado. |
| **Arquitectura:** `api.py` sin ORM | **CUMPLE** | `grep -rnE "\.objects\|\.save\(\|\.filter\(\|\.create\(\|\.delete\(" backend/apps/*/api.py backend/config/api.py` → VACÍO (exit 1). Fase 3 de init.sh: "routers (api.py) sin llamadas al ORM" ✔. |
| `corsheaders` desde env | **N/A** | F013 no toca configuración CORS. |
| Si cambió contrato: openapi regenerado | **N/A** | No cambió contrato (criterio 6). |

### Sección Global + Higiene de `CHECKPOINTS.md`

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `./init.sh` verde de punta a punta | **CUMPLE** | Resumen: 31 ok, 0 fallos, 4 pendientes (MVP). Salida completa abajo. |
| Solo F013 `in_progress`; ninguna otra cambió | **CUMPLE** | `feature_list.json`: F013 único `in_progress`; init.sh Fase 1: "features in_progress: 1 (máximo 1)" ✔. |
| Existe `progress/impl_F013_backend.md` con output real | **CUMPLE** | Presente; su output coincide con mis re-corridas. |
| Cumple la spec criterio por criterio | **CUMPLE** | Tabla de criterios arriba (6/6). |
| `feature_list.json` JSON válido, ≤1 `in_progress` | **CUMPLE** | init.sh Fase 1 ✔. |
| Frontend: `fetch(` fuera del cliente / `any` | **CUMPLE** (sin cambios) | Greps de frontend → VACÍO. F013 no toca frontend. |
| Repo git inicializado | **CUMPLE** | `git rev-parse` → true; init.sh Fase 0 "repositorio git inicializado" ✔. |

---

## Diff: archivos tocados (solo capa permitida)

`git status --porcelain`:
```
 M backend/apps/core/services.py
?? backend/apps/core/management/
?? backend/apps/core/tests/test_seed.py
?? progress/impl_F013_backend.md
```
Solo `backend/apps/core/*` (services + management/commands/seed.py + tests) y
`progress/`. **`backend/openapi.json` NO aparece** (correcto). Diff de
`services.py` confirma que `get_health` se conserva y solo se añadió `seed_demo`.

Grep ORM en routers (debe dar VACÍO):
```
grep -rnE "\.objects|\.save\(|\.filter\(|\.create\(|\.delete\(" backend/apps/*/api.py backend/config/api.py
→ (vacío, exit 1)
```

---

## Output real: dos corridas de `seed` (idempotencia)

```
=========== SEED RUN 1 ===========
Seed demo aplicado (idempotente).
  retailers: 2
  locations: 2
  zones: 1
  zone_maps: 2
  categories: 1
  canonical_products: 3
  retailer_products: 6
  observations: 18
  observations_created: 0
exit: 0
=========== SEED RUN 2 (idempotency) ===========
Seed demo aplicado (idempotente).
  retailers: 2
  locations: 2
  zones: 1
  zone_maps: 2
  categories: 1
  canonical_products: 3
  retailer_products: 6
  observations: 18
  observations_created: 0
exit: 0
```
Nota: la DB de dev ya estaba sembrada por el implementer, por eso ambas corridas
reportan `observations_created: 0` con conteos idénticos (idempotencia sobre DB
ya poblada). La idempotencia desde DB limpia (1ª crea, 2ª crea 0 sin cambiar
conteos) la cubre `test_seed_es_idempotente` sobre DB de test fresca → PASA.

## Output real: prueba "git stash mental" (el test fallaría sin la implementación)

Con `seed.py` movido temporalmente y luego restaurado:
```
E   django.core.management.base.CommandError: Unknown command: 'seed'
FAILED apps/core/tests/test_seed.py::test_seed_crea_el_grafo_de_la_spec
FAILED apps/core/tests/test_seed.py::test_seed_crea_historial_y_ultima_observacion
FAILED apps/core/tests/test_seed.py::test_seed_es_idempotente
```
Restaurado → 3 passed. El test es load-bearing.

## Output real: `./init.sh` (modo full)

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
  ✔ las 8 feature(s) 'done' tienen review APROBADO

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

=== init.sh exit: 0 ===
```

---

## Conclusión

Todos los criterios de la spec (6/6) y los puntos aplicables de Global +
Backend + Higiene de `CHECKPOINTS.md` CUMPLEN, verificados re-ejecutando los
comandos. La lógica vive en `services.py`, el command es delgado, no hay ORM en
routers, no hay migraciones nuevas, el contrato no cambió, y el test es
load-bearing (falla sin el command). `./init.sh` VERDE.

**Veredicto: APROBADO.**
