# impl F030 — Fix hydration mismatch (hooks de localStorage SSR-safe)

Capas: frontend + e2e. Spec: `specs/F030-fix-hydration.md`.

## Causa raíz

`useSelectedZone` (F019) inicializaba el estado con un **lazy initializer**
`useState(readStoredZone)`. En el servidor `readStoredZone()` devuelve `null`
(sin `window`); en el **primer render del cliente** (hidratación) lee
`localStorage` y devuelve la zona guardada. Por eso `SearchPanel` renderizaba
"Elige tu zona…/Buscar materiales (sin zona)" en SSR y "Precios para
<zona>…" en el cliente → "Hydration failed... server rendered text didn't match
the client" en `CardDescription`.

`useQuote` (F022) no leía `localStorage` en el render inicial (el `useState`
arrancaba del store de módulo, que nace en `idle`), pero su valor inicial podía
divergir del server snapshot en remontajes; se le aplicó el mismo patrón por
consistencia y robustez. `getSessionKey` (`session.ts`) solo se invoca en
callbacks/efectos, nunca en render → ya era SSR-safe, sin cambios.

## Fix por hook (SSR-safe, patrón canónico `useSyncExternalStore`)

- **`useSelectedZone`** (`src/features/zones/hooks/use-selected-zone.ts`):
  reescrito sobre `useSyncExternalStore(subscribe, getClientSnapshot,
  getServerSnapshot)`. `getServerSnapshot` devuelve SIEMPRE el default (`null`)
  = primer render del cliente; `localStorage` se lee solo tras montar
  (`getClientSnapshot`, con snapshot cacheado y referencia estable para no
  entrar en bucle de renders). Se conservan persistencia (write a
  `localStorage`), sync `storage` cross-tab y el broadcast in-tab; `subscribe`
  re-lee `localStorage` al (re)activarse el store. Solo cambió **cuándo** se lee
  por primera vez.
- **`useQuote`** (`src/features/lists/hooks/use-quote.ts`): cambiado de
  `useState`+`useEffect` a `useSyncExternalStore` con `getQuoteServerSnapshot`
  que devuelve una referencia estable `{ status: "idle" }`. Store de módulo,
  listeners in-tab, persistencia del `defaultListId` y broadcast intactos.
- **`session.ts`**: sin cambios (no lee en render).

Ningún componente (`search-panel.tsx`, `zone-selector.tsx`, `quote-badge.tsx`,
`quote-list.tsx`) ramifica markup distinto SSR vs primer render cliente: ahora
todos parten del default (`selectedZone = null`, cotización `idle`).

## Guardia de regresión (e2e)

Nuevo `e2e/tests/hydration.spec.ts`: pre-setea la zona en `localStorage` vía
`page.addInitScript` ANTES de cargar `/`, escucha `page.on('console')` y
`page.on('pageerror')`, navega a `/`, verifica que tras hidratar el panel
refleja la zona guardada ("Monterrey Metro"), y **falla** si aparece algún
mensaje que matchee `/hydration|did not match|hydration failed/i`. Los 5 specs
previos siguen verdes.

## Archivos

- Modificado: `frontend/src/features/zones/hooks/use-selected-zone.ts`
- Modificado: `frontend/src/features/lists/hooks/use-quote.ts`
- Creado: `e2e/tests/hydration.spec.ts`
- Componentes shadcn añadidos: ninguno.
- `pnpm gen:api`: no aplica (el contrato/API no cambió; Fase 5 de init.sh verde).

## Output real de verificación

### `pnpm exec tsc --noEmit` (frontend/)
```
(sin salida — limpio)
```

### `pnpm lint` (frontend/)
```
$ eslint
```

### `pnpm test:unit` (frontend/)
```
$ vitest run

 RUN  v3.2.6 C:/scrap-prices/frontend

 ✓ src/features/lists/session.test.ts (6 tests) 12ms
 ✓ src/features/search/relative-time.test.ts (9 tests) 11ms
 ✓ src/features/zones/hooks/use-selected-zone.test.ts (5 tests) 52ms
 ✓ src/app/page.test.tsx (3 tests) 156ms

 Test Files  4 passed (4)
      Tests  23 passed (23)
```

### `pnpm build` (frontend/)
```
$ next build
   ▲ Next.js 15.5.19
   - Environments: .env.local

   Creating an optimized production build ...
 ✓ Compiled successfully in 11.8s
   Linting and checking validity of types ...
   Collecting page data ...
 ✓ Generating static pages (6/6)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    32.3 kB         151 kB
├ ○ /_not-found                            990 B         103 kB
├ ○ /cotizacion                          1.93 kB         121 kB
└ ƒ /products/[id]                       4.11 kB         123 kB
+ First Load JS shared by all             102 kB

○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
```

### `pnpm test:e2e` (e2e/)
```
$ playwright test

Running 6 tests using 6 workers
[1/6] tests\hydration.spec.ts:24:5 › cargar / con una zona ya guardada no produce hydration mismatch
[2/6] tests\detail.spec.ts ...
[3/6] tests\search.spec.ts ...
[4/6] tests\quote.spec.ts ...
[5/6] tests\smoke.spec.ts ...
[6/6] tests\zone.spec.ts ...

  6 passed (46.0s)
```

### `./init.sh --e2e` (raíz)
```
── Fase 3 · Backend (Django + Ninja) ──
  ✔ pytest
── Fase 4 · Frontend (Next.js + Tailwind + shadcn) ──
  ✔ tsc --noEmit
  ✔ lint
  ✔ tests unitarios (vitest)
  ✔ build de producción
  ✔ arquitectura: fetch solo en src/lib/api/client.ts
── Fase 5 · Contrato OpenAPI → tipos TS ──
  ✔ tipos TS sincronizados con backend/openapi.json
── Fase 6 · E2E (Playwright) ──
  ✔ suite Playwright

════════ Resumen ════════
  ✔ 33 ok   ✘ 0 fallos   ◌ 3 pendientes
  VERDE — el arnés está en estado consistente.
```

## Decisiones de UI/UX

Se acepta el breve "flash" del estado por-defecto antes de hidratar desde
`localStorage` (costo correcto de SSR-safety, según la spec). El primer paint
muestra el panel sin zona; tras montar, refleja la zona guardada.

## Deuda / seguimientos

- Sin `fetch` fuera de `client.ts`, cero `any`, `"use client"` ya estaba al
  nivel más bajo (los hooks). No se introdujo deuda nueva.
- Posible mejora futura: un único helper genérico `createPersistentStore`
  (localStorage + `useSyncExternalStore`) para `use-selected-zone` y `use-quote`
  evitaría la duplicación del patrón snapshot/subscribe. Fuera del alcance de
  F030.
