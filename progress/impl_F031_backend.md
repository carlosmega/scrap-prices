# Implementación backend — F031 (Normalización de unidad)

Spec aplicada: `specs/F031-normalizacion-unidad.md`.

## Decisiones tomadas (≤5 líneas)
- Seguí la spec al pie: `mass_kg` (Decimal nullable) en `CanonicalProduct`, `sale_unit`
  (TextChoices, blank) en `RetailerProduct`; `unit_raw` conservado.
- `normaliza_precio` puro con cuantización 2dp ROUND_HALF_UP; `per_piece` se calcula
  desde el `per_kg` **sin** cuantizar (fórmula de la spec) y cada lado se cuantiza al final.
- Orden y "menor precio" de la búsqueda pasaron a `price_per_kg` (`_menor_precio_disponible`
  → `_menor_precio_por_kg`). El `price` nativo se conserva en la respuesta (transparencia).
- Seed: `mass_kg` por NMX×longitud (#3=6.684, #4=11.952, #2=1.488), `sale_unit` HD→tonelada /
  CR→kg, historial multiplicativo `[1.000,1.015,1.030]` y precios nativos base de la spec.
- Tests afectados actualizados (search/detalle/seed) **y además** `apps/lists/tests/test_api.py`,
  que hardcodeaba los precios viejos del seed (la cotización sigue en precio nativo, fuera de alcance).

## Archivos creados
- `backend/apps/catalog/normalization.py` — `normaliza_precio` puro (sin ORM/HTTP).
- `backend/apps/catalog/tests/test_normalization.py` — tabla de casos (14 casos + cuantización + tipo Decimal).
- `backend/apps/catalog/migrations/0002_canonicalproduct_mass_kg_retailerproduct_sale_unit.py` — migración commiteada.

## Archivos modificados
- `backend/apps/catalog/models.py` — `CanonicalProduct.mass_kg`; `RetailerProduct.SaleUnit` + `sale_unit`.
- `backend/apps/catalog/schemas.py` — `PriceByRetailerOut` (+`sale_unit`,`price_per_piece`,`price_per_kg`),
  `CanonicalProductRefOut`/`CanonicalProductDetailOut` (+`mass_kg`), `PriceHistoryPointOut` (+`sale_unit`).
- `backend/apps/catalog/services.py` — `_ensamblar_precio(rp, zona, mass_kg)` normaliza; orden/menor por `price_per_kg`;
  `_historial` etiqueta `sale_unit`; `detalle_producto` y `buscar` pasan `mass_kg`.
- `backend/apps/catalog/admin.py` — `mass_kg` editable en `CanonicalProductAdmin`; `sale_unit` visible/filtrable/editable en `RetailerProductAdmin`.
- `backend/apps/scraping/parsers.py` — `homedepot_sale_unit(code)` (C62→pieza, TN/TNE→tonelada, KGM→kg, MTR→m, desconocido→"").
- `backend/apps/scraping/services.py` — `_get_or_create_retailer_product` setea `sale_unit` en `defaults`.
- `backend/apps/scraping/tests/test_parsers_homedepot.py` — test parametrizado del mapeo de unidad.
- `backend/apps/core/services.py` — seed con `mass_kg`, `sale_unit` por retailer, historial multiplicativo y precios nativos base.
- `backend/apps/core/tests/test_seed.py` — asserts de `mass_kg` y `sale_unit` por retailer.
- `backend/apps/catalog/tests/test_search.py` — keys nuevas, precios nativos (#3 HD 20085.00/ton, CR 21.53/kg),
  orden por `$/kg`, y test del criterio clave (#4: HD menor `$/kg` aunque su nativo sea mayor).
- `backend/apps/catalog/tests/test_detalle.py` — `mass_kg`, `sale_unit`, normalizados y `sale_unit` en historial.
- `backend/apps/lists/tests/test_api.py` — expectativas de snapshot/line_total/subtotal al nuevo seed nativo.
- `backend/openapi.json` — regenerado.

## ¿Cambió el contrato OpenAPI?
**Sí.** Se añadieron campos a `PriceByRetailerOut` (`sale_unit`, `price_per_piece`, `price_per_kg`),
`CanonicalProductRefOut`/`CanonicalProductDetailOut` (`mass_kg`) y `PriceHistoryPointOut` (`sale_unit`).
Decimal serializado como string (igual que `price`). `backend/openapi.json` regenerado con el comando de
la spec; regeneración determinista verificada (sin drift).
**Acción para el líder:** disparar `pnpm gen:api` en frontend antes del implementer-frontend.

## Criterio de aceptación clave (verificado end-to-end)
Para la varilla #4, en Monterrey Metro: HD nativo `20085.00`/tonelada (> CR `21.53`/kg como número crudo),
pero normalizado HD `price_per_kg=20.09` < CR `21.53` → HD sale con menor `$/kg`. La comparación varía por
canónico (HD gana #3 y #4, CR gana #2): NO coincide con el número crudo más chico.

## Output REAL de las verificaciones

### `uv run ruff check .`
```
All checks passed!
```

### `uv run python manage.py makemigrations --check --dry-run`
```
No changes detected
```

### `uv run pytest -q`
```
........................................................................ [ 50%]
........................................................................ [100%]
144 passed in 2.22s
```

### Regeneración del contrato (sin drift)
```
uv run python manage.py export_openapi_schema --api config.api.api --indent 2 --output openapi.json
# (segunda regeneración) diff contra la previa: idéntico -> "NO DRIFT: regeneration is deterministic"
```

## Deuda / seguimientos detectados
- `apps/catalog/services.py:33` `_PRECIO_INFINITO` es código muerto **preexistente** (no introducido por F031);
  el sort usa `0` como sentinela. Lo dejé intacto para no salirme del alcance; candidato a limpieza aparte.
- Follow-up conocido de la spec (fuera de alcance): la cotización (`apps/lists`) sigue en precio nativo, así
  que "agregar 1" de un SKU listado por tonelada equivale a 1 tonelada en el carrito. No se resuelve aquí.
- Unidades `saco`/`m` admitidas en el enum pero `normaliza_precio` solo computa pieza/kg/tonelada (caen a None),
  por diseño de la spec.
