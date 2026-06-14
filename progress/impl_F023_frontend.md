# impl F023 — frontend + e2e (puertos fijos 8800/3300)

Spec aplicada: `specs/F023-puertos-fijos.md`.

## Decisiones de UI/UX

- No hay cambios de UI/UX: F023 es puramente operativa (puertos). Solo se ajustó
  config de entorno, scripts y la config de Playwright.
- `dev`/`start` fijan `--port 3300` en `package.json`; Playwright además pasa
  `pnpm dev --port 3300` (Next toma el último `--port`, sigue siendo 3300 →
  idempotente, ambos coinciden en 3300).
- Default de `NEXT_PUBLIC_API_URL` en `env.ts` queda en `:8800`; sigue siendo
  sobreescribible por env/`.env.local`.
- Los specs E2E ya usaban `baseURL` + rutas relativas (robustez de F022); no
  tenían puertos hardcodeados, así que no se tocó su navegación. Solo se corrigió
  un comentario residual `:3000` en `smoke.spec.ts`.

## Archivos creados/modificados

Frontend (solo dentro de `frontend/`):
- `frontend/src/lib/env.ts`: default `NEXT_PUBLIC_API_URL` `:8000` → `:8800`.
- `frontend/.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8800`.
- `frontend/.env.example`: `NEXT_PUBLIC_API_URL=http://localhost:8800` (comentario intacto).
- `frontend/package.json`: `"dev": "next dev --port 3300"`, `"start": "next start --port 3300"`.

E2E (solo dentro de `e2e/`):
- `e2e/playwright.config.ts`:
  - webServer backend: `runserver 127.0.0.1:8800`, `url` `http://127.0.0.1:8800/api/health`
    (se mantiene `migrate && seed &&`).
  - webServer frontend: `pnpm dev --port 3300`, `url` `http://localhost:3300`.
  - `use.baseURL`: `http://localhost:3300`. `retries`/timeouts intactos.
- `e2e/tests/smoke.spec.ts`: comentario `localhost:3000` → `localhost:3300` (solo doc).

Componentes shadcn añadidos: ninguno.

NO se tocó `frontend/src/lib/api/schema.d.ts` (generado) ni `backend/`.

## Grep de residuos (cero en frontend/src y e2e/)

```
$ rg ":8000|:3000" frontend/src
No matches found
$ rg ":8000|:3000" e2e
No matches found
```

Nota: `frontend/README.md:17` aún menciona `http://localhost:3000` (boilerplate de
create-next-app). Está FUERA de `frontend/src` (fuera del alcance del criterio de
aceptación, que acota a `frontend/src`) → se deja como deuda menor (ver abajo).

## Output REAL de verificación

### `pnpm exec tsc --noEmit` (frontend/)
```
===== tsc --noEmit =====
EXIT_TSC=0
```

### `pnpm lint` (frontend/)
```
===== lint =====
$ eslint
EXIT_LINT=0
```

### `pnpm build` (frontend/)
```
===== build =====
$ next build
   ▲ Next.js 15.5.19
   - Environments: .env.local

   Creating an optimized production build ...
 ✓ Compiled successfully in 7.0s
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/6) ...
 ✓ Generating static pages (6/6)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    32.2 kB         151 kB
├ ○ /_not-found                            990 B         103 kB
├ ○ /cotizacion                          1.93 kB         121 kB
└ ƒ /products/[id]                       4.06 kB         123 kB
+ First Load JS shared by all             102 kB

EXIT_BUILD=0
```

### `pnpm test:unit` (frontend/)
```
===== test:unit =====
$ vitest run
 ✓ src/features/search/relative-time.test.ts (9 tests) 7ms
 ✓ src/features/lists/session.test.ts (6 tests) 12ms
 ✓ src/features/zones/hooks/use-selected-zone.test.ts (5 tests) 41ms
 ✓ src/app/page.test.tsx (3 tests) 107ms

 Test Files  4 passed (4)
      Tests  23 passed (23)
EXIT_UNIT=0
```

### `pnpm exec playwright test --reporter=list` (e2e/) — 5 specs, puertos nuevos
```
Running 5 tests using 5 workers
[WebServer] $ next dev --port 3300 "--port" "3300"
[WebServer] [14/Jun/2026 10:59:16] "GET /api/health HTTP/1.1" 200 16
  ✓  2 [chromium] › tests\smoke.spec.ts:9:5 › la home carga y el indicador de salud muestra ok (4.7s)
  ✓  4 [chromium] › tests\search.spec.ts:19:5 › buscar varilla en Monterrey Metro: ambos retailers y orden por precio (5.0s)
  ✓  3 [chromium] › tests\quote.spec.ts:23:5 › cotización: agregar → ver snapshot+total → editar cantidad → quitar (11.1s)
  ✓  1 [chromium] › tests\detail.spec.ts:13:5 › desde la búsqueda al detalle: precios por retailer e historial (11.2s)
  ✓  5 [chromium] › tests\zone.spec.ts:11:5 › elegir zona y que persista tras recargar (10.1s)

  5 passed (31.6s)
```
Los logs del WebServer confirman el lazo fullstack: frontend dev en `:3300`,
backend respondiendo `/api/health` y `/api/zones` en `:8800`, y preflights CORS
`OPTIONS /api/lists ... 200` desde el origen `:3300`.

### `./init.sh --e2e` desde la raíz — VERDE (Fase 4/5/6 + resumen)
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
EXIT_INIT=0
```

## Deuda / seguimientos

- `frontend/README.md:17` (boilerplate create-next-app) sigue diciendo
  `http://localhost:3000`. Fuera del alcance del criterio (`frontend/src`) y no
  afecta runtime; el líder podría actualizarlo junto a `README.md`/`AGENTS.md` raíz
  en la parte "Raíz/docs" de la spec. No bloquea.
- `pnpm dev --port 3300` desde Playwright duplica el flag (`next dev --port 3300 --port 3300`);
  Next usa el último, sin efecto adverso. Se deja explícito para no depender solo
  del script.
