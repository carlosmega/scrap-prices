# impl_F021_frontend — UI: detalle de producto + historial de precio

Spec aplicada: `specs/F021-ui-detalle-producto.md` (capas frontend + e2e).

## Decisiones de UI/UX (≤5 líneas)
- Ruta `app/products/[id]/page.tsx`: Server Component delgado que lee `id` (en Next 15
  `params` es `Promise`) y compone el organismo `<ProductDetail />` (Client) — `"use client"`
  vive solo en `ProductDetail` y en el hook, lo más abajo posible.
- Tres tarjetas: canónico + `specs` (pares clave/valor), precios actuales por retailer
  (precio, frescura "actualizado hace X" reusando `freshnessLabel` de F020, disponibilidad,
  enlace a `url` con `target=_blank rel=noopener noreferrer`) e historial (reciente→antiguo).
- Estados explícitos: no-zona (invita a elegir) / cargando / error / no-encontrado (404) / datos.
- Resultados de F020 enlazan al detalle: el título de `ResultCard` es un `next/link` a `/products/{id}`.
- `specs` libre del contrato (`{ [key: string]: unknown }`) se aplana sin inventar estructura;
  etiquetas legibles para claves conocidas (calibre/diámetro/longitud), raw para el resto.

## Contrato / cliente tipado
El endpoint `GET /api/products/{id}` lleva **param de ruta `{id}` + query `zone_id`**, combo
que los helpers existentes (`apiGet`/`apiGetQuery`) no cubrían (solo path literal o query).
Se añadió a `src/lib/api/client.ts` el helper tipado `apiGetPath(path, params, query?, options?)`
que sustituye `{…}` en la plantilla y serializa la query, derivando TODOS los tipos del contrato
(path params, query y respuesta) desde `schema.d.ts`. Cero `any`, cero tipos a mano, `fetch`
sigue solo en `client.ts`. NO se regeneró `gen:api`: `ProductDetailOut`/`PriceHistoryPointOut`
ya existían en el contrato (Fase 5 de init.sh confirma sin drift).

## Archivos
Creados:
- `frontend/src/app/products/[id]/page.tsx` — ruta App Router (Server Component).
- `frontend/src/features/products/api.ts` — `fetchProductDetail(id, zoneId)`.
- `frontend/src/features/products/types.ts` — tipos derivados del contrato.
- `frontend/src/features/products/format.ts` — `specEntries`, `formatHistoryDate`.
- `frontend/src/features/products/hooks/use-product-detail.ts` — estados no-zone/loading/ready/not-found/error.
- `frontend/src/features/products/components/product-detail.tsx` — organismo Client (`"use client"`).
- `frontend/src/features/products/components/product-specs.tsx`
- `frontend/src/features/products/components/product-prices.tsx`
- `frontend/src/features/products/components/product-history.tsx`
- `e2e/tests/detail.spec.ts` — búsqueda → detalle → precios por retailer + historial.

Modificados:
- `frontend/src/lib/api/client.ts` — nuevo helper `apiGetPath` + tipos de path params (sección
  de `fetch` permitido sin cambios de regla).
- `frontend/src/features/search/components/result-card.tsx` — título envuelto en `next/link` a `/products/{id}`.

Componentes shadcn añadidos: **ninguno**. Se reutilizan los ya instalados (`card`, `button` con
`asChild` para el enlace "volver"); se reaprovechan helpers del dominio search
(`formatPrice`/`sortPricesAsc`/`freshnessLabel`).

## Output REAL de verificación

### `pnpm exec tsc --noEmit`
```
=== tsc ===
EXIT=0
```
(sin salida = sin errores)

### `pnpm lint`
```
$ eslint
EXIT=0
```
(sin salida de eslint = sin errores ni warnings)

### `pnpm build`
```
$ next build
   ▲ Next.js 15.5.19
   - Environments: .env.local

   Creating an optimized production build ...
 ✓ Compiled successfully in 3.0s
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/5) ...
 ✓ Generating static pages (5/5)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    30.9 kB         150 kB
├ ○ /_not-found                            990 B         103 kB
└ ƒ /products/[id]                       2.53 kB         121 kB
+ First Load JS shared by all             102 kB

○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
EXIT=0
```

### `pnpm test:unit` (frontend)
```
 RUN  v3.2.6 C:/scrap-prices/frontend

 ✓ src/features/search/relative-time.test.ts (9 tests) 5ms
 ✓ src/features/zones/hooks/use-selected-zone.test.ts (5 tests) 28ms
 ✓ src/app/page.test.tsx (3 tests) 82ms

 Test Files  3 passed (3)
      Tests  17 passed (17)
```

### `pnpm test:e2e` (desde e2e/)
```
Running 4 tests using 4 workers
[1/4] [chromium] › tests\smoke.spec.ts:9:5 › la home carga y el indicador de salud muestra ok
[2/4] [chromium] › tests\zone.spec.ts:11:5 › elegir zona y que persista tras recargar
[3/4] [chromium] › tests\search.spec.ts:19:5 › buscar varilla en Monterrey Metro: ambos retailers y orden por precio
[4/4] [chromium] › tests\detail.spec.ts:13:5 › desde la búsqueda al detalle: precios por retailer e historial
[WebServer] "GET /api/products/160623a6-...?zone_id=615b0e10-... HTTP/1.1" 200 1746
  4 passed (25.0s)
```

### `./init.sh --e2e` (raíz) — Fase 6 verde
```
── Fase 4 · Frontend (Next.js + Tailwind + shadcn) ──
  ✔ pnpm install
  ✔ tsc --noEmit
  ✔ lint
  ✔ tests unitarios (vitest)
  ✔ build de producción
  ✔ arquitectura: fetch solo en src/lib/api/client.ts

── Fase 5 · Contrato OpenAPI → tipos TS ──
  ✔ tipos TS sincronizados con backend/openapi.json

── Fase 6 · E2E (Playwright) ──
  ✔ pnpm install
  ✔ suite Playwright

════════ Resumen ════════
  ✔ 33 ok   ✘ 0 fallos   ◌ 3 pendientes
  VERDE — el arnés está en estado consistente.
```

## Deuda / seguimientos
- `apiGetPath` es el primer consumidor de rutas con param de ruta (`/api/lists/{list_id}`,
  `/api/products/{id}`). Queda disponible y tipado para F022 (listas de cotización) sin más cambios.
- El detalle no incluye gráfica de historial (fuera de alcance por spec: lista basta para MVP).
- "Agregar a lista/cotización" desde el detalle lo cablea F022 (no incluido aquí).
- El backend ordena `history` por `-captured_at`; el componente reordena de forma defensiva
  por si el orden de red cambiara. Sin impacto funcional.
