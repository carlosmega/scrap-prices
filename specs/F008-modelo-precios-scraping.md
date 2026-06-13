# F008 — Modelo de precios y auditoría de scraping

> SDD: la spec es el contrato. Deriva del PRD §8, §9 (subsistema de scraping)
> y RNF3/RNF6. Depende de F006 (`Zone`, `RetailerLocation`, `Retailer`) y F007
> (`RetailerProduct`).

## Contexto y objetivo

El principio arquitectónico no negociable del PRD: el scraping NO ocurre en vivo;
los scrapers escriben observaciones de precio con `zona + timestamp` y la
búsqueda del usuario consulta siempre la DB propia. Esta feature crea el almacén
histórico de precios (`PriceObservation`) y la auditoría de corridas
(`ScrapeRun`). No implementa scrapers (eso es M1/M2); solo el destino de los datos.

## Alcance

**Incluye:**
- Modelos `PriceObservation`, `ScrapeRun`.
- Migraciones e índices para consulta eficiente por (`retailer_product`, `zone`,
  `captured_at`) — soporta "último precio por producto/zona".
- **Django Admin** de ambos (D2 del PRD: monitorear corridas).
- Tests de modelo + de la consulta "última observación por producto y zona".

**No incluye (explícitamente fuera):**
- Adapters / scrapers HTTP (M2).
- Endpoints Ninja de precios/historial (M3).
- Tareas Celery de scraping (M2/M5).

## Modelo (campos exactos, PRD §8)

Heredan la base de F006 donde aplique (UUID/timestamps/`is_active`).

**`PriceObservation`** — una lectura de precio (histórico, no se sobrescribe):
`retailer_product` (FK→RetailerProduct, related_name `observations`), `zone`
(FK→Zone, null, blank, related_name `observations`), `retailer_location`
(FK→RetailerLocation, null, blank), `price` (DecimalField, max_digits 12,
decimal_places 2), `currency` (str, default `MXN`), `is_available` (bool,
default true), `source` (choices: `xhr` | `html` | `playwright`), `captured_at`
(DateTimeField; momento de la lectura, indexado), `raw_payload` (JSONField,
default dict; auditabilidad RNF/guardrail §2.3).
- Índice compuesto: `(retailer_product, zone, -captured_at)`.

**`ScrapeRun`** — auditoría de corrida:
`retailer` (FK→Retailer, related_name `scrape_runs`), `zone` (FK→Zone, null,
blank), `started_at` (DateTime), `finished_at` (DateTime, null, blank),
`status` (choices: `ok` | `partial` | `failed`), `items_found` (int, default 0),
`errors` (JSONField, default list).

### Relaciones clave
- `RetailerProduct` *1↔N* `PriceObservation`.
- `Retailer`/`Zone` *1↔N* `ScrapeRun`.

## Criterios de aceptación

- [ ] **Backend:** ambas entidades en `models.py`; `migrate` limpio; el índice
      compuesto de `PriceObservation` aparece en la migración.
- [ ] **Backend:** Admin de `ScrapeRun` con `list_display`
      (retailer, zona, status, items_found, started_at) y `list_filter` por
      `status`/`retailer`; Admin de `PriceObservation` con filtros por
      `retailer_product`/`zone` y orden por `-captured_at`.
- [ ] **Backend:** tests que: crean varias `PriceObservation` del mismo
      `RetailerProduct`+`Zone` con distintos `captured_at` y verifican que la
      consulta de "última observación" devuelve la más reciente; crean un
      `ScrapeRun` `partial` con `errors` no vacío.
- [ ] **Backend:** `raw_payload` se persiste y recupera como JSON (guardrail de
      auditabilidad §2.3 punto 5).
- [ ] **Backend:** `uv run pytest` pasa, `ruff check .` limpio,
      `makemigrations --check --dry-run` limpio.
- [ ] **Backend:** no cambia el contrato OpenAPI (sin endpoints).

## Plan de verificación

```bash
cd backend && uv run python manage.py migrate
uv run pytest apps -q
uv run ruff check . && uv run python manage.py makemigrations --check --dry-run
./init.sh   # verde
```

## Notas y decisiones abiertas

- `price` es `Decimal` (nunca float) por exactitud monetaria (RNF/PRD §8).
- La regla de negocio "precio más fresco por zona" se consultará vía
  `services.py` en M3; aquí solo se garantiza que el índice lo hace eficiente.
- `captured_at` es explícito (lo fija el scraper), distinto de `created_at` de la
  base (cuándo se insertó la fila).
