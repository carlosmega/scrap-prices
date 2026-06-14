# impl F014 — Frontend (paso de contrato)

Spec: `specs/F014-api-zonas.md`. Capa frontend = sincronizar el contrato tras
los nuevos endpoints `/api/zones` y `/api/zones/resolve`. SIN UI (la UI de
selección de zona es F019).

## Decisiones de UI/UX

- Sin UI por diseño: solo se sincroniza el contrato (`schema.d.ts`) y se añade
  un helper de dominio mínimo.
- Helper `fetchZones()` para `GET /api/zones`, espejo de `health/api.ts`: usa el
  `apiGet` existente; el tipo de respuesta (`ZoneOut[]`) se infiere del contrato,
  cero `any`, ningún `fetch` fuera de `client.ts`.
- NO se añadió helper para `POST /api/zones/resolve`: el cliente solo expone
  `apiGet` (no hay `apiPost`); añadir uno tocaría `client.ts` y excede el alcance
  trivial de F014. Se difiere a F019 (UI), que consumirá el POST.

## Archivos creados/modificados

- `frontend/src/lib/api/schema.d.ts` — REGENERADO con `pnpm gen:api` (no a mano).
  Ahora incluye `ZoneOut`, `ResolveIn` y los paths `/api/zones` y
  `/api/zones/resolve`.
- `frontend/src/features/zones/api.ts` — NUEVO. Helper tipado `fetchZones()`
  (GET `/api/zones`) usando `apiGet` + tipos generados.

Componentes shadcn añadidos: ninguno.

## Output REAL de las verificaciones

### `pnpm gen:api` (1ª regeneración)
```
$ openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts
✨ openapi-typescript 7.13.0
🚀 ../backend/openapi.json → src/lib/api/schema.d.ts [36.7ms]
```
schema.d.ts ahora contiene `ZoneOut`, `ResolveIn` y las rutas
`/api/zones` (GET) y `/api/zones/resolve` (POST).

### `pnpm exec tsc --noEmit`
```
===== tsc =====
EXIT:0
```

### `pnpm lint`
```
===== lint =====
$ eslint
EXIT:0
```

### `pnpm build`
```
$ next build
   ▲ Next.js 15.5.19
   - Environments: .env.local

   Creating an optimized production build ...
 ✓ Compiled successfully in 3.7s
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
  ├ chunks/360-9e1ffefdc97ad6f3.js       45.8 kB
  ├ chunks/e5baef3c-20d656520f724785.js  54.2 kB
  └ other shared chunks (total)          1.96 kB

○  (Static)  prerendered as static content
EXIT:0
```

### `pnpm test:unit`
```
$ vitest run
 RUN  v3.2.6 C:/scrap-prices/frontend

 ✓ src/app/page.test.tsx (2 tests) 118ms

 Test Files  1 passed (1)
      Tests  2 passed (2)
EXIT:0
```

## Control de drift (2ª `pnpm gen:api`)
```
$ openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts
✨ openapi-typescript 7.13.0
🚀 ../backend/openapi.json → src/lib/api/schema.d.ts [25.7ms]
sha before: bbc335838dc3891d7046cb1c2478f807fe42189817e961e1d5374d7be1d14992
sha after : bbc335838dc3891d7046cb1c2478f807fe42189817e961e1d5374d7be1d14992
diff: (vacio) — NO DRIFT, schema.d.ts identico
```

## Deuda / seguimientos

- F019 (UI de selección de zona): añadir `apiPost` al cliente tipado y un helper
  `resolveZone(lat, lng)` para `POST /api/zones/resolve`, más los componentes/
  hooks con los tres estados (carga/error/datos) y manejo del 404 "sin cobertura".
