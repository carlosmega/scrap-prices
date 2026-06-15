# impl F029 backend — HD búsqueda: profileName + marketId/stLocId

Spec: `specs/F029-hd-busqueda-params.md`.

## Spec aplicada y decisiones (máx. 5 líneas)
- Añadido `RetailerLocation.extra = JSONField(default=dict, blank=True)` (params de routing genéricos por retailer) + migración `0002`.
- `seed_demo`: la location HD Monterrey fija `extra={"market_id":"10","st_loc_id":"18503"}` en los `defaults` del `update_or_create` (idempotente); `external_id` sigue `1333`.
- Adapter: `set_zone` captura `market_id`/`st_loc_id` de `location.extra`; `_build_search_url` añade `marketId` (de extra) y `stLocId` (de extra, id interno) además del `profileName`/`limit`/`offset` ya presentes. `physicalStoreId` sigue saliendo de `external_id`.
- Fallback razonable: si `extra` no trae esos valores, se OMITEN `marketId`/`stLocId` (antes `stLocId` se ponía igual a `external_id`); la URL no revienta.
- Contrato OpenAPI sin cambios (campo de modelo no expuesto en ningún schema de geo).

## Archivos creados/modificados
- `backend/apps/geo/models.py` (modificado): campo `extra`.
- `backend/apps/geo/migrations/0002_retailerlocation_extra.py` (creado): AddField `extra`.
- `backend/apps/core/services.py` (modificado): `extra` en seed de HD Monterrey.
- `backend/apps/scraping/homedepot.py` (modificado): `set_zone` lee extra; `_build_search_url` emite `marketId`/`stLocId` desde extra; docstrings.
- `backend/apps/scraping/tests/test_homedepot.py` (modificado): 2 tests nuevos de `_build_search_url` (con extra → profileName/marketId=10/stLocId=18503/physicalStoreId=1333/searchTerm/limit/offset vía `parse_qs`; sin extra → omite marketId/stLocId sin reventar).
- `backend/apps/core/tests/test_seed.py` (modificado): asserts de `extra` esperado en la location HD (creación + idempotencia).

## ¿Cambió el contrato OpenAPI?
NO. `extra` es un campo de modelo no referenciado por ningún schema Ninja; no hay rutas/params nuevos. No se regeneró `openapi.json` (no aplica).

## Output REAL de las verificaciones

### `uv run python manage.py makemigrations`
```
Migrations for 'geo':
  apps\geo\migrations\0002_retailerlocation_extra.py
    + Add field extra to retailerlocation
```

### `uv run python manage.py makemigrations --check --dry-run`
```
No changes detected
EXIT=0
```

### `uv run python manage.py migrate`
```
Operations to perform:
  Apply all migrations: admin, auth, catalog, contenttypes, geo, lists, prices, sessions
Running migrations:
  Applying geo.0002_retailerlocation_extra... OK
EXIT=0
```

### `uv run python manage.py seed`
```
Seed demo aplicado (idempotente).
  retailers: 2
  locations: 2
  zones: 1
  zone_maps: 2
  categories: 1
  canonical_products: 3
  retailer_products: 6
  observations: 18
  observations_created: 0
EXIT=0
```

### `uv run ruff check .`
```
All checks passed!
EXIT=0
```

### `uv run pytest apps -q`
```
........................................................................ [ 60%]
................................................                         [100%]
120 passed in 4.50s
```

## Deuda / seguimientos
- El test offline `hd_setup` usa `external_id="18503"` (no representa la tienda real, donde 18503 es el stLocId interno y 1333 el external_id/physicalStoreId). No se tocó para no romper la ingestión existente; el shape correcto sí se ejercita en los tests nuevos de `_build_search_url`. Sin impacto funcional.
- Confirmación en vivo del `--dry-run` (≈13 varillas) la hace el líder con red; CI sigue 100% offline (MockTransport/fixtures).
- `extra` queda disponible para F026 (Construrama: distribuidor/ciudad).
