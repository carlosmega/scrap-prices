# impl F025 — backend (HomeDepotAdapter + ingestión)

## Spec aplicada y decisiones (≤5 líneas)
Spec: `specs/F025-adapter-homedepot.md` (M2, sobre infra F024 y recon F010).
1. Parser puro en `parsers.py`: `parse_homedepot`/`parse_homedepot_prices` extraen sku (`partNumber`), nombre, precio Decimal (prioridad `price[].Offer` → `x_prices.<store>.mxn` → `Display`), moneda MXN, disponibilidad (`inventories.<store>.quantity` → `total` → `buyable`), unidad (`x_measurements.quantityMeasure`); OMITE SuperSKU padre con precio `""`/`0.0`.
2. Adapter `HomeDepotAdapter` usa el `PoliteClient` de F024 por composición; `set_zone` exige `RetailerLocation` y fija `physicalStoreId=external_id`; `fetch_products_with_prices` evita una 2ª petición por SKU (cortesía).
3. Ingestión `ingest_homedepot` + tarea `scrape_retailer_zone`; matching a canónico queda `unmatched` (manual en Admin). Stop-if-blocked: el 429 propaga `RetailerBlockedError`, cierra `failed`, sin reintento.
4. Fixtures golden sanitizados extraídos del HAR con script node (jq no disponible); solo catálogo/precio/inventario relevante, sin cookies/tokens.

## Archivos creados/modificados
Creados:
- `backend/apps/scraping/parsers.py` — parser puro HD (sin red/DB).
- `backend/apps/scraping/homedepot.py` — `HomeDepotAdapter(BaseRetailerAdapter)`.
- `backend/apps/scraping/tasks.py` — tarea Celery `scrape_retailer_zone`.
- `backend/apps/scraping/tests/test_parsers_homedepot.py` — parser vs golden fixtures.
- `backend/apps/scraping/tests/test_homedepot.py` — adapter+ingestión (MockTransport, eager, 429).
- `backend/apps/scraping/tests/fixtures/homedepot_varilla_482588.json` — 1 varilla con inventario (golden, commitea).
- `backend/apps/scraping/tests/fixtures/homedepot_varilla_batch.json` — 4 SKUs con precio (golden, commitea).
- `backend/apps/scraping/tests/fixtures/homedepot_supersku_empty.json` — SuperSKU padre sin precio (golden, commitea).

Modificados:
- `backend/apps/scraping/services.py` — añade `ingest_homedepot` y helper `_get_or_create_retailer_product`.

## ¿Cambió el contrato OpenAPI?
**NO.** No se añadió ni modificó `api.py`/`schemas.py`; sin endpoints nuevos. `backend/openapi.json` intacto. (import-linter: 1 kept, 0 broken.)

## Output REAL de las verificaciones

```
### ruff  (uv run ruff check .)
All checks passed!

### makemigrations  (uv run python manage.py makemigrations --check --dry-run)
No changes detected

### pytest  (uv run pytest apps/scraping)
.................................                                        [100%]
33 passed in 0.62s
```

Suite completa de backend (`uv run pytest -q`): 110 passed.

## Deuda / seguimientos
- Paginación: `fetch_products_with_prices` pide una sola página (`limit=28&offset=0`); iterar por `total` cuando haya >28 productos (recon §2.2) queda pendiente — el HAR no guardó el body del listado, solo del batch por `partNumber`.
- Matching a `CanonicalProduct` es manual en Admin (PRD D1); el matching automático (rapidfuzz) es fase posterior.
- Mapeo zona↔tienda: el adapter recibe la `RetailerLocation`; poblar `external_id=18503` (interno) / `1333` (código) se cura en seed/Admin. El recon advierte validar que 1333/18503 sea físicamente Monterrey antes de activar.
- `Retailer.scraper_status` sigue `paused` hasta el gate ToS/robots humano (recon §0): el adapter es técnicamente funcional pero NO se activa corrida real en CI; solo tests offline.
- Disponibilidad fina: para SKUs sin `inventories.*` se cae a `buyable`; algunos batches solo traen `inventories.M10.quantity` (mercado, valor centinela max-int) — no usado como tienda.
