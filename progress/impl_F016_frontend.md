# impl_F016_frontend — Capa frontend (paso de contrato)

**Spec aplicada:** `specs/F016-api-detalle-producto.md` (Milestone M3, detalle de
producto + historial).

## Decisiones de UI/UX

- Tarea de **contrato puro, SIN UI** (la UI de detalle es F021): el único cambio
  es regenerar `src/lib/api/schema.d.ts` con `pnpm gen:api` desde el
  `backend/openapi.json` ya actualizado por backend.
- No se añadieron helpers, componentes ni `features/` nuevos: no eran necesarios
  y habrían sido alcance de F021.
- Sin `fetch` fuera de `client.ts`, sin `any`, sin tipos de API declarados a mano.

## Archivos creados/modificados

- **Modificado (generado, no a mano):** `frontend/src/lib/api/schema.d.ts`
  - Nuevos tipos expuestos por el contrato: `ProductDetailOut`,
    `CanonicalProductDetailOut`, `PriceHistoryPointOut` y la ruta
    `GET /api/products/{id}` con `response = ProductDetailOut`.

Componentes shadcn añadidos: **ninguno**.

## Output REAL de verificaciones

### `pnpm gen:api`
```
$ openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts
✨ openapi-typescript 7.13.0
🚀 ../backend/openapi.json → src/lib/api/schema.d.ts [35.2ms]
```

Tipos nuevos confirmados en `schema.d.ts`:
```
89:    "/api/products/{id}": {
214:        CanonicalProductDetailOut: {
236:        PriceHistoryPointOut: {
261:        ProductDetailOut: {
262:            canonical_product: components["schemas"]["CanonicalProductDetailOut"];
266:            history: components["schemas"]["PriceHistoryPointOut"][];
384:                    "application/json": components["schemas"]["ProductDetailOut"];
```

### Control de drift (2º `pnpm gen:api` deja schema.d.ts idéntico)
```
$ openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts
✨ openapi-typescript 7.13.0
🚀 ../backend/openapi.json → src/lib/api/schema.d.ts [45ms]

=== HASH AFTER 1st GEN ===
18ae78ed12b2fd32e0457250d49b728799ef4ac5142abf8325e3b6b3d6f00cb6 *src/lib/api/schema.d.ts
=== HASH AFTER 2nd GEN ===
18ae78ed12b2fd32e0457250d49b728799ef4ac5142abf8325e3b6b3d6f00cb6 *src/lib/api/schema.d.ts

=== DRIFT DIFF (empty = no drift) ===
DRIFT CONTROL: NO DIFFERENCES (identical)
```
Hash idéntico tras ambas corridas y `diff` vacío → **sin drift**.

### `pnpm exec tsc --noEmit`
```
===== tsc --noEmit =====
TSC_EXIT=0
```
(salida vacía, exit 0 → limpio)

### `pnpm lint`
```
===== lint =====
$ eslint
LINT_EXIT=0
```
(sin warnings ni errores)

### `pnpm build`
```
$ next build
   ▲ Next.js 15.5.19
   - Environments: .env.local

   Creating an optimized production build ...
 ✓ Compiled successfully in 4.5s
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/5) ...
 ✓ Generating static pages (5/5)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    73.8 kB         176 kB
└ ○ /_not-found                            990 B         103 kB
+ First Load JS shared by all             102 kB
BUILD_EXIT=0
```

### `pnpm test:unit`
```
$ vitest run
 ✓ src/app/page.test.tsx (2 tests) 138ms

 Test Files  1 passed (1)
      Tests  2 passed (2)
TESTUNIT_EXIT=0
```

## Deuda / seguimientos

- **F021** consumirá estos tipos para la UI de detalle (gráfica de historial,
  precios por retailer). No hay `features/products/api.ts` aún: se creará allí,
  pasando por `lib/api/client.ts`.
- No se ejecutó `e2e/` porque esta feature no toca la capa E2E (es solo contrato).
