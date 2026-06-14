# impl F015 — Frontend (capa contrato)

Spec: `specs/F015-api-busqueda.md`. Tarea: regenerar tipos del contrato tras el
nuevo `GET /api/search` del backend. SIN UI (la UI de búsqueda es F020).

## Decisiones

- **Regeneración de tipos (paso 1):** `pnpm gen:api` regenera
  `src/lib/api/schema.d.ts` desde `backend/openapi.json`. Ahora incluye la ruta
  `/api/search` (operación `apps_catalog_api_buscar`, con query `q`, `zone_id`,
  `sort?`) y los schemas `SearchResultOut`, `PriceByRetailerOut`,
  `RetailerRefOut`, `CanonicalProductRefOut`. No se editó a mano.
- **Helper `fetchSearch` (paso 2, opcional): NO añadido.** El cliente actual,
  `apiGet<P extends GetPaths>(path: P, init?)` (`src/lib/api/client.ts`), solo
  acepta una clave de ruta literal del schema (`"/api/search"`) e infiere el JSON
  200 a partir de ella; **no tiene soporte para query params**. Un `fetchSearch`
  tipado y limpio exigiría modificar `client.ts` para aceptar `params`. La spec/
  tarea indica: si `apiGet` no soporta query params cómodamente, limitar el cambio
  a regenerar tipos y no tocar `client.ts` salvo que sea estrictamente necesario
  y limpio. Por tanto se deja el helper para F020 (UI), que añadirá el soporte de
  query params al cliente de forma consciente.

## Archivos

- Modificado (generado, no a mano): `frontend/src/lib/api/schema.d.ts`.
- Componentes shadcn añadidos: ninguno.
- `client.ts`: sin cambios.

## Output real

### pnpm gen:api
```
$ openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts
✨ openapi-typescript 7.13.0
🚀 ../backend/openapi.json → src/lib/api/schema.d.ts [214.6ms]
```
schema.d.ts contiene ahora `"/api/search"`, `apps_catalog_api_buscar`
(query `q`/`zone_id`/`sort?`), `SearchResultOut`, `PriceByRetailerOut`,
`RetailerRefOut`, `CanonicalProductRefOut`. Verificado por lectura del archivo.

### pnpm exec tsc --noEmit
```
EXIT_TSC=0
```
(sin salida; exit 0)

### pnpm lint
```
$ eslint
EXIT_LINT=0
```

### pnpm build
```
$ next build
   ▲ Next.js 15.5.19
   - Environments: .env.local

   Creating an optimized production build ...
 ✓ Compiled successfully in 4.3s
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (5/5)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    73.8 kB         176 kB
└ ○ /_not-found                            990 B         103 kB
+ First Load JS shared by all             102 kB
EXIT_BUILD=0
```

### pnpm test:unit
```
$ vitest run
 RUN  v3.2.6 C:/scrap-prices/frontend
 ✓ src/app/page.test.tsx (2 tests) 125ms

 Test Files  1 passed (1)
      Tests  2 passed (2)
EXIT_TEST=0
```

### Control de drift (2º gen:api idéntico)
```
BEFORE=2393c0f22cce0b52ab623a9a9589183cf7e4774525fc33cbc2774165264c2a34
AFTER =2393c0f22cce0b52ab623a9a9589183cf7e4774525fc33cbc2774165264c2a34
DRIFT: none (identical)
```

## Deuda / seguimientos

- **F020 (UI búsqueda):** añadir soporte de query params al cliente tipado
  (`apiGet` con `params`, o un `apiGetQuery`) y el helper
  `fetchSearch(q, zoneId, sort)` en `src/features/search/api.ts` usando los tipos
  ya generados (`SearchResultOut`). No hacerlo aquí evita modificar `client.ts`
  sin un consumidor real y mantiene el alcance de F015 en "solo contrato".
