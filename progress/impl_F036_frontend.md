# impl F036 — frontend (distDir aislado para builds de verificación)

Spec: `specs/F036-distdir-aislado-build.md`. Capa: frontend (`next.config.ts` + `tsconfig.json`).

## Spec aplicada y decisiones

- Cambio principal: `frontend/next.config.ts` → `distDir: process.env.NEXT_DIST_DIR || ".next"`.
- Dev y start siguen en `.next` por defecto; solo el build de verificación (CI/review) lo redirige vía `NEXT_DIST_DIR=.next-ci`.
- Config sigue tipada como `NextConfig`, sin `any`.
- **`frontend/tsconfig.json`:** se CONSERVA el cambio que Next (`writeConfigurationDefaults`)
  escribe al buildear con `.next-ci` — añade `.next-ci/types/**/*.ts` al `include` (junto al
  `.next/types/**/*.ts` de dev) y canonicaliza el formato. Decisión del líder para que F036
  quede **idempotente**: con ambas rutas presentes, ni `pnpm dev`/`pnpm build` (default `.next`)
  ni el build `.next-ci` vuelven a tocar tsconfig → `./init.sh` Fase 4 no ensucia el árbol.
- No se tocó `init.sh`, `.gitignore`, `e2e/` ni backend (fuera de mi alcance / los hizo el líder).

## Archivos

- **Modificado:** `frontend/next.config.ts` (1 línea efectiva + comentario).
- **Modificado:** `frontend/tsconfig.json` (Next añade `.next-ci/types/**/*.ts` al `include` +
  canonicaliza arrays; se conserva a propósito, ver decisiones).
- **Modificado:** `frontend/eslint.config.mjs` (fix RECHAZO #1: añade `".next-ci/**"` al
  array `ignores`, junto a `".next/**"`; es build output generado y no se lintea).
- Componentes shadcn añadidos: **ninguno** (feature de configuración, sin UI).

Diff real:

```diff
 const nextConfig: NextConfig = {
-  /* config options here */
+  // F036: distDir aislado para builds de verificación. Dev y start usan `.next`
+  // por defecto; solo el build de CI/review lo cambia vía NEXT_DIST_DIR=.next-ci
+  // para no corromper el `.next/` del `next dev` del humano.
+  distDir: process.env.NEXT_DIST_DIR || ".next",
 };
```

## RECHAZO #1 (`progress/review_F036.md`) — corregido

**Bug real que enmascaré:** en mi 1ª verificación hice `rm -rf .next-ci` ANTES de lintear,
así que `pnpm lint` nunca vio `.next-ci/`. Pero `.next-ci/` NO estaba en los `ignores` de
ESLint → cuando `.next-ci/` existe, `pnpm lint` lintea el build de producción generado dentro
y falla (4967 problemas / 226 errores). Como `./init.sh` Fase 4 corre `lint` ANTES de `build`,
la 2ª corrida de `./init.sh` (con `.next-ci/` ya presente de la 1ª) iba ROJO → rompía el
objetivo de F036 (verde repetible).

**Fix (quirúrgico, 1 línea):** añadí `".next-ci/**"` al array `ignores` de
`frontend/eslint.config.mjs`, junto a `".next/**"`. Es build output generado, igual que `.next/`.

### Re-verificación SIN enmascarar (build → lint CON `.next-ci` presente)

No borré `.next-ci` antes de lintear (eso fue lo que ocultó el fallo):

```
=== build de verificacion -> crea .next-ci ===
○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
OK: .next-ci PRESENTE (no lo borro antes de lintear)

=== pnpm lint CON .next-ci presente (esto es lo que antes fallaba/enmascare) ===
$ eslint
LINT_CON_NEXTCI_EXIT=0
```

→ `pnpm lint` VERDE (exit 0) **con `.next-ci/` presente**. El fix funciona.

### Prueba decisiva: `./init.sh` DOS veces seguidas → ambas VERDE

`.next-ci/` quedaba presente entre corridas (dejado por el build de la corrida anterior), que
es justo la condición que antes ponía ROJA la 2ª. Ambas corridas verdes:

```
=== ./init.sh CORRIDA #1 ===  (con .next-ci presente de la corrida manual previa)
── Fase 4 · Frontend ── ✔ pnpm install ✔ tsc --noEmit ✔ lint ✔ vitest ✔ build (distDir .next-ci) ✔ fetch solo en client.ts
════════ Resumen ════════  ✔ 33 ok   ✘ 0 fallos   ◌ 2 pendientes   VERDE
INITSH1_EXIT=0

=== ./init.sh CORRIDA #2 (la decisiva, la que antes fallaba) ===  (.next-ci presente del build de #1)
── Fase 0 · Herramientas ──            ✔ git, node, jq, uv, docker, pnpm; ✔ repo git
── Fase 1 · Invariantes del arnés ──   ✔ feature_list.json válido; ✔ in_progress: 1 (máx 1); ✔ 33 done con review APROBADO
── Fase 2 · Infraestructura ──         ◌ Docker no usado en el MVP (SQLite)
── Fase 3 · Backend ──                 ✔ uv sync; ✔ ruff; ✔ migraciones al día; ✔ pytest; ✔ api.py sin ORM
── Fase 4 · Frontend ──                ✔ pnpm install; ✔ tsc --noEmit; ✔ lint; ✔ vitest; ✔ build (distDir .next-ci); ✔ fetch solo en client.ts
── Fase 5 · Contrato OpenAPI → TS ──   ✔ tipos TS sincronizados con backend/openapi.json
── Fase 6 · E2E ──                     ◌ saltada (usa --e2e)
════════ Resumen ════════  ✔ 33 ok   ✘ 0 fallos   ◌ 2 pendientes   VERDE
INITSH2_EXIT=0
```

→ **F036 verde repetible**: la 2ª corrida (antes ROJA por lint sobre `.next-ci/`) ahora VERDE.
Limpieza posterior: `rm -rf frontend/.next-ci`; `frontend/.next` del humano intacto.

## Verificación — PRUEBA DE AISLAMIENTO (criterio clave)

Con un `.next/` de dev presente (el humano tiene `./dev.sh` en :3300), sembré un marcador
y corrí el build de verificación a `.next-ci`:

```
=== simula un .next de dev y coloca marcador ===
marcador escrito:
probe
=== build de verificacion AISLADO -> .next-ci ===
$ next build
   ▲ Next.js 15.5.19
   Creating an optimized production build ...
 ✓ Compiled successfully in 4.8s
   Linting and checking validity of types ...
   Collecting page data ...
 ✓ Generating static pages (6/6)
   Finalizing page optimization ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    33.4 kB         153 kB
├ ○ /_not-found                            988 B         103 kB
├ ○ /cotizacion                          1.93 kB         121 kB
└ ƒ /products/[id]                       4.31 kB         124 kB
+ First Load JS shared by all             102 kB
```

Aserciones (output real):

```
=== ASERCIONES DE AISLAMIENTO ===
OK: .next INTACTO (marcador de dev sigue presente)
OK: build aislado en .next-ci

-- .next (dev) conserva PROBE_F036 --
PROBE_F036, app-build-manifest.json, ... , server, static, trace, types
-- .next-ci (build de verificacion) tiene el build de prod completo --
BUILD_ID, app-path-routes-manifest.json, diagnostics, export-marker.json,
images-manifest.json, required-server-files.json, ... , server, static, types
```

→ El build de verificación crea `.next-ci/` con el build de producción completo (incluye
`BUILD_ID`, `export-marker.json`, etc.) y **deja `.next/` del dev intacto** (el marcador
`PROBE_F036` sobrevive). Limpieza posterior: `rm -rf .next-ci .next/PROBE_F036` (el `.next`
del humano se conserva).

## Verificación — PRUEBA DE IDEMPOTENCIA de tsconfig (criterio del líder)

Objetivo: que `NEXT_DIST_DIR=.next-ci pnpm build` NO ensucie el árbol en cada corrida.

- **1ª corrida** `NEXT_DIST_DIR=.next-ci pnpm build`: Next escribe el `include` canónico en
  `frontend/tsconfig.json`. Se CONSERVA. Verificación de que quedan AMBAS rutas:

```
=== verificacion: AMBAS rutas de types presentes en el include ===
OK: .next/types (dev) presente
OK: .next-ci/types (verificacion) presente
```

- **2ª corrida** `NEXT_DIST_DIR=.next-ci pnpm build`: no debe modificar tsconfig. Comparo el
  sha1 del archivo antes/después de la 2ª corrida:

```
  sha1(tsconfig) antes:   cc91f4a7a91bed590c70b7976a5334eb3f17396f
  sha1(tsconfig) despues: cc91f4a7a91bed590c70b7976a5334eb3f17396f
OK IDEMPOTENTE: tsconfig SIN cambios en la 2a corrida (mismo sha1)
```

  → sha1 idéntico ⇒ la 2ª corrida es un no-op sobre tsconfig. (`git status --porcelain` sigue
  mostrando `M frontend/tsconfig.json` porque el cambio de la 1ª corrida se conserva a
  propósito vs HEAD; el criterio de idempotencia —"sin cambios nuevos al re-buildear"— es el
  sha1 igual.)

## Verificación — tsc / lint (con el tsconfig nuevo)

`.next-ci` fue eliminado antes de tsc, para probar que un glob a `.next-ci/types` inexistente
NO rompe tsc:

```
=== step 4: pnpm exec tsc --noEmit con .next-ci ausente (glob vacio no debe romper) ===
TSC_EXIT=0 (limpio con tsconfig nuevo, .next-ci inexistente)
```

```
=== pnpm lint (revalidacion con tsconfig nuevo) ===
$ eslint
LINT_EXIT=0
```

Ambos verdes. Árbol final (código): `M frontend/next.config.ts` + `M frontend/tsconfig.json`,
nada más. `.next/` del humano intacto; `.next-ci/` eliminado (gitignored).

## Sobre `pnpm build` estándar (sin env → `.next`)

**Deliberadamente NO corrí el `pnpm build` estándar (default `.next`).** Razón: el humano
tiene `./dev.sh` vivo en :3300 usando `.next`; un build a default `.next` reescribiría ese
directorio activo — exactamente la corrupción que F036 previene. La compilación ya quedó
probada por el build de verificación a `.next-ci` (mismo pipeline, solo cambia el directorio
de salida), más `tsc --noEmit` y `lint` verdes. El reviewer hará el build formal vía
`./init.sh` Fase 4, que ahora apunta a `.next-ci`. Esto sigue la guía explícita del humano
("para el pnpm build estándar bastan tsc+lint... el reviewer hará el build formal").

## Deuda / seguimientos

- **Efecto colateral de `next build` sobre `tsconfig.json` — RESUELTO (idempotente).**
  En la primera versión lo había revertido; por decisión del líder ahora se CONSERVA el
  cambio que Next escribe (`.next-ci/types/**/*.ts` en `include` + canonicalización). Con
  `.next/types` y `.next-ci/types` ambas presentes, el `include` ya está en la forma canónica
  que Next espera para los dos distDir, así que **ningún build/dev futuro vuelve a tocar
  tsconfig** (probado: sha1 idéntico en la 2ª corrida). `./init.sh` Fase 4 no ensuciará el
  árbol en cada review. El glob a `.next-ci/types` inexistente no rompe tsc (probado, exit 0).
- **`.next-ci/` como build output ignorado — cubierto en 3 capas:** `.gitignore` raíz (git,
  líder), `include`/glob de `tsconfig.json` (types, idempotente) y `ignores` de
  `eslint.config.mjs` (lint). Las tres son necesarias para que `./init.sh` sea verde repetible.
- Sin deuda pendiente. El cambio frontend de F036 son 3 archivos: `next.config.ts` (distDir),
  `tsconfig.json` (types idempotente) y `eslint.config.mjs` (ignore de lint). `init.sh` Fase 4
  y `.gitignore` los maneja el líder (verificado por el reviewer).
