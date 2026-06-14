# Implementación frontend — F017 (API de listas)

Spec aplicada: `specs/F017-api-listas.md` (capa frontend: paso de contrato +
ampliar el cliente tipado). Backend ya añadió los 8 endpoints `/api/lists` y
regeneró `backend/openapi.json`.

## Decisiones de implementación (≤5 líneas)
- `pnpm gen:api` regeneró `src/lib/api/schema.d.ts`; tipos `UserListOut`,
  `UserListDetailOut`, `UserListItemOut`, `*CreateIn`/`*PatchIn` y las 8 operaciones aparecen.
- Extendí `client.ts` con `apiPost`/`apiPatch`/`apiDelete` espejo de `apiGet`; el
  `fetch` sigue centralizado en un único `request()` interno (un solo `fetch`).
- Header de sesión: opción tipada `sessionKey` en las opciones de cada helper, que
  se traduce al header HTTP `X-Session-Key` (identidad anónima de F017).
- 204 sin body: `apiDelete` no parsea JSON y resuelve a `void`; tipos derivados
  de `paths` (helper `SuccessJson`/`RequestJson` por inferencia). Cero `any`.
- NO añadí `src/features/lists/api.ts`: las rutas con parámetro (`{list_id}`) exigirían
  construcción de path no tipada; la spec permite limitarse a client.ts + tipos (UI es F022).

## Archivos creados/modificados
- Modificado: `frontend/src/lib/api/client.ts` (helpers `apiPost`/`apiPatch`/`apiDelete`,
  `ApiRequestOptions` con `sessionKey`, `request()` interno compartido).
- Regenerado (no a mano): `frontend/src/lib/api/schema.d.ts` (`pnpm gen:api`).
- Componentes shadcn añadidos: ninguno (no hay UI en esta feature).

## Output REAL de las verificaciones

### `pnpm gen:api`
```
$ openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts
✨ openapi-typescript 7.13.0
🚀 ../backend/openapi.json → src/lib/api/schema.d.ts [137ms]
```

### `pnpm exec tsc --noEmit`
```
EXIT: 0
```
(sin salida; type-check limpio)

### `pnpm lint`
```
$ eslint
EXIT: 0
```

#### Verificación de invariantes (grep)
`fetch(` solo en client.ts:
```
=== fetch( occurrences under src (excluding schema.d.ts) ===
src/lib/api/client.ts:132:    response = await fetch(buildUrl(path), {
```
Cero `any` en src (excluyendo schema.d.ts generado):
```
=== bare 'any' type occurrences under src (excluding schema.d.ts) ===
(none)
```

### `pnpm build`
```
$ next build
   ▲ Next.js 15.5.19
   - Environments: .env.local

   Creating an optimized production build ...
 ✓ Compiled successfully in 6.8s
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (5/5)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    73.9 kB         176 kB
└ ○ /_not-found                            990 B         103 kB
+ First Load JS shared by all             102 kB

○  (Static)  prerendered as static content
EXIT: 0
```

### `pnpm test:unit`
```
$ vitest run
 RUN  v3.2.6 C:/scrap-prices/frontend
 ✓ src/app/page.test.tsx (2 tests) 131ms
 Test Files  1 passed (1)
      Tests  2 passed (2)
EXIT: 0
```

### Control de drift (2º `pnpm gen:api`)
```
$ openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts
✨ openapi-typescript 7.13.0
🚀 ../backend/openapi.json → src/lib/api/schema.d.ts [71.3ms]
--- diff (empty = no drift) ---
NO DRIFT: schema.d.ts idéntico tras 2º gen:api
```

## Deuda / seguimientos
- Las rutas parametrizadas (`/api/lists/{list_id}`, `.../items/{item_id}`) se tipan como
  el literal-template del contrato, igual que el `apiGet` existente (`/api/products/{id}`).
  La construcción/interpolación del path concreto y un `features/lists/api.ts` que ligue
  `sessionKey` quedan para F022 (UI), donde tendrán contexto de uso real.
- No hay test unitario específico del cliente (no existía suite para `apiGet`); si el
  reviewer lo exige, se añadiría un test de `client.ts` con `fetch` mockeado (204/sessionKey).
