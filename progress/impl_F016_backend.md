# impl F016 backend — API detalle de producto + historial

## Spec aplicada y decisiones
Spec: `specs/F016-api-detalle-producto.md`. Implementado `GET /api/products/{id}?zone_id=<uuid>`
→ `ProductDetailOut`. Reusé el ensamblado "precio más fresco por retailer/zona" de F015
(`_ensamblar_precio` + `ultima_observacion`) para `prices`. `history` = últimas N=20
`PriceObservation` de los `RetailerProduct` activos matcheados al canónico, en la zona,
orden `-captured_at`, cada punto con su retailer. 404 si canónico no existe/inactivo o
si zona no existe/inactiva (service devuelve None; router traduce a `HttpError(404)`).
`specs` del canónico se exponen tal cual vía nuevo `CanonicalProductDetailOut`.

## Archivos creados/modificados
- `backend/apps/catalog/schemas.py` (mod): + `CanonicalProductDetailOut`, `PriceHistoryPointOut`, `ProductDetailOut`.
- `backend/apps/catalog/services.py` (mod): + `detalle_producto()` y helper `_historial()`; imports y `_HISTORIAL_DEFAULT=20`.
- `backend/apps/catalog/api.py` (mod): + ruta `GET /products/{id}` (router ya montado en `config/api.py` → queda `/api/products/{id}`). Sin ORM, `response=ProductDetailOut`.
- `backend/apps/catalog/tests/test_detalle.py` (nuevo): happy path (prices ambos retailers + history no vacío ordenado), 404 producto inexistente, 404 producto inactivo, 404 zona inexistente, 404 zona inactiva.
- `backend/openapi.json` (regenerado).

## ¿Cambió el contrato OpenAPI?
SÍ. `openapi.json` regenerado: contiene `/api/products/{id}` (path `id` requerido + query
`zone_id` requerido, response `ProductDetailOut`) y los schemas `ProductDetailOut`,
`PriceHistoryPointOut`, `CanonicalProductDetailOut`.
**Acción para el líder:** disparar `pnpm gen:api` en frontend antes del implementer-frontend.

## Output REAL de las verificaciones

### `uv run ruff check .`
```
All checks passed!
```

### `uv run python manage.py makemigrations --check --dry-run`
```
No changes detected
```

### `uv run pytest apps/catalog -q` (classic style)
```
.......................

23 passed in 1.16s
```

### `uv run pytest` (suite completa)
```
..........................................................

58 passed in 1.17s
```

### Verificación del contrato (`openapi.json`)
```
148:    "/api/products/{id}": {
178:                  "$ref": "#/components/schemas/ProductDetailOut"
381:      "CanonicalProductDetailOut": {
416:      "PriceHistoryPointOut": {
451:      "ProductDetailOut": {
```

## Deuda / seguimientos
- Sin paginación del historial (default N=20, fuera de alcance por spec). Con el seed
  actual hay 6 puntos por canónico (3 capturas × 2 retailers), muy por debajo de N.
- El service no valida formato UUID de `id`/`zone_id`; un UUID con formato inválido
  podría propagar un error de DB en vez de 404 (los tests usan UUIDs bien formados,
  igual que F015 en `/search`). Consistente con el comportamiento existente de F015.
- Frontend debe regenerar tipos (`pnpm gen:api`) — el contrato cambió.
