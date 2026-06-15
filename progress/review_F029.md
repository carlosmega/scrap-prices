# Review F029 — HomeDepotAdapter: params reales de búsqueda (profileName + marketId/stLocId)

**Veredicto: APROBADO**

Capa única backend (no toca contrato). Verificación offline re-ejecutada por el
reviewer (no se aceptó el output del implementer). `./init.sh` (modo full, sin
`--e2e`) termina VERDE. Toda evidencia abajo es de mi propia corrida.

## Criterios de aceptación (spec F029) — uno por uno

| # | Criterio | Estado | Evidencia (comando/archivo) |
|---|----------|--------|------------------------------|
| 1 | `RetailerLocation.extra` (JSONField) existe + migración; `makemigrations --check` limpio | CUMPLE | `apps/geo/models.py:63` `extra = models.JSONField(default=dict, blank=True)`; migración `apps/geo/migrations/0002_retailerlocation_extra.py` (AddField `extra`). `makemigrations --check --dry-run` → `No changes detected` EXIT=0 (mi corrida). Ver NOTA 1 sobre "commiteada". |
| 2 | Tras `seed`, HD Monterrey tiene `extra == {"market_id":"10","st_loc_id":"18503"}`. Idempotente | CUMPLE | Shell propio (DB de test): `extra (1ra)={'market_id':'10','st_loc_id':'18503'}`, `external_id=1333`; tras 2º `seed_demo()`: `extra (2da)` idéntico, `HD locations count: 1`, `MATCH: True`. También `apps/core/services.py:132` y test `test_seed_es_idempotente`. |
| 3 | Test unit `_build_search_url` con ese `extra` → URL con `profileName=HCL_V2_findProductsBySearchTermWithPrice`, `marketId=10`, `stLocId=18503`, `physicalStoreId=1333`, `searchTerm=varilla`, `limit` | CUMPLE | Test `apps/scraping/tests/test_homedepot.py::test_build_search_url_incluye_profile_market_y_stloc_desde_extra` (usa `parse_qs`, independiente del orden) PASS. Reconstruido por mí en shell: URL contiene los 6 params; `ALL OK: True`. |
| 4 | Tests offline existentes (parser, ingestión MockTransport, comando, seed) verdes; `pytest apps` verde; `ruff` limpio; contrato OpenAPI sin cambios | CUMPLE | `uv run pytest apps` → `120 passed`. `uv run ruff check .` → `All checks passed!` EXIT=0. `git status --porcelain backend/openapi.json` vacío (contrato intacto); el impl declara correctamente que no aplica regenerarlo. |
| 5 | Cero evasión; ningún test pega a red real | CUMPLE | `grep` de `httpx.get/post/Client(`, `requests.`, `urlopen` en `apps/scraping/tests` → ninguno; todo vía `httpx.MockTransport` (test_client/test_command_scrape/test_homedepot). Test 429 (`test_ingest_429_lanza_blocked_y_run_failed_sin_reintento`) verifica 1 sola request sin reintento. |
| 6 | (Confirmación en vivo ≈13 varillas) | NO VERIFICABLE (offline) | Fuera del gate del reviewer; el líder confirmó `scrape --dry-run` → 13 varillas. CI/offline no pega a red. |

## CHECKPOINTS.md — punto por punto

### Global
- `./init.sh` verde de punta a punta — CUMPLE (31 ok, 0 fallos; output abajo).
- Exactamente F029 `in_progress`, ninguna otra cambió — CUMPLE: `node` sobre
  `feature_list.json` → `in_progress count: 1`, `in_progress ids: F029`.
- Existe `progress/impl_F029_backend.md` con output real — CUMPLE (presente).
- Cumple la spec criterio por criterio — CUMPLE (tabla anterior).

### Backend
- `uv run pytest` pasa con tests nuevos que fallarían sin la implementación —
  CUMPLE: los 2 tests de `_build_search_url` afirman `marketId=10`/`stLocId=18503`
  desde `extra`; sin el código de `set_zone`/`_build_search_url` que lee `extra`,
  esos asserts fallarían (regla "git stash mental"). El test de seed afirma
  `extra == {...}`, que falla sin el `defaults` de `services.py:132`.
- `makemigrations --check --dry-run` limpio — CUMPLE (`No changes detected`).
- `ruff check .` limpio — CUMPLE (`All checks passed!`).
- Lógica en `services.py`, no en routers — CUMPLE (el seed vive en
  `apps/core/services.py`; `api.py` no tocado).
- Arquitectura: `api.py` sin ORM — CUMPLE: grep con el filtro de decoradores de
  `init.sh` → vacío (los 2 hits crudos en `lists/api.py` son `@router.delete(...)`,
  declaraciones de ruta, no ORM; los filtra `init.sh` y Fase 3 da verde).
- `corsheaders`/`CORS_ALLOWED_ORIGINS` — N/A para F029 (no toca settings; ya
  configurado en features previas, Fase 3 verde).
- Contrato: no cambió → no aplica regenerar `openapi.json` — CUMPLE.

### Contrato — N/A (la API no cambió; `backend/openapi.json` sin diff).

### Higiene del arnés
- `feature_list.json` JSON válido con ≤1 `in_progress` — CUMPLE.
- `progress/current.md` refleja la sesión — presente (responsabilidad del líder).
- Repo git inicializado — CUMPLE: `git rev-parse --is-inside-work-tree` → `true`
  (la cabecera de entorno decía "no repo", pero el comando determinista confirma
  que SÍ lo es; Fase 0 de `init.sh` → "repositorio git inicializado").

## Diff / scope (git)

`git status --porcelain` — solo capa permitida:

```
 M backend/apps/core/services.py
 M backend/apps/core/tests/test_seed.py
 M backend/apps/geo/models.py
 M backend/apps/scraping/homedepot.py
 M backend/apps/scraping/tests/test_homedepot.py
?? backend/apps/geo/migrations/0002_retailerlocation_extra.py
?? progress/impl_F029_backend.md
```

Todo cae en `backend/apps/{geo (+migración), core, scraping}` + `progress/`,
exactamente lo que la spec autoriza. `backend/openapi.json` NO aparece (sin cambios).

## Notas

- **NOTA 1 (no bloqueante):** la spec dice "migración **commiteada**". El archivo
  `0002_retailerlocation_extra.py` existe en el árbol pero está *untracked* (`??`),
  igual que el resto del changeset de F029 (aún sin commit, coherente con el flujo:
  el líder commitea tras la aprobación). El gate operativo del criterio
  (`makemigrations --check --dry-run` → "No changes detected", archivo presente,
  `init.sh` verde) se cumple. **Acción para el líder:** al marcar F029 `done`,
  incluir la migración en el commit de la feature (no es trabajo de implementer).
- Deuda heredada (ya documentada por el impl): el fixture `hd_setup` usa
  `external_id="18503"`; no representa la tienda real (donde 18503 es el `stLocId`),
  pero no afecta a F029 — el shape correcto se ejercita en los tests nuevos de
  `_build_search_url`. Sin impacto funcional.

## Output REAL de `./init.sh` (modo full)

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
  ✔ las 25 feature(s) 'done' tienen review APROBADO

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

INIT_EXIT=0
```

Pendientes (4): jq y docker no presentes (opcionales), Fase 2 Postgres/Redis
diferida (MVP SQLite/sin-Docker), Fase 6 E2E saltada (modo full, no `--e2e`).
Esperado y no bloqueante para F029 (capa única backend).

## Evidencia complementaria (corridas propias)

```
$ uv run python manage.py makemigrations --check --dry-run
No changes detected            EXIT=0

$ uv run ruff check .
All checks passed!             EXIT=0

$ uv run pytest apps
120 passed in 3.05s            EXIT=0

# 4 tests de aceptación F029 (explícitos)
test_build_search_url_incluye_profile_market_y_stloc_desde_extra  PASS
test_build_search_url_sin_extra_omite_market_y_stloc              PASS
test_seed_crea_el_grafo_de_la_spec                                PASS
test_seed_es_idempotente                                          PASS
4 passed in 0.65s

# Shell: seed → extra (independiente del test)
extra (1ra): {'market_id': '10', 'st_loc_id': '18503'}   external_id: 1333
extra (2da): {'market_id': '10', 'st_loc_id': '18503'}   HD locations count: 1   MATCH: True

# Shell: _build_search_url (independiente del test)
URL: .../products?storeId=10351&searchTerm=varilla&limit=28&offset=0&profileName=HCL_V2_findProductsBySearchTermWithPrice&contractId=...&currency=MXN&langId=-5&marketId=10&physicalStoreId=1333&stLocId=18503
CHECKS: {profileName, marketId=10, stLocId=18503, physicalStoreId=1333, searchTerm=varilla, limit present} ALL OK: True
```
