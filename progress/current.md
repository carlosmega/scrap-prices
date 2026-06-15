# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F025** — HomeDepotAdapter + ingestión (M2)
**Spec:** `specs/F025-adapter-homedepot.md`

## Plan F025 (capa backend → implementer-backend)
- `HomeDepotAdapter(BaseRetailerAdapter)` (usa PoliteClient de F024); parser puro
  `parse_homedepot` (precio Decimal de `price[]`/`x_prices`, sku, disponibilidad, unidad).
- **Golden fixture** extraído del HAR real (sanitizado) en apps/scraping/tests/fixtures/.
- Ingestión: ScrapeRun + get_or_create RetailerProduct (matching manual) + PriceObservation (source=xhr).
- Tarea Celery `scrape_retailer_zone` testeada con ALWAYS_EAGER + httpx MockTransport (sin red real).
- Respetuoso: stop-if-blocked (un test simula 429 → ScrapeRun failed, sin evasión).

La corrida REAL contra HD va en el entorno del humano (delay ≥7s); aquí todo offline.

**Estado:** F025 `in_progress`. M2: F024 ✅ → **F025** (HD) → F026 (Construrama, tras captura Algolia).
