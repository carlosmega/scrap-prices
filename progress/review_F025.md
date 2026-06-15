# Review F025 — HomeDepotAdapter + ingestión a PriceObservation

**Veredicto: APROBADO**

Capa única backend (no toca contrato). Verificación re-ejecutada por el reviewer
(no se aceptó output pegado): `./init.sh` (modo full) VERDE, `uv run pytest
apps/scraping` 33 passed, greps deterministas limpios, diff acotado a
`backend/apps/scraping` + `progress/`. `backend/openapi.json` sin cambios.

## Criterios de aceptación (spec F025) → estado → evidencia

| # | Criterio | Estado | Evidencia (comando/archivo) |
|---|----------|--------|------------------------------|
| 1 | `parse_homedepot` vs golden fixtures: precio Decimal correcto, sku (`partNumber`), disponibilidad, unidad | CUMPLE | `test_parse_varilla_precio_decimal_sku_unidad` (sku `482588`, unidad `C62`), `test_parse_varilla_prices_precio_y_disponibilidad` (`Decimal("20068.0")`, `is_available=False` por `inventories.18503.quantity="0.0"`), `test_parse_batch...` (4 SKUs). `parsers.py:108` función pura (sin red/DB) |
| 2 | Omite el SuperSKU padre sin precio | CUMPLE | `test_parse_omite_supersku_sin_precio_fiable` → `productos == []` y `precios == []`; fixture `homedepot_supersku_empty.json` (`Offer.value:""`, `Display:"0.0"`); `_decimal_or_none` descarta vacío/≤0 (`parsers.py:29`) |
| 3 | Fixtures existen en `apps/scraping/tests/fixtures/` y están sanitizados (sin cookies/tokens) | CUMPLE | `ls` lista los 3 `.json`. `grep -inE "cookie\|authorization\|bearer\|set-cookie\|token"` sobre los fixtures → **VACÍO** (No matches found) |
| 4 | `ingest_homedepot` con HTTP mockeado (MockTransport + fixture) crea las `PriceObservation` (source=xhr) + `ScrapeRun` ok con `items_found` correcto | CUMPLE | `test_ingest_homedepot_crea_observations_y_run_ok` → `run.status==OK`, `items_found==4`, 4 `PriceObservation` con `source=XHR`, `retailer_location`, `price` Decimal>0, `raw_payload`. MockTransport en `_make_adapter` (`test_homedepot.py:50`) |
| 5 | Idempotencia: correr 2 veces NO duplica `RetailerProduct` | CUMPLE | `test_ingest_dos_veces_no_duplica_retailer_product` → 8 `PriceObservation` (histórico) pero 4 `RetailerProduct`. `get_or_create` por (retailer, external_sku) en `services.py:86` |
| 6 | Tarea Celery con `CELERY_TASK_ALWAYS_EAGER` produce la ingestión | CUMPLE | `test_tarea_celery_eager_produce_ingestion` (`@override_settings(CELERY_TASK_ALWAYS_EAGER=True)`) → `result.status==OK`, 4 observaciones. Tarea `scrape_retailer_zone` en `tasks.py:19` |
| 7 | **Respetuoso (CRÍTICO):** 429 → `RetailerBlockedError`, `ScrapeRun` cierra `failed`/`partial` SIN reintentar para evadir | CUMPLE | `test_ingest_429_lanza_blocked_y_run_failed_sin_reintento` → `pytest.raises(RetailerBlockedError)`, `calls["n"]==1` (una sola request, sin reintento), `run.status==FAILED`, `errors[0].type=="blocked"`, `PriceObservation.count()==0`. Mecanismo: `BLOCKED_STATUS_CODES={403,429}` (`client.py:46`), 429 mapea a `RetailerBlockedError` que NO está en `retry_if_exception_type` (`client.py:165`); `services.ingest_homedepot` relanza sin reintentar (`services.py:133`) |
| 8 | Ningún test pega a una URL real (MockTransport/fixtures); `pytest apps/scraping` verde | CUMPLE | `uv run pytest apps/scraping` → **33 passed in 0.52s**. Todo HTTP vía `httpx.MockTransport`; parser puro carga fixtures de disco |
| 9 | `ruff` limpio; `makemigrations --check` limpio (sin modelos nuevos) | CUMPLE | `./init.sh` Fase 3: `ruff check` ✔, `makemigrations --check` ✔. Reusa modelos existentes (`PriceObservation`/`ScrapeRun` de F008, `RetailerProduct` de F007); no añade modelos |
| 10 | ORM nunca en `api.py` (no hay `api.py` en scraping) | CUMPLE | `ls backend/apps/scraping/api.py` → no existe. `grep "\.objects\|\.save(\|\.filter(\|\.create(\|\.delete(" backend/apps/*/api.py` → **VACÍO**. Lógica en `services.py` |
| 11 | Cero código de evasión | CUMPLE | `grep -rinE "fingerprint\|captcha\|stealth\|rotate\|undetected" backend/apps/scraping` → solo detección-para-detenerse (docstrings + heurística `_is_challenge_response` que RECONOCE captcha para parar + test "no se intenta resolver el captcha"). Ningún `rotate`/`stealth`/`undetected`/`fingerprint`-spoof activo |
| 12 | Contrato OpenAPI sin cambios | CUMPLE | `git status --porcelain backend/openapi.json` → VACÍO. `./init.sh` Fase 5 (contrato) VERDE sin cambios. No se tocó `api.py`/`schemas.py` |

## Checkpoints aplicables

### Global
- `./init.sh` verde de punta a punta → CUMPLE (0 fallos, ver output abajo).
- Exactamente F025 `in_progress`, ninguna otra cambió → CUMPLE (`feature_list.json`: 1 in_progress; Fase 1 init.sh ✔).
- `progress/impl_F025_backend.md` con output real → CUMPLE (existe, con ruff/makemigrations/pytest reales).
- Cumple cada criterio de la spec → CUMPLE (tabla arriba).

### Backend
- `uv run pytest` pasa; tests nuevos fallarían sin la implementación → CUMPLE. Verificación "git stash mental": el test 429 asserta `calls["n"]==1` y `RetailerBlockedError`; si se quitara el guard (429 tratado como transitorio/reintentable) el conteo sería >1 y no se lanzaría la excepción → el test fallaría. El test de omisión del SuperSKU fallaría si `_decimal_or_none` aceptara `""`/`"0.0"`. Los tests prueben la implementación, no tautologías.
- `makemigrations --check` limpio → CUMPLE.
- `ruff check .` limpio → CUMPLE.
- Lógica de negocio en `services.py`, no en routers → CUMPLE (no hay router; ingestión en `services.ingest_homedepot`).
- Arquitectura: `api.py` sin ORM → CUMPLE (no hay api.py en scraping; grep global vacío; Fase 3 init.sh ✔).
- Si cambió contrato: openapi regenerado → N/A (no cambió contrato; verificado).

### Higiene del arnés
- `feature_list.json` JSON válido con ≤1 `in_progress` → CUMPLE (Fase 1: in_progress=1).
- `progress/current.md` refleja la sesión (F025 in_progress) → CUMPLE.
- Repo git inicializado → CUMPLE (`git rev-parse` ✔, Fase 0 ✔).

## Diff revisado (capa permitida)

`git status --porcelain`:
```
 M backend/apps/scraping/services.py
?? backend/apps/scraping/homedepot.py
?? backend/apps/scraping/parsers.py
?? backend/apps/scraping/tasks.py
?? backend/apps/scraping/tests/fixtures/
?? backend/apps/scraping/tests/test_homedepot.py
?? backend/apps/scraping/tests/test_parsers_homedepot.py
?? progress/impl_F025_backend.md
```
Todo dentro de `backend/apps/scraping` (+ fixtures) y `progress/`. Ningún archivo
fuera de la capa permitida. `backend/openapi.json` NO cambió.

## Greps deterministas (reviewer)

```
# Fixtures sanitizados (debe dar VACÍO):
$ grep -inE "cookie|authorization|bearer|set-cookie|token" \
    backend/apps/scraping/tests/fixtures/*.json
→ No matches found  (VACÍO ✔)

# ORM en routers (debe dar VACÍO):
$ grep -rnE "\.objects|\.save\(|\.filter\(|\.create\(|\.delete\(" backend/apps/*/api.py
→ No matches found  (VACÍO ✔; además no existe apps/scraping/api.py)

# Código de evasión (solo detección-para-detenerse):
$ grep -rinE "fingerprint|captcha|stealth|rotate|undetected" backend/apps/scraping
→ solo docstrings de stop-if-blocked + heurística que RECONOCE challenge para parar
  + test que asserta que NO se resuelve el captcha. Cero evasión activa. ✔
```

## Output REAL de `./init.sh` (modo full, ejecutado por el reviewer)

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
  ✔ las 22 feature(s) 'done' tienen review APROBADO

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

Las 4 pendientes (jq, docker — Fase 0/2) son del entorno MVP (SQLite/sin-Docker/sin-jq),
no fallos. Fase 5 (contrato) VERDE sin cambios. Fase 6 (E2E) saltada por modo full
(F025 no añade capa e2e, correcto).

## Suite scraping (reviewer, re-ejecutada)

```
$ uv run pytest apps/scraping
.................................                                        [100%]
33 passed in 0.52s
```

## Observaciones (no bloqueantes)

- La deuda declarada en el impl (paginación de una sola página, matching manual a
  `CanonicalProduct`, `scraper_status=paused` hasta gate ToS/robots humano) está
  alineada con la spec ("No incluye": matching automático, scheduling, corrida real
  en CI). No afecta el veredicto.
- El test de idempotencia confirma correctamente que `PriceObservation` ES histórico
  (no se deduplica) y solo `RetailerProduct` es idempotente — coincide con el diseño.
