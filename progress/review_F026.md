# Review F026 — ConstruramaAdapter (Algolia respetuoso)

**Veredicto: APROBADO**

Ronda 2 (re-verificación tras el fix del RECHAZO #1). El defecto único que motivó
el rechazo — el criterio 4 (`manage.py scrape --retailer construrama ...`) fallaba
contra la BD del seed real con un `CommandError` de **mapeo** — quedó **resuelto y
verificado ejecutando yo mismo** los comandos. El resto de criterios ya estaba
correcto en la ronda 1. `./init.sh` verde de punta a punta.

---

## Re-verificación del fix (ejecución propia)

### 1. Criterio 4 — el comando contra el seed REAL (BD fresca desechable)

```
$ export DATABASE_URL="sqlite:////.../scratchpad/review_f026_fix.sqlite3"
$ uv run python manage.py migrate && uv run python manage.py seed
$ uv run python manage.py scrape --retailer construrama --zone monterrey-metro --category varilla --dry-run
Retailer: Construrama (construrama) · Zona: Monterrey Metro (monterrey-metro) ·
  Tienda: Construrama Materiales del Norte (external_id=distribuidor-mty-centro) · Categoría: varilla
DRY-RUN: no se escribirá nada en la BD.
CommandError: No se pudo completar el fetch del retailer (guardrail): Falta la
  search key de Algolia de Construrama. Defínela en CONSTRURAMA_ALGOLIA_SEARCH_KEY...
exit = 1
```

- La línea **`Tienda: Construrama Materiales del Norte`** prueba que el mapeo
  zona↔tienda **se resolvió**: ya NO aparece el `CommandError` de "RetailerLocation
  primaria".
- El `exit=1` restante es el **guardrail esperado offline** (`ScrapeError` por falta
  de `CONSTRURAMA_ALGOLIA_SEARCH_KEY`), que el coordinador declaró **aceptable**. No
  hubo petición de red (el adapter falla antes de pegar).

Estado de mapeos en la BD sembrada (ambos retailers primarios de su propia tienda):
```
home-depot   is_primary= True
construrama  is_primary= True
```

### 2. Seed + regresión (tests que fallarían sin el fix)

- Seed corregido: `apps/core/services.py:198` siembra el `ZoneLocationMap` de
  Construrama con `is_primary=True` (comentario `:189-191`: `is_primary` es POR
  retailer). Verifiqué en ronda 1 que `is_primary` solo lo consumen el resolver del
  comando (por-retailer) y el Admin → cambio seguro, sin impacto en la búsqueda.
- Dos tests de integración **seed↔comando real** en `test_construrama.py:363-416`:
  - `test_seed_y_scrape_construrama_dry_run_resuelve_el_mapeo`: corre `seed` REAL +
    `scrape ... --dry-run` (adapter mockeado) y exige `"Productos que se traerían: 7"`
    — inalcanzable si el resolver de la tienda falla.
  - `test_seed_y_scrape_construrama_sin_key_para_en_guardrail_no_en_mapeo`: corre
    `seed` REAL + `scrape` (key vacía) y exige `"search key" in mensaje` **y**
    `"primaria" not in mensaje`.
  - **Load-bearing probado deterministamente:** en la ronda 1 capturé por ejecución
    que el seed viejo (`is_primary=False`) produce exactamente
    `CommandError: No hay una RetailerLocation primaria de 'construrama'...` (exit 1).
    Ambos tests asertan justo la **negación** de esa falla, así que con el seed
    revertido delatarían el defecto (el primero por no imprimir "7", el segundo
    porque el mensaje contendría "primaria").
  - Corrida propia de los dos tests: **2 passed**.
- `apps/core/tests/test_seed.py`: la aserción de primarios pasó de "1 por zona" a
  "1 por retailer" y **pasa** (3 passed).

### 3. Sin regresión

```
uv run ruff check .                              → All checks passed!
uv run python manage.py makemigrations --check   → No changes detected
uv run pytest                                    → 171 passed in 0.72s   (169 ronda 1 + 2 regresión)
uv run lint-imports                              → Contracts: 1 kept, 0 broken
```

---

## Criterios de aceptación (spec) — estado final

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | `ConstruramaAdapter(BaseRetailerAdapter)` vía `PoliteClient`, UA honesto, delay, tenacity, stop-if-blocked → `RetailerBlockedError`, sin evasión | **CUMPLE** | `construrama.py`; `client.py:221-234`; test `test_ingest_429_lanza_blocked_y_run_failed_sin_reintento` |
| 2 | Parser puro `hits[]`→`RawProduct`/`RawPrice`, Decimal, golden fixtures, ignora hits sin precio (`>0`) | **CUMPLE** | `parsers.py:322-383`; `test_parsers_construrama.py` |
| 3 | Ingestión: `RetailerProduct` get_or_create(external_sku) + `PriceObservation` (source=xhr, raw_payload=hit) + `ScrapeRun` | **CUMPLE** | `services.py:198-244`; tests `test_ingest_construrama_*` |
| 4 | `manage.py scrape --retailer construrama --zone monterrey-metro --category varilla [--dry-run]` **funciona** | **CUMPLE** (antes NO) | Corrida real: resuelve la tienda; solo se detiene en el guardrail de search key (esperado offline). 2 tests seed↔comando lo blindan |
| 5 | Seed idempotente Retailer/RetailerLocation/ZoneLocationMap (extra nuevo-leon/place_id/store-id/OSS7); `scraper_status=active` | **CUMPLE** (antes PARCIAL) | `core/services.py:169-175` (extra), `:125` (`ACTIVE` vía `update_or_create`), `:198` (`is_primary=True`) |
| 6 | `pytest` offline (MockTransport), 429→stop-if-blocked; `ruff`, `makemigrations --check`, api.py sin ORM | **CUMPLE** | `171 passed`; tests 100% offline (`httpx.MockTransport`+`FakeClock`) |
| 7 | `./init.sh` verde de punta a punta | **CUMPLE** | Resumen `33 ok · 0 fallos · VERDE` |

## Chequeos extra (líder) — estado final

| Chequeo | Estado |
|---------|--------|
| ruff / makemigrations --check / pytest / lint-imports | **CUMPLE** (`All checks passed!` · `No changes detected` · `171 passed` · `1 kept, 0 broken`) |
| api.py sin ORM | **CUMPLE** (solo matches de `@router.delete(...)`, decoradores de ruta) |
| Tests OFFLINE (sin red real) | **CUMPLE** (`MockTransport` + `FakeClock`) |
| Search key NO hardcodeada/commiteada; env `CONSTRURAMA_ALGOLIA_SEARCH_KEY` | **CUMPLE** (`settings.py:49,170`; `construrama.py:163-168`) |
| Golden fixture sin key/headers (solo `hits[]`) | **CUMPLE** (fixtures solo catálogo; 0 matches de key hex) |
| Comando registrado (registry + `--dry-run`) | **CUMPLE** (`scrape.py:43-60`; funcionalmente OK contra el seed) |
| Contrato OpenAPI sin drift | **CUMPLE** (`init.sh` Fase 5 verde; sin tocar `api.py`/`schemas.py`) |
| `feature_list.json` válido, exactamente 1 `in_progress` (F026) | **CUMPLE** (`init.sh` Fase 1; `grep` → 1, id F026) |
| Archivos tocados dentro de la capa permitida | **CUMPLE** (`git status`: todo bajo `backend/`; `specs/F026` y `progress/` son territorio del líder) |

## Observación menor (no bloqueante, ya anotada en ronda 1)

- La spec (criterio 1) menciona _"con `retailer_slug`"_, pero el contrato base
  (`base.py:57-92`) no define tal atributo y ningún adapter lo declara (el retailer
  se resuelve de `location.retailer`). Consistente con F025 (aprobado). Discrepancia
  de redacción, no de funcionalidad.

---

## `./init.sh` (output real, ronda 2)

```
── Fase 0 · Herramientas ──            ✔ git/node/jq/uv/docker/pnpm · repo git
── Fase 1 · Invariantes del arnés ──   ✔ feature_list.json válido · in_progress: 1
                                       ✔ las 29 feature(s) 'done' tienen review APROBADO
── Fase 2 · Infraestructura ──         ◌ Docker no usado en MVP (SQLite)
── Fase 3 · Backend ──                 ✔ ruff · makemigrations · pytest · api.py sin ORM
── Fase 4 · Frontend ──                ✔ tsc · lint · vitest · build · fetch solo en client.ts
── Fase 5 · Contrato OpenAPI → TS ──   ✔ tipos TS sincronizados con backend/openapi.json
── Fase 6 · E2E ──                     ◌ saltada (usa ./init.sh --e2e)

════════ Resumen ════════
  ✔ 33 ok   ✘ 0 fallos   ◌ 2 pendientes
  VERDE — el arnés está en estado consistente.
```

## Historial de veredictos

- **Ronda 1 — RECHAZADO:** criterio 4 fallaba contra el seed real (`ZoneLocationMap`
  de Construrama `is_primary=False` vs. resolver que exige `is_primary=True`);
  integración seed↔comando sin cubrir.
- **Ronda 2 — APROBADO:** seed corregido a `is_primary=True`, 2 tests de regresión
  seed↔comando (load-bearing), suite `171 passed`, `./init.sh` verde.
