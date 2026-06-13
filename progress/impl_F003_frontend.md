# Implementación F003 — Frontend (capa contrato/tipos + cliente + health UI)

Spec aplicada: `specs/F003-contrato-tipos.md` (pasos 2–4).
Convenciones: `frontend/CLAUDE.md`, `docs/conventions-frontend.md`, sección
Frontend/Contrato de `CHECKPOINTS.md`.

## Decisiones de UI/UX y arquitectura (≤5 líneas)

- Pipeline de contrato: dev-dep `openapi-typescript@7.13.0`; script real
  `gen:api` genera `src/lib/api/schema.d.ts` (no se edita a mano).
- `src/lib/api/client.ts` es el ÚNICO punto con `fetch`: base URL desde
  `env.apiUrl` (`NEXT_PUBLIC_API_URL`), `apiGet<P>` con `path` y tipo de
  respuesta inferidos del contrato (`paths`/`infer R`), errores normalizados
  vía `ApiError` (status 0 = fallo de red/CORS/backend caído).
- Indicador de salud client-side: la home sigue siendo Server Component y
  compone `<HealthIndicator />` (`"use client"`), que hace el fetch en el
  navegador con tres estados (cargando / error amable / "ok"). Así
  `pnpm build` NO depende de que el backend esté arriba.
- Dominio "grita": feature completa en `src/features/health/`
  (`api.ts` + `hooks/use-health.ts` + `components/health-indicator.tsx`).

## Archivos creados / modificados

Creados:
- `frontend/src/lib/api/schema.d.ts` (GENERADO por `pnpm gen:api`)
- `frontend/src/lib/api/client.ts`
- `frontend/src/features/health/api.ts`
- `frontend/src/features/health/hooks/use-health.ts`
- `frontend/src/features/health/components/health-indicator.tsx`

Modificados:
- `frontend/package.json` — dev-dep `openapi-typescript`; script `gen:api` real.
- `frontend/src/app/page.tsx` — la home compone `<HealthIndicator />` en el
  CardFooter (sigue siendo Server Component).

Componentes shadcn añadidos: ninguno (se reutilizan Card/Input/Button de F002).

## Nota de implementación (bug encontrado y corregido)

El comentario JSDoc inicial de `client.ts` contenía el patrón glob
`**/lib/api/schema`, cuyo `*/` cerraba el bloque de comentario antes de tiempo
y rompía el parseo (errores TS1005/TS1434/TS1443/TS1160). Se reescribió el
comentario para no contener la secuencia `*/`. tsc quedó limpio tras el fix.

## Output REAL de las verificaciones

### `pnpm gen:api` (genera schema.d.ts con `status` y la ruta health)
```
$ openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts
✨ openapi-typescript 7.13.0
🚀 ../backend/openapi.json → src/lib/api/schema.d.ts [22.1ms]
```
schema.d.ts contiene `"/api/health"` (paths) y `HealthOut: { status: string }`.

### `pnpm exec tsc --noEmit`
```
EXIT: 0
```
(sin output, limpio)

### `pnpm lint`
```
$ eslint
EXIT: 0
```
(`fetch(` solo en client.ts:63; cero `any` — verificado con grep)

### `pnpm build` (con el backend CAÍDO)
```
$ next build
   ▲ Next.js 15.5.19
   - Environments: .env.local

   Creating an optimized production build ...
 ✓ Compiled successfully in 4.9s
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

○  (Static)  prerendered as static content

EXIT: 0
```
La home `/` prerenderiza como estático (○) porque el fetch es client-side.

### `pnpm test:unit`
```
$ vitest run
 ✓ src/app/page.test.tsx (2 tests) 108ms

 Test Files  1 passed (1)
      Tests  2 passed (2)
EXIT: 0
```

### Control de drift (Fase 5 de init.sh — diff tras regenerar)
```
NO DRIFT: schema.d.ts identical after regeneration
EXIT: 0
```
(`cp` del schema actual a tmp → `pnpm gen:api` → `diff -q` idéntico.)

## Guard checks de arquitectura
- `grep "fetch(" src/`  →  solo `src/lib/api/client.ts:63`.
- `grep "\bany\b" src/lib/api/client.ts`  →  sin coincidencias.
- Cero tipos de respuesta de API declarados a mano: `apiGet` infiere todo de
  `paths` (schema.d.ts); `features/health/api.ts` no anota el tipo de retorno.

## Deuda / seguimientos
- Solo `GET` está soportado en el cliente (`apiGet`). POST/PUT/DELETE se
  añadirán cuando una feature los requiera (no en alcance de F003).
- `use-health.ts` no reintenta ni cachea; suficiente para el indicador de
  salud. Si crece el consumo de API, evaluar una capa de data-fetching
  (React Query/SWR) en una feature futura.
