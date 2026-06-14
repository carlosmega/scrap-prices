# impl_F018_frontend — API de retailers (paso de contrato)

Spec aplicada: `specs/F018-api-retailers.md` (capa frontend = solo paso de contrato).

## Decisiones de UI/UX

- Sin UI (alcance de la spec: "No incluye UI"). Solo se regeneró el contrato.
- Se añadió un helper de dominio trivial `features/retailers/api.ts` (`fetchRetailers()`),
  siguiendo el patrón exacto de `features/zones/api.ts` y `features/health/api.ts`:
  envuelve `apiGet("/api/retailers")`, sin `fetch` propio y sin `any`; el tipo del
  resultado (`RetailerOut[]`) se infiere del contrato generado.
- El tipo `RetailerOut` salió íntegro de `schema.d.ts` (generado), no a mano:
  campos `id/name/slug/pricing_model/scraper_status` (string), `is_active` (boolean),
  todos requeridos — coincide con la tabla del contrato de la spec.

## Archivos creados/modificados

- `frontend/src/lib/api/schema.d.ts` — REGENERADO con `pnpm gen:api` (ahora incluye
  la ruta `/api/retailers` y el schema `RetailerOut`; antes solo existía
  `PriceByRetailerOut`).
- `frontend/src/features/retailers/api.ts` — CREADO. Helper `fetchRetailers()`.

Componentes shadcn añadidos: ninguno.

## Output REAL de verificaciones

### pnpm gen:api

```
$ openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts
✨ openapi-typescript 7.13.0
🚀 ../backend/openapi.json → src/lib/api/schema.d.ts [140ms]
```

### pnpm exec tsc --noEmit

```
EXIT_CODE=0
```

(salida vacía, sin errores de tipos)

### pnpm lint

```
$ eslint
EXIT_CODE=0
```

### pnpm build

```
$ next build
   ▲ Next.js 15.5.19
   - Environments: .env.local

   Creating an optimized production build ...
 ✓ Compiled successfully in 4.2s
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/5) ...
 ✓ Generating static pages (5/5)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    73.9 kB         176 kB
└ ○ /_not-found                            990 B         103 kB
+ First Load JS shared by all             102 kB

○  (Static)  prerendered as static content

EXIT_CODE=0
```

### pnpm test:unit

```
$ vitest run
 RUN  v3.2.6 C:/scrap-prices/frontend

 ✓ src/app/page.test.tsx (2 tests) 135ms

 Test Files  1 passed (1)
      Tests  2 passed (2)

EXIT_CODE=0
```

### Control de drift (2º gen:api idéntico)

SHA-256 antes y después del segundo `pnpm gen:api`, más `diff`:

```
f7eadda1b4d8620c518b1149c4026e4207023d470a690f7680c4235e599454f5 *src/lib/api/schema.d.ts
$ openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts
✨ openapi-typescript 7.13.0
🚀 ../backend/openapi.json → src/lib/api/schema.d.ts [139.8ms]
---SECOND GEN DONE---
f7eadda1b4d8620c518b1149c4026e4207023d470a690f7680c4235e599454f5 *src/lib/api/schema.d.ts
DRIFT_CHECK=IDENTICAL_NO_DRIFT
```

Hash idéntico y `diff` sin diferencias → sin drift contra `backend/openapi.json`.

## Deuda / seguimientos

- Sin UI todavía (esperado por la spec). La pantalla de diagnóstico de scrapers que
  consuma `fetchRetailers()` queda pendiente para una feature futura.
- Deuda de seguridad heredada del backend (anotada en la spec): el endpoint es
  público en MVP; cuando exista login/roles deberá protegerse (admin/staff). El
  frontend no añade auth a la llamada por ahora.
