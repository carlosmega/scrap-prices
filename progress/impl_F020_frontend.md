# Informe de implementación — F020 (frontend + e2e)

Spec aplicada: `specs/F020-ui-busqueda-resultados.md` (UI de búsqueda + resultados
comparados por retailer, Épica B1, `GET /api/search`).

## Decisiones de UI/UX (≤5 líneas)
1. Búsqueda por **submit explícito** (Enter/botón), no por tecleo, para evitar
   ráfagas de requests y flakiness de E2E; el orden re-busca el término activo.
2. Sin zona → tarjeta que **invita a elegir zona y no busca** (B1, dependencia F019).
3. Dentro de cada tarjeta, las filas por retailer se ordenan **menor precio primero**
   (B1·CA4); retailer sin precio → "sin precio en tu zona" (B1·CA5) al final.
4. Frescura "actualizado hace X" desde `captured_at` (helper puro); el dato nunca
   se oculta (RNF3): sin fecha muestra "actualización sin fecha".
5. Control de orden = `<select>` nativo (tokens del theme), determinista para E2E;
   no requirió componente shadcn nuevo.

## Sincronización de zona (fix necesario, capa zones)
`useSelectedZone` se instancia por separado en `ZoneSelector` y en `SearchPanel`.
El evento `storage` del navegador NO se dispara en la pestaña que hace el cambio,
así que `SearchPanel` no se enteraba de la zona elegida (el input nunca aparecía).
Se añadió un canal **in-tab** (Set de suscriptores + `broadcastInTab`) en
`frontend/src/features/zones/hooks/use-selected-zone.ts`; se conserva el sync
cross-tab por `storage` y los 5 tests de F019 siguen verdes.

## Capa cliente (contrato)
`/api/search` declara query params (`q`, `zone_id`, `sort`) a nivel de operación,
no de path-key, así que `apiGet(path)` no podía tiparlos. Se añadió
**`apiGetQuery(path, query, options)`** en `src/lib/api/client.ts`: deriva el tipo
de `query` del propio contrato (`paths[P]["get"].parameters.query`) y serializa a
la URL con `URLSearchParams`. Cero `any`, cero tipos a mano; el `fetch` sigue
viviendo solo en `client.ts`.

## Archivos creados
- `frontend/src/features/search/api.ts` — `fetchSearch(q, zoneId, sort)` vía `apiGetQuery`.
- `frontend/src/features/search/types.ts` — `SearchResult`/`RetailerPrice` derivados de `fetchSearch`.
- `frontend/src/features/search/relative-time.ts` — `relativeTime` (puro) + `freshnessLabel`.
- `frontend/src/features/search/relative-time.test.ts` — unit test (vitest), 9 casos.
- `frontend/src/features/search/format.ts` — `formatPrice` + `sortPricesAsc` (puros).
- `frontend/src/features/search/hooks/use-search.ts` — hook con estados idle/loading/ready/empty/error.
- `frontend/src/features/search/components/result-card.tsx` — tarjeta por canónico + filas por retailer.
- `frontend/src/features/search/components/search-panel.tsx` — organismo Client Component (input/sort/estados).
- `e2e/tests/search.spec.ts` — E2E del flujo feliz.

## Archivos modificados
- `frontend/src/lib/api/client.ts` — `apiGetQuery` + helpers `buildQueryString`, tipos `GetQuery`/`GetPathsWithQuery`.
- `frontend/src/app/page.tsx` — compone `<SearchPanel />` debajo de `<ZoneSelector />` (sigue Server Component).
- `frontend/src/features/zones/hooks/use-selected-zone.ts` — sync in-tab entre instancias del hook.

## Componentes shadcn añadidos
Ninguno nuevo. Se reutilizan los ya instalados (`Card`, `CardHeader`, `CardTitle`,
`CardDescription`, `CardContent`, `Input`, `Button`). El control de orden es un
`<select>` nativo con tokens del theme.

## Output REAL de verificaciones

### `pnpm exec tsc --noEmit` (frontend/)
```
$ tsc --noEmit
(sin salida — exit 0)
```

### `pnpm lint` (frontend/)
```
$ eslint
(sin salida — exit 0)
```

### `pnpm build` (frontend/)
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
┌ ○ /                                      43 kB         145 kB
└ ○ /_not-found                            990 B         103 kB
+ First Load JS shared by all             102 kB
○  (Static)  prerendered as static content
```

### `pnpm test:unit` (frontend/)
```
$ vitest run
 RUN  v3.2.6 C:/scrap-prices/frontend

 ✓ src/features/search/relative-time.test.ts (9 tests) 6ms
 ✓ src/features/zones/hooks/use-selected-zone.test.ts (5 tests) 29ms
 ✓ src/app/page.test.tsx (3 tests) 92ms

 Test Files  3 passed (3)
      Tests  17 passed (17)
```

### `pnpm test:e2e` (e2e/)
```
$ playwright test
Running 3 tests using 3 workers
[WebServer] "GET /api/search?q=varilla&zone_id=615b0e10-...&sort=price HTTP/1.1" 200 2155
  3 passed (20.7s)
```
(smoke + zone + search; sin romper los previos.)

### `./init.sh --e2e` (raíz)
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
(Pendientes = jq/docker opcionales + Fase 2 infra diferida; no son fallos.)

## Deuda / seguimientos
- `useSelectedZone` ya tiene tres consumidores potenciales; si crecen, valdría
  extraer un store mínimo (zustand/context) en vez del Set in-tab. No urgente.
- El enlace de cada resultado al detalle (F021) queda fuera de alcance (lo cablea F021).
- El backend sirve `prices` ordenado por `retailer__name`; la UI re-ordena por precio
  en cliente (`sortPricesAsc`). Si F021 necesita el mismo orden, conviene centralizarlo.
