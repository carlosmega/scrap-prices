# F016 — API detalle de producto + historial (Django Ninja)

> Milestone M3. PRD §12 (`/api/products/{id}`), Épica B2 (detalle + historial).

## Contexto y objetivo
Desde un resultado de búsqueda, el usuario abre el detalle de un producto canónico
para comparar precios actuales por retailer en su zona y ver el **historial** de
precio (últimas lecturas). Todo desde la DB propia.

## Contrato API
| Método | Ruta | Request (query) | Response | Errores |
| ------ | ---- | --------------- | -------- | ------- |
| GET | /api/products/{id} | `zone_id` (uuid, requerido) | `ProductDetailOut` | 404 si producto o zona no existen/inactivos |

```
ProductDetailOut = {
  "canonical_product": { "id": str, "name": str, "category": str, "unit": str, "specs": object },
  "prices": PriceByRetailerOut[],     # actual: última observación por retailer en la zona (reusa F015)
  "history": PriceHistoryPointOut[]   # últimas N (default 20) observaciones en la zona, orden -captured_at
}
PriceHistoryPointOut = {
  "retailer": { "slug": str, "name": str },
  "price": str(Decimal),
  "currency": "MXN",
  "is_available": bool,
  "captured_at": datetime
}
```

- `prices` reutiliza el ensamblado "precio más fresco por retailer/zona" de F015
  (`apps/catalog/services`).
- `history` = las últimas N `PriceObservation` (de los `RetailerProduct` matcheados
  al canónico, en esa zona), ordenadas por `-captured_at`. Incluye el retailer en cada punto.
- `{id}` es el UUID del `CanonicalProduct`. 404 si no existe/ inactivo; 404 si `zone_id` inválida.

## Alcance
**Incluye:** endpoint en `apps/catalog/api.py`, schemas en `schemas.py`, lógica en
`services.py` (detalle + historial). Regenera `openapi.json`; frontend `pnpm gen:api`
(sin UI; la UI de detalle es F021).
**No incluye:** UI; gráficas; agregaciones avanzadas; paginación del historial (default N).

## Criterios de aceptación
- [ ] **Backend:** `GET /api/products/{id}?zone_id=<MTY>` (con `seed`) devuelve el
      canónico (con `specs`), `prices` por retailer (última obs) y `history` con
      varias lecturas ordenadas `-captured_at` (el seed tiene ≥2 por retailer).
- [ ] **Backend:** producto inexistente → 404; zona inexistente/inactiva → 404.
      Router sin ORM, lógica en `services.py`, `response=` explícito.
- [ ] **Backend:** tests del happy path (detalle + historial no vacío), del 404 de
      producto y del 404 de zona; fallan sin la implementación.
- [ ] **Backend:** `openapi.json` regenerado. **Contrato:** `pnpm gen:api`, Fase 5 sin drift.
- [ ] `./init.sh` verde; ruff/pytest/tsc/lint/build limpios.

## Plan de verificación
```bash
cd backend && uv run python manage.py seed && uv run pytest apps/catalog -q
uv run python manage.py export_openapi_schema --api config.api.api --indent 2 --output openapi.json
cd ../frontend && pnpm gen:api && cd .. && ./init.sh
```

## Notas y decisiones abiertas
- Historial combinado (todos los retailers) ordenado por fecha; la UI (F021) puede
  agrupar por retailer si conviene. N por defecto = 20 (suficiente para MVP).
- `specs` (JSON del canónico) se expone tal cual para que la UI muestre calibre/diámetro/etc.
