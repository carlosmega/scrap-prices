# F015 — API de búsqueda (Django Ninja)

> Milestone M3. Deriva del PRD §12 (`/api/search`), Épica B1, RF3/RF4.
> Capacidad central de ConstruScan: buscar un producto y ver sus precios por
> retailer en una zona, desde la DB propia (nunca en vivo).

## Contexto y objetivo
El usuario busca "varilla 3/8" en su zona y obtiene productos canónicos con el
**precio más fresco por retailer** en esa zona, con frescura visible. Consulta
SOLO la DB propia (principio no negociable del PRD §1/B1·CA1).

## Contrato API
| Método | Ruta | Request (query) | Response | Errores |
| ------ | ---- | --------------- | -------- | ------- |
| GET | /api/search | `q` (str, requerido), `zone_id` (uuid, requerido), `sort` (`price`\|`name`, default `price`) | `SearchResultOut[]` | 404 si `zone_id` no existe / inactiva |

```
SearchResultOut = {
  "canonical_product": { "id": str, "name": str, "category": str, "unit": str },
  "prices": PriceByRetailerOut[]   # un item por retailer con producto en la zona
}
PriceByRetailerOut = {
  "retailer": { "slug": str, "name": str },
  "retailer_product_id": str,
  "price": str(Decimal) | null,    # null si no disponible/sin observación
  "currency": "MXN",
  "is_available": bool,
  "captured_at": datetime | null,  # frescura (RNF3) — última observación
  "url": str
}
```

- "Precio por retailer en la zona" = **última `PriceObservation`** (más reciente por
  `captured_at`) de cada `RetailerProduct` matcheado al canónico, en esa `zone`.
  Reutiliza el patrón de `apps/prices/services.py` (F008, `ultima_observacion`).
- Búsqueda `q`: full-text simple en español **tolerante a acentos** sobre
  `CanonicalProduct.name` (y opcionalmente `RetailerProduct.raw_name`). En SQLite,
  `icontains` + normalización de acentos es suficiente para MVP (Postgres FTS llega
  con la migración a Postgres / M5).
- `sort=price` ordena por el menor precio disponible entre retailers; `sort=name` por nombre.
- Si un retailer no tiene el producto/observación en la zona → se indica
  (`price=null`, `is_available=false`) — Épica B1·CA5.

## Alcance
**Incluye:** endpoint `/api/search` en `apps/catalog/api.py` (o módulo de búsqueda),
schemas en `schemas.py`, lógica en `services.py` (búsqueda + ensamblado de precios
por retailer + orden). Regenera `openapi.json`; frontend `pnpm gen:api` (sin UI; la
UI es F020).
**No incluye:** UI; Postgres FTS; ranking avanzado; paginación (si el dataset crece,
feature posterior).

## Criterios de aceptación
- [ ] **Backend:** `GET /api/search?q=varilla&zone_id=<MTY>` (con `seed`) devuelve los
      canónicos de varilla, cada uno con precios de Home Depot y Construrama y su
      `captured_at` (frescura); usa la **última** observación por retailer/zona.
- [ ] **Backend:** `q` tolerante a acentos (p.ej. "varilla" encuentra resultados);
      `sort=price` ordena por menor precio; retailer sin observación → `price=null`,
      `is_available=false`.
- [ ] **Backend:** `zone_id` inexistente/inactiva → 404. Lógica en `services.py`,
      router sin ORM, `response=` explícito.
- [ ] **Backend:** tests del happy path (varilla en MTY con ambos retailers), del
      orden por precio, del retailer-sin-precio y del 404; fallan sin la implementación.
- [ ] **Backend:** `openapi.json` regenerado. **Contrato:** `pnpm gen:api`, Fase 5 sin drift.
- [ ] `./init.sh` verde; ruff/pytest/tsc/lint/build limpios.

## Plan de verificación
```bash
cd backend && uv run python manage.py seed && uv run pytest apps/catalog -q
uv run python manage.py export_openapi_schema --api config.api.api --indent 2 --output openapi.json
cd ../frontend && pnpm gen:api && cd .. && ./init.sh   # Fase 5 sin drift, verde
```

## Notas y decisiones abiertas
- Frescura: cada precio lleva `captured_at`; la UI (F020) muestra "actualizado hace X".
- Búsqueda real en Postgres (FTS con `unaccent`/`SearchVector`) se adopta al migrar a
  Postgres; en SQLite el MVP usa `icontains` + normalización de acentos en Python/ORM.
