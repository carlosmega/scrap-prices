# impl F026 — backend (ConstruramaAdapter, Algolia respetuoso)

## Spec aplicada y decisiones (≤5 líneas)
Spec: `specs/F026-adapter-construrama.md` (M2, espeja F024/F025/F027).
1. Parser puro `parse_construrama`/`parse_construrama_prices` en `parsers.py`: precio `OSS7_priceValue_mxn_double` (ignora `priceValue_mxn_double`=0), sku `code_string` (objectID/pk de respaldo), `raw_name`=`name_text_es_mx`, url absoluta desde `url_es_mx_string`, brand de `brand_string_mv` filtrando el token `"brands"`, `is_available`=`inStockFlag_boolean`, `sale_unit` inferido del nombre (Kilogramos→kg / Pieza→pieza, F031).
2. `ConstruramaAdapter` (POST a la Query API de Algolia) por composición sobre `PoliteClient`; le añadí `post()` al cliente (Algolia solo acepta POST) reusando el mismo rate-limit/tenacity/stop-if-blocked. `set_zone` lee `current_store`/app_id/índice de `RetailerLocation.extra`.
3. Search key: env `CONSTRURAMA_ALGOLIA_SEARCH_KEY` (default vacío, NO se commitea); si falta ⇒ `ScrapeError` antes de la red. App ID/índice públicos (default en settings).
4. Ingestión `ingest_construrama` (extrae el núcleo común `_run_ingestion`, reusado por HD) + tarea Celery `scrape_construrama_zone` + wiring en `manage.py scrape` + seed idempotente con `extra` (nuevo-leon/OSS7/place_id/appId/índice). Golden fixture sanitizado (7 hits reales) committeable.

## Archivos creados/modificados (solo dentro de `backend/`)
Creados:
- `backend/apps/scraping/construrama.py` — `ConstruramaAdapter(BaseRetailerAdapter)` (POST Algolia, `source=xhr`).
- `backend/apps/scraping/tests/test_parsers_construrama.py` — parser puro vs golden fixtures.
- `backend/apps/scraping/tests/test_construrama.py` — adapter + ingestión + tarea + comando (MockTransport, 429, search key faltante).
- `backend/apps/scraping/tests/fixtures/construrama_varilla_algolia.json` — respuesta Algolia REAL sanitizada (7 hits, solo `results[0].hits[]`, sin headers/keys; committeable).
- `backend/apps/scraping/tests/fixtures/construrama_sin_precio.json` — hit con `OSS7_priceValue`=0 (debe omitirse).

Modificados:
- `backend/apps/scraping/parsers.py` — funciones puras de Construrama (parse + helpers url/brand/unit/sale_unit).
- `backend/apps/scraping/client.py` — `post()` + refactor `_send`/`_do_request` (get intacto).
- `backend/apps/scraping/services.py` — `ingest_construrama` + `_get_or_create_retailer_product_construrama` + `_run_ingestion` común (HD delega igual).
- `backend/apps/scraping/tasks.py` — tarea `scrape_construrama_zone` + helper `_resumen_corrida`.
- `backend/apps/scraping/management/commands/scrape.py` — registra construrama en `INGEST_REGISTRY` y `build_adapter`; **[review fix]** surface `ScrapeError` como STOP limpio del guardrail (`_reportar_scrape_error`).
- `backend/apps/scraping/tests/test_command_scrape.py` — el test "slug sin adapter" ahora usa un retailer futuro (`ferre-futura`): construrama ya tiene adapter.
- `backend/apps/scraping/tests/test_construrama.py` — **[review fix]** 2 tests de integración seed↔comando real (regresión del mapeo).
- `backend/apps/core/services.py` (seed) — `RetailerLocation` Construrama con `extra` (subpath `nuevo-leon`, `current_store=OSS7`, `place_id`, `algolia_app_id=NJVY3EU5DW`, `algolia_index=construrama_mx`); subpath `/nuevo-leon`; **[review fix]** `ZoneLocationMap` Construrama `is_primary=True`.
- `backend/apps/core/tests/test_seed.py` — **[review fix]** aserción de primarios: 1 por retailer (antes 1 por zona).
- `backend/config/settings.py` — `CONSTRURAMA_ALGOLIA_APP_ID`/`_INDEX` (públicos, default) y `_SEARCH_KEY` (env, default vacío).

## Fix del review (RECHAZO #1 — `progress/review_F026.md`)
Defecto único y acotado: el criterio 4 fallaba contra la BD del seed real porque el `ZoneLocationMap` de Construrama se sembraba `is_primary=False` y `_resolver_primary_location` (comando `scrape`) exige `is_primary=True`. Los tests lo enmascaraban (el fixture `cr_setup` usaba `is_primary=True`, estado que el seed nunca producía → integración seed↔comando sin cubrir).
1. `apps/core/services.py` (seed): `ZoneLocationMap` de Construrama ahora `is_primary=True` (igual que Home Depot). `is_primary` es POR retailer (lo consume el resolver del comando, que filtra por retailer, y el Admin); la búsqueda de precios no depende de un único primario por zona.
2. `apps/core/tests/test_seed.py`: la aserción de primarios pasa de "exactamente 1 por zona" a "1 por retailer".
3. Hueco de test cerrado: 2 tests de integración seed↔comando REAL en `test_construrama.py` (corren `seed` y luego `scrape --retailer construrama --dry-run`). **Demostrado que fallan sin el fix**: con el seed revertido a `is_primary=False`, ambos fallan con `AssertionError`/mapping →
   `CommandError: No hay una RetailerLocation primaria de 'construrama' que sirva la zona 'monterrey-metro' (falta un ZoneLocationMap is_primary)`.
4. `scrape.py`: el comando ahora surface `ScrapeError` (p.ej. falta la search key) como un STOP limpio del guardrail (CommandError con motivo, sin stacktrace), distinto del CommandError de mapeo.

### Demostración de corrida real (seed + scrape dry-run) — output + exit code
```
=== SEED ===
Seed demo aplicado (idempotente).
  retailers: 2
  ...
=== SCRAPE (dry-run) ===
Retailer: Construrama (construrama) · Zona: Monterrey Metro (monterrey-metro) · Tienda: Construrama Materiales del Norte (external_id=distribuidor-mty-centro) · Categoría: varilla
DRY-RUN: no se escribirá nada en la BD.
CommandError: No se pudo completar el fetch del retailer (guardrail): Falta la search key de Algolia de Construrama. Defínela en CONSTRURAMA_ALGOLIA_SEARCH_KEY (o re-obténla de `get/algolia`). No se hardcodea ni se commitea.
EXIT=1
```
La línea "Tienda: Construrama Materiales del Norte" prueba que el **mapeo zona↔tienda se resolvió** (ya NO es el `CommandError` de mapeo); el único fallo restante es el **guardrail** por falta de la search key (esperado offline). No hubo petición de red (el adapter falla antes de pegar).

## ¿Cambió el contrato OpenAPI?
**NO.** No se tocaron `api.py`/`schemas.py` ni rutas (adapter + management command + task). Verificado regenerando a temp y `diff -q` contra `backend/openapi.json` → "CONTRATO SIN CAMBIOS". No procede `pnpm gen:api`. Sin migraciones nuevas (reuso `RetailerLocation.extra` y `RetailerProduct.brand`, ya migrados).

## Output REAL de las verificaciones

### uv run ruff check .
```
All checks passed!
```

### uv run python manage.py makemigrations --check --dry-run
```
No changes detected
```

### uv run pytest -q
```
........................................................................ [ 42%]
........................................................................ [ 84%]
...........................                                              [100%]
171 passed in 0.73s
```
(Suite de scraping + seed: `uv run pytest apps/scraping apps/core/tests/test_seed.py` → 82 passed, incluye los 2 tests de regresión seed↔comando. Contrato de capas: `uv run lint-imports` → 1 kept, 0 broken.)

## Deuda / seguimientos
- **Corrida real (red)**: pendiente en el entorno del humano con la search key real (`CONSTRURAMA_ALGOLIA_SEARCH_KEY`) para validar empíricamente que Algolia responde a un cliente server-side sin pasar por Imperva (recon §5). Si la key está restringida por Referer/`allowedSources` ⇒ 403 ⇒ `RetailerBlockedError` (stop-if-blocked) ⇒ escalar a Plan B (Playwright) o `non_viable` como feature aparte.
- **Paginación**: `fetch_products_with_prices` pide una sola página (`hitsPerPage=20`, `page=0`); iterar por `page`/`nbPages` queda pendiente (igual que HD). La categoría piloto (varilla, 7 hits) cabe en una página.
- **Matching a `CanonicalProduct`**: manual en Admin (PRD D1). "varilla" trae accesorios (p.ej. amarrador Truper) que el humano descartará. Curar `sale_unit`/`mass_kg` para que la comparación $/kg vs Home Depot sea real (F031).
- **Prefijo de precio `OSS7`**: se lee de `RetailerLocation.extra.current_store` (parametrizable por zona). Si otra zona usa otro prefijo, basta sembrarlo en `extra`.
