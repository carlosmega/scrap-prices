# F007 — Modelo de catálogo (categorías y productos)

> SDD: la spec es el contrato. Deriva del PRD §8 y §11 (matching de SKU).
> Depende de F006 (base abstracta + `Retailer`).

## Contexto y objetivo

El catálogo normaliza "el mismo producto" entre retailers: un `CanonicalProduct`
agrupa los `RetailerProduct` (SKUs reales de cada tienda) que le corresponden.
El matching en MVP es **manual vía Django Admin**. Esta feature crea esas
entidades y su curación en Admin; la categoría piloto es **varilla**.

## Alcance

**Incluye:**
- Modelos `Category`, `CanonicalProduct`, `RetailerProduct`.
- Migraciones.
- **Django Admin** con flujo de curación: filtrar `RetailerProduct` por
  `match_status=unmatched` y asignar `CanonicalProduct`.
- Tests de modelo + del cambio de `match_status`.

**No incluye (explícitamente fuera):**
- Endpoints Ninja de búsqueda/detalle (M3).
- Matching automático con `rapidfuzz` (fase posterior; MVP es manual).
- Carga de SKUs reales (eso lo produce el scraping en M2).

## Modelo (campos exactos, PRD §8)

Todos heredan la base `TimeStampedUUIDModel` de F006 (UUID/timestamps/`is_active`).

**`Category`**:
`name` (str), `slug` (slug, unique), `parent` (FK→self, null, blank,
related_name `children`). (`is_active` viene de la base.)

**`CanonicalProduct`** — producto normalizado entre retailers:
`name` (str), `category` (FK→Category, related_name `products`), `unit`
(choices: `pieza` | `saco` | `m` | `kg` | …, extensible), `specs` (JSONField,
default dict; ej. `{calibre, diametro, longitud, marca, presentacion}`).

**`RetailerProduct`** — un SKU tal como existe en UN retailer:
`retailer` (FK→Retailer, related_name `products`), `external_sku` (str),
`raw_name` (str), `url` (URL, blank), `unit_raw` (str, blank), `brand`
(str, blank), `canonical_product` (FK→CanonicalProduct, null, blank,
related_name `retailer_products`), `match_status` (choices: `unmatched` |
`auto` | `manual` | `rejected`, default `unmatched`), `match_confidence`
(Float, null, blank). `unique_together = (retailer, external_sku)`.

### Relaciones clave
- `CanonicalProduct` *1↔N* `RetailerProduct` (matching).
- `Category` jerárquica (self-FK).

## Criterios de aceptación

- [ ] **Backend:** las 3 entidades en `models.py` heredando la base de F006;
      `migrate` corre limpio.
- [ ] **Backend:** Admin de `RetailerProduct` con `list_filter` por
      `match_status` y `retailer`, `search_fields` por `raw_name`/`external_sku`,
      y capacidad de asignar `canonical_product` (D1 del PRD). Admin de
      `CanonicalProduct` y `Category` navegables.
- [ ] **Backend:** tests que: crean una `Category` "Varilla", un
      `CanonicalProduct`, dos `RetailerProduct` (uno por retailer) inicialmente
      `unmatched`, los asignan al canónico y verifican `match_status=manual`;
      y verifican el `unique_together (retailer, external_sku)`.
- [ ] **Backend:** `uv run pytest` pasa, `ruff check .` limpio,
      `makemigrations --check --dry-run` limpio.
- [ ] **Backend:** no cambia el contrato OpenAPI (sin endpoints).

## Plan de verificación

```bash
cd backend && uv run python manage.py migrate
uv run pytest apps -q
uv run ruff check . && uv run python manage.py makemigrations --check --dry-run
# En /admin/: filtrar RetailerProduct por unmatched y asignar un CanonicalProduct
./init.sh   # verde
```

## Notas y decisiones abiertas

- `unit` se modela como choices extensibles; si crece, evaluar tabla `Unit`
  propia en fase posterior (no en MVP).
- La acción de curación puede ser edición inline en el cambio de
  `RetailerProduct` o una `admin action` masiva; el implementer elige, mientras
  cumpla D1 (asignar canónico desde Admin filtrando `unmatched`).
