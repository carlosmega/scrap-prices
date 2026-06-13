# Implementación F002 — Bootstrap frontend (Next.js + Tailwind + shadcn/ui)

Capa: **frontend**. Spec: `specs/F002-bootstrap-frontend.md`.

## Spec aplicada y decisiones de UI/UX

- Scaffold con `create-next-app` (App Router, TS estricto, `src/`, Tailwind v4,
  ESLint). **Pinné Next.js 15** (`create-next-app@15` → next 15.5.19) en lugar de
  `@latest`, que ya resuelve a Next 16: la spec, su título y
  `docs/conventions-frontend.md` exigen "Next.js 15". (Ver Deuda.)
- Procedimiento del directorio no vacío: moví `CLAUDE.md` y `.gitkeep` a `/tmp`,
  scaffoldeé en `frontend/` vacío y **restauré `frontend/CLAUDE.md`**.
- Home placeholder (Server Component, sin `"use client"`, sin consumo de API):
  Card + Input + Button de shadcn, estilos Tailwind con tokens del theme
  (`text-foreground`, `bg-background`, `text-muted-foreground`). Muestra el
  `NEXT_PUBLIC_API_URL` leído de config tipada (`src/lib/env.ts`), no por fetch.
- `src/lib/api/` queda **vacía** (solo `.gitkeep`): el cliente HTTP y el consumo
  real son F003. No declaré tipos de API a mano.

## Punto crítico resuelto: `pnpm install` exit 1 (ERR_PNPM_IGNORED_BUILDS)

`pnpm 11.6.0` con `strictDepBuilds=true` (default) hace que `pnpm install` **salga
con código 1** si hay build scripts nativos sin aprobar (sharp, unrs-resolver,
esbuild). Eso habría roto la Fase 4 de `init.sh` (`run "pnpm install"`).
En pnpm 11 `onlyBuiltDependencies` está **deprecado y reemplazado por
`allowBuilds`** (confirmado con docs vía context7). Solución en
`frontend/pnpm-workspace.yaml`:

```yaml
allowBuilds:
  sharp: true
  unrs-resolver: true
  esbuild: true
```

Tras esto `pnpm install` sale 0 y ejecuta los postinstall aprobados.

## Reglas ESLint de arquitectura (verificadas que FALLAN)

En `frontend/eslint.config.mjs`:
- `@typescript-eslint/no-explicit-any: "error"`.
- `no-restricted-syntax` prohíbe `fetch(...)`, `window.fetch`, `globalThis.fetch`
  en `src/**`, con override que lo **permite solo en `src/lib/api/client.ts`**
  (alineado con el grep de la Fase 4 de `init.sh`).
- `no-restricted-imports` bloquea importar `lib/api/schema.d.ts` a mano.

Comprobación con un archivo sonda temporal (luego borrado):
```
src\__lint_probe.ts
  1:19  error  Unexpected any. Specify a different type                                    @typescript-eslint/no-explicit-any
  3:10  error  Prohibido `fetch` directo. Todo HTTP pasa por src/lib/api/client.ts (F003)  no-restricted-syntax
✖ 2 problems (2 errors, 0 warnings)  → lint exit 1
```
Y un `fetch` DENTRO de `src/lib/api/client.ts` → lint exit 0 (excepción OK).

El test de humo también se verificó rojo sin la implementación: al romper el
heading de la home, `pnpm test:unit` falla (1 failed); restaurado vuelve a verde.

## Archivos creados / modificados

Creados:
- `frontend/pnpm-workspace.yaml` (allowBuilds)
- `frontend/vitest.config.ts`, `frontend/vitest.setup.ts`
- `frontend/.env.example`, `frontend/.env.local` (`NEXT_PUBLIC_API_URL=http://localhost:8000`)
- `frontend/src/lib/env.ts` (config tipada del API URL; NO hace fetch)
- `frontend/src/app/page.test.tsx` (smoke test, 2 casos)
- `frontend/src/features/.gitkeep`, `frontend/src/lib/api/.gitkeep` (estructura, api/ vacía)
- shadcn vía CLI (`pnpm dlx shadcn@latest init -b radix -d --force` + `add button card input -y`):
  `frontend/components.json`, `frontend/src/lib/utils.ts`,
  `frontend/src/components/ui/button.tsx`, `card.tsx`, `input.tsx`

Modificados (sobre el scaffold):
- `frontend/package.json` — scripts `dev`, `build`, `lint`, `gen:api`
  (`echo 'gen:api pendiente F003'`), `test:unit` (`vitest run`); devDeps de test.
- `frontend/eslint.config.mjs` — reglas de arquitectura.
- `frontend/src/app/page.tsx` — home placeholder con shadcn.
- `frontend/src/app/layout.tsx` — metadata ConstruScan.
- `frontend/.gitignore` — `!.env.example` (versiona el ejemplo).
- `frontend/CLAUDE.md` — restaurado tal cual estaba.

Componentes shadcn añadidos por CLI en `src/components/ui/`: **button, card, input**.

## Output REAL de las verificaciones

`pnpm exec tsc --noEmit`:
```
tsc_exit=0
```
(sin salida; código 0)

`pnpm lint`:
```
$ eslint
lint_exit=0
```

`pnpm build`:
```
$ next build
   ▲ Next.js 15.5.19
   - Environments: .env.local

   Creating an optimized production build ...
 ✓ Compiled successfully in 3.1s
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/5) ...
 ✓ Generating static pages (5/5)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    72.9 kB         175 kB
└ ○ /_not-found                            990 B         103 kB
+ First Load JS shared by all             102 kB
  ├ chunks/360-9e1ffefdc97ad6f3.js       45.8 kB
  ├ chunks/e5baef3c-20d656520f724785.js  54.2 kB
  └ other shared chunks (total)          1.96 kB

○  (Static)  prerendered as static content
build_exit=0
```

`pnpm test:unit` (= `vitest run`):
```
$ vitest run

 RUN  v3.2.6 C:/scrap-prices/frontend

 ✓ src/app/page.test.tsx (2 tests) 114ms

 Test Files  1 passed (1)
      Tests  2 passed (2)
   Start at  13:34:04
   Duration  3.60s (transform 136ms, setup 449ms, collect 802ms, tests 114ms, environment 954ms, prepare 429ms)
test_exit=0
```

`pnpm install --silent` (lo que ejecuta init.sh Fase 4) → `INSTALL_EXIT=0`.

## Deuda / seguimientos

1. **Versión Next.js:** la spec dice `pnpm create next-app@latest` pero también
   exige "Next.js 15". `@latest` instala Next 16. Pinné a Next 15 (15.5.19) para
   honrar el stack declarado. Si el líder/PRD prefiere Next 16, es un cambio de
   spec, no de implementación.
2. **`src/lib/api/` vacía a propósito** (solo `.gitkeep`). `client.ts` y
   `schema.d.ts` los crea F003 (`pnpm gen:api`). La regla ESLint ya contempla
   `client.ts` como única excepción de `fetch`, así que F003 no tendrá fricción.
3. `gen:api` es placeholder (`echo`), por diseño de la spec; el pipeline real
   de OpenAPI→tipos es F003.
4. Build scripts nativos aprobados explícitamente vía `allowBuilds` (pnpm 11).
   Si en el futuro entran nuevas deps con postinstall, habrá que añadirlas o
   `pnpm install` volverá a salir 1.
