# Implementación frontend + e2e — F031 (Normalización de unidad)

Spec aplicada: `specs/F031-normalizacion-unidad.md`.

## Decisiones de UI/UX (≤5 líneas)
- Primer paso `pnpm gen:api`: `schema.d.ts` trajo `sale_unit`/`price_per_piece`/
  `price_per_kg` (PriceByRetailerOut), `mass_kg` (canónico) y `sale_unit` (historial).
  Cero tipos de API a mano (regla 1).
- Por fila de retailer: **titular** `$/pieza` (`price_per_piece`), **secundario** chico
  con el **nativo** "listado a $X / ton" (`price`+`sale_unit`) y el `$/kg` (base de comparación).
- **Orden** por `price_per_kg` ascendente (sin él al final); fila de menor `$/kg` marcada
  con badge **"mejor precio"** (`best-price-badge`) para E2E. Reusé `Badge` de shadcn ya instalado.
- **Fallback "sin normalizar"**: si `price_per_piece` y `price_per_kg` son null pero hay precio,
  cae al nativo y muestra la nota. Conservé frescura, disponibilidad, "sin precio en tu zona" y "Agregar".
- E2E nuevo en `1/2"` (#4): el match del backend es substring del nombre, así que `1/2"` aísla la varilla #4.

## Archivos creados
- `frontend/src/features/search/format.test.ts` — vitest de los helpers puros (orden por `$/kg`,
  mejor precio, formatos titular/nativo/`$/kg`, mapeo de `sale_unit`). 18 casos.
- `e2e/tests/normalization.spec.ts` — criterio clave F031 (varilla 1/2", Monterrey Metro).

## Archivos modificados
- `frontend/src/lib/api/schema.d.ts` — REGENERADO por `pnpm gen:api` (no a mano).
- `frontend/src/features/search/format.ts` — `sortPricesAsc` ahora ordena por `price_per_kg`
  (genérico, sin él al final); nuevos: `saleUnitLabel`, `formatPricePerPiece`,
  `formatPricePerKg`, `formatNativePrice`, `bestPriceIndex`.
- `frontend/src/features/search/components/result-card.tsx` — titular `$/pieza`, secundario
  nativo + `$/kg`, badge "mejor precio", fallback "sin normalizar"; nuevos data-testids
  (`best-price-badge`, `retailer-native-price`, `retailer-price-per-kg`, `retailer-unnormalized`).
- `frontend/src/features/products/components/product-prices.tsx` — paridad con la tarjeta
  (`product-best-price-badge`, `product-retailer-native-price`, `product-retailer-price-per-kg`,
  `product-retailer-unnormalized`); conserva enlace externo, frescura y "Agregar".
- `e2e/tests/search.spec.ts` — la aserción de orden pasó de "primer titular = mínimo titular"
  (inválida con F031) a "primer `$/kg` = mínimo `$/kg` de la tarjeta" + badge en la 1ª fila.

## Componentes shadcn añadidos
- Ninguno nuevo: `Badge` (`src/components/ui/badge.tsx`) ya estaba instalado por CLI; solo se importó.

## Output REAL de las verificaciones

### `pnpm gen:api`
```
$ openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts
✨ openapi-typescript 7.13.0
🚀 ../backend/openapi.json → src/lib/api/schema.d.ts [53ms]
```

### `pnpm exec tsc --noEmit`
```
tsc: OK (sin salida = sin errores)
```

### `pnpm lint`
```
$ eslint
lint: OK
```
(eslint sin findings)

### `pnpm build`
```
   ▲ Next.js 15.5.19
 ✓ Compiled successfully in 9.0s
   Linting and checking validity of types ...
 ✓ Generating static pages (6/6)
Route (app)                                 Size  First Load JS
┌ ○ /                                    32.5 kB         152 kB
├ ○ /_not-found                            990 B         103 kB
├ ○ /cotizacion                          1.93 kB         121 kB
└ ƒ /products/[id]                       4.32 kB         124 kB
```

### `pnpm exec vitest run`
```
 ✓ src/features/search/relative-time.test.ts (9 tests)
 ✓ src/features/lists/session.test.ts (6 tests)
 ✓ src/features/zones/hooks/use-selected-zone.test.ts (5 tests)
 ✓ src/features/search/format.test.ts (18 tests)
 ✓ src/app/page.test.tsx (3 tests)
 Test Files  5 passed (5)
      Tests  41 passed (41)
```

### E2E — `pnpm exec playwright test` (toda la suite, e2e/)
```
  7 passed (1.2m)
```
Incluye `normalization.spec.ts` (nuevo): para "varilla 1/2"" en Monterrey Metro, Home Depot
sale marcado **mejor precio** (menor `$/kg`) y su nativo **"$.../ ton"** es visible, pese a que
su número nativo (~$20k/ton) es MAYOR que el de Construrama (~$21/kg). `search.spec.ts` y
`detail.spec.ts` pasan con el nuevo orden por `$/kg`.

Nota operativa: había un dev server STALE colgado en :3300 de una sesión previa (PID huérfano,
servía contenido viejo sin los testids) que causaba EADDRINUSE; lo terminé para que Playwright
levantara un frontend fresco. No es un cambio de código.

## Deuda / seguimientos detectados
- `quote.spec.ts` mostró flakiness puntual (1 retry) en una corrida; pasó verde en la corrida
  completa final. No toca testids de F031; es flaky preexistente de navegación al carrito (no de esta capa).
- Follow-up heredado de la spec (fuera de alcance, capa lists): la cotización sigue en precio
  nativo, así que "Agregar 1" de un SKU listado por tonelada = 1 tonelada en el carrito. No se
  resuelve aquí; ya documentado por backend.
- Unidades `saco`/`m`: `saleUnitLabel` las muestra tal cual y caen al fallback "sin normalizar"
  cuando el backend devuelve `price_per_*` null (por diseño de la spec).
```
