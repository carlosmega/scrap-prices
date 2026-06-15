# F025 — HomeDepotAdapter + ingestión a PriceObservation

> Milestone M2. Usa la infra de F024 y el reconocimiento de F010
> (`docs/recon/homedepot.md`). Convierte precios reales de Home Depot en
> `PriceObservation`, con parser probado **offline** contra golden fixtures.

## Contexto y objetivo
Implementar el adapter de Home Depot (`source=xhr`, plataforma HCL Commerce) que,
dada una zona/tienda, obtiene precios de "varilla" y los ingiere a la DB. El parser
se prueba sin red contra un fixture extraído del HAR real; la corrida en vivo la
ejecuta el humano en su entorno.

## Alcance
**Incluye (backend, `apps/scraping/`):**
- **`HomeDepotAdapter(BaseRetailerAdapter)`** (de F024): `set_zone(location)` fija el
  `physicalStoreId`; `list_products(category, location)` / `get_price(...)` consultan
  el endpoint XHR documentado en F010
  (`GET /search/resources/api/v2/products?...&physicalStoreId={id}&currency=MXN`)
  vía el `PoliteClient` de F024 (UA honesto, rate-limit, stop-if-blocked).
- **Parser puro** `parse_homedepot(payload) -> list[RawProduct/RawPrice]`: de
  `contents[]` extrae `partNumber` (sku), `name`, precio (`price[]` usage
  Offer/Display y/o `x_prices.<store>.mxn`, Decimal), `currency`, disponibilidad
  (`inventories...quantity`), unidad (`x_measurements`), `raw_payload`. Función pura,
  sin red.
- **Golden fixture**: extraer del HAR (`docs/recon/har/www.homedepot.com.mx.har`) 1–3
  respuestas reales de producto y guardarlas **sanitizadas** en
  `apps/scraping/tests/fixtures/homedepot_*.json` (solo datos de catálogo/precio; sin
  cookies/tokens). El fixture SÍ se commitea.
- **Ingestión** `ingest_homedepot(zone, location, category)` (services): abre `ScrapeRun`,
  obtiene productos (vía adapter), hace `get_or_create` de `RetailerProduct`
  (por `retailer`+`external_sku`; matching a `CanonicalProduct` queda **manual/unmatched**),
  inserta `PriceObservation` (source=`xhr`, `captured_at`, `raw_payload`) en la zona, y
  cierra el `ScrapeRun` (ok/partial/failed, items, errors).
- **Tarea Celery** `scrape_retailer_zone` (o `scrape_homedepot_zone`) que invoca la ingestión.

**No incluye:** corrida real contra HD en CI (eso es del entorno del humano); matching
automático (manual en Admin); Construrama (F026); Celery beat scheduling (M5).

## Criterios de aceptación
- [ ] **Backend:** `parse_homedepot` contra el golden fixture devuelve los productos con
      precio Decimal correcto, sku, disponibilidad y unidad (test).
- [ ] **Backend:** `ingest_homedepot` (con el HTTP **mockeado** devolviendo el fixture,
      `httpx.MockTransport`) crea las `PriceObservation` esperadas en la zona + un
      `ScrapeRun` con status ok e `items_found` correcto (test, `@pytest.mark.django_db`).
      Idempotencia razonable (no duplica RetailerProduct por corrida).
- [ ] **Backend:** la tarea Celery corre con `CELERY_TASK_ALWAYS_EAGER` en test y produce
      la ingestión (test). Sin red real en ningún test.
- [ ] **Backend:** el adapter usa el `PoliteClient` de F024 (UA honesto, rate-limit,
      stop-if-blocked); si HD respondiera 403/429/challenge, el `ScrapeRun` cierra
      `failed`/`partial` y NO se evade (test con MockTransport que simula 429).
- [ ] **Backend:** `ruff`/`pytest` verdes; `makemigrations --check` limpio; contrato
      OpenAPI sin cambios. Cero código de evasión.

## Plan de verificación
```bash
cd backend && uv run ruff check . && uv run pytest apps/scraping -q
uv run python manage.py makemigrations --check --dry-run
./init.sh   # verde
# (Corrida en vivo — SOLO en entorno del humano, no en CI):
# uv run python manage.py shell -c "from apps.scraping.services import ingest_homedepot; ..."
```

## Notas y decisiones abiertas
- El fixture es de datos de catálogo/precio (sin PII); commitearlo como golden fixture
  es práctica estándar de test del parser.
- La tienda de Monterrey (`physicalStoreId` del recon F010, `1333`/`18503`) y el
  mapeo zona↔tienda se curan en Admin / seed; el adapter recibe la `RetailerLocation`.
- La corrida real (red) respeta delay ≥7s (robots HD) y se detiene si bloquea.
