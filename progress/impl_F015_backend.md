# impl F015 — backend (API de búsqueda)

## Spec aplicada y decisiones
Spec: `specs/F015-api-busqueda.md` (M3, `/api/search`). Decisiones:
- Schemas EXACTOS de la spec en `apps/catalog/schemas.py` (`SearchResultOut`,
  `PriceByRetailerOut`, anidados `RetailerRefOut`/`CanonicalProductRefOut`). `price`
  es `Decimal | None` → se serializa como string del Decimal (exactitud monetaria).
- Precio más fresco por retailer/zona reutiliza `apps.prices.services.ultima_observacion`.
- `q` tolerante a acentos: normalización NFKD + strip de diacríticos en memoria
  (SQLite, sin Postgres FTS); `sort=price` (menor precio disponible, sin-precio al
  final) y `sort=name` (alfabético, también acento-insensible).
- 404: el service devuelve `None` si la zona no existe o está inactiva
  (`is_active=False`); el router lo traduce a `HttpError(404)`. Router SIN ORM ni
  import de models (cumple ruff banned-api e import-linter).

## Archivos creados/modificados
- `backend/apps/catalog/schemas.py` (nuevo): schemas del contrato.
- `backend/apps/catalog/services.py` (nuevo): búsqueda + ensamblado + orden.
- `backend/apps/catalog/api.py` (nuevo): router `/search`, delega en services.
- `backend/apps/catalog/tests/test_search.py` (nuevo): 9 tests.
- `backend/config/api.py` (mod): monta `catalog_router` → ruta `/api/search`.
- `backend/openapi.json` (regenerado): incluye `/api/search` y los schemas nuevos.

## ¿Cambió el contrato OpenAPI?
SÍ. `backend/openapi.json` regenerado con `export_openapi_schema`. Contiene
`/api/search` (params `q` requerido, `zone_id` requerido, `sort` default `price`),
`SearchResultOut`, `PriceByRetailerOut`, `RetailerRefOut`, `CanonicalProductRefOut`.
ACCIÓN PARA EL LÍDER: disparar `pnpm gen:api` en frontend antes del implementer-frontend.

## Output REAL de verificaciones

### `uv run ruff check .`
```
All checks passed!
```

### `uv run python manage.py makemigrations --check --dry-run`
```
No changes detected
```

### `uv run pytest apps/catalog -q`
```
..................                                                       [100%]
exit=0
```
(Detalle con reporte completo — `-o addopts=""`:)
```
collected 18 items

apps\catalog\tests\test_models.py .........                              [ 50%]
apps\catalog\tests\test_search.py .........                              [100%]

============================= 18 passed in 0.74s ==============================
```

### Suite completa (sanidad, no se rompió nada)
```
collected 53 items
...
============================= 53 passed in 1.44s ==============================
```

### Regla de capas (import-linter)
```
Routers (api) no importan models directamente; delegan en services KEPT
Contracts: 1 kept, 0 broken.
```

## Confirmación de contrato
`backend/openapi.json` contiene `/api/search` (línea 92), `SearchResultOut`,
`PriceByRetailerOut`, `RetailerRefOut`, `CanonicalProductRefOut` (verificado por grep).

## Deuda / seguimientos
- Búsqueda en SQLite: el filtro acento-insensible itera canónicos en memoria
  (suficiente para el dataset MVP). Postgres FTS (`unaccent`/`SearchVector`) +
  paginación quedan para M5, como indica la spec.
- `sort` se acepta como string libre; valores distintos de `name` caen en el
  comportamiento `price` por defecto. No se valida con enum (la spec no lo exige);
  podría endurecerse a `Literal["price","name"]` si el reviewer lo pide.
- NO se corrió `./init.sh` completo: la Fase 5 (drift de contrato) queda roja hasta
  que el frontend corra `pnpm gen:api`.
