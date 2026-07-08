Veredicto: APROBADO

# Review F036 — distDir aislado (.next-ci) para builds de verificación

Spec: `specs/F036-distdir-aislado-build.md` · Informe impl: `progress/impl_F036_frontend.md`
Ronda 2 (tras el fix del RECHAZO #1 de la ronda 1). El reviewer re-ejecutó TODA la
verificación él mismo (no se aceptó output pegado). Estado del entorno preservado:
`frontend/.next` del humano intacto de punta a punta; `.next-ci` limpiado al terminar.

## Resolución del bloqueante de la ronda 1

- **Ronda 1 RECHAZADA:** `.next-ci/` no estaba en los `ignores` de ESLint, así que
  `pnpm lint` linteaba el build de producción generado dentro de `.next-ci/` y fallaba
  (4967 problemas / 226 errores) siempre que `.next-ci/` existía. Como `./init.sh`
  Fase 4 corre `lint` ANTES del build, `./init.sh` iba ROJO en la 2ª corrida seguida.
- **Fix aplicado (implementer-frontend):** `frontend/eslint.config.mjs:39` añade
  `".next-ci/**"` al array `ignores`, junto a `".next/**"`, con comentario F036.
  Cambio quirúrgico y aditivo (+4 líneas), verificado abajo. **RESUELTO.**

## Prueba decisiva — `./init.sh` VERDE REPETIBLE (2 corridas seguidas, yo mismo)

Corrí `./init.sh` DOS veces seguidas desde la raíz, **sin limpiar `.next-ci` entre
ambas**. La 2ª corrida es la que antes fallaba (lint sobre `.next-ci/` dejado por la 1ª).

### Corrida #1 (crea `.next-ci`) → VERDE  (RUN1_EXIT=0)
```
── Fase 4 · Frontend ──  ✔ lint
════════ Resumen ════════
  ✔ 33 ok   ✘ 0 fallos   ◌ 2 pendientes
  VERDE — el arnés está en estado consistente.
.next-ci creado por la corrida #1: frontend/.next-ci (11:26)
```

### Corrida #2 (con `.next-ci` PRESENTE de la #1) → VERDE  (RUN2_EXIT=0)
```
── Fase 4 · Frontend (Next.js + Tailwind + shadcn) ──
  ✔ pnpm install
  ✔ tsc --noEmit
  ✔ lint                                    <-- antes ROJO aquí (4967 problemas)
  ✔ tests unitarios (vitest)
  ✔ build de producción (distDir .next-ci)
  ✔ arquitectura: fetch solo en src/lib/api/client.ts
── Fase 5 · Contrato OpenAPI → tipos TS ──  ✔ tipos TS sincronizados
════════ Resumen ════════
  ✔ 33 ok   ✘ 0 fallos   ◌ 2 pendientes
  VERDE — el arnés está en estado consistente.
```

### `pnpm lint` con `.next-ci/` PRESENTE (aislando el fix) → exit 0
```
.next-ci existe: SI
LINT_CON_NEXTCI_EXIT=0          # ronda 1 era exit 1 con "✖ 4967 problems (226 errors)"
```

## Sigue cumpliendo lo ya aprobado en la ronda 1

```
Aislamiento:   .next/REVIEW_PROBE INTACTO tras las 2 corridas -> "review-probe-F036-r2"
               (el .next del humano nunca fue tocado por init.sh)
Idempotencia:  sha1(tsconfig) = 2fcc31d012488f44f382d5bbf3c0cfbbc5a05c76 (baseline),
               sin cambios tras 2 corridas completas; include conserva .next/types y .next-ci/types
.gitignore:    git status --ignored -> "!! frontend/.next-ci/"
Sin suciedad:  git status --porcelain tras las corridas = solo los 3 cambios de F036
               (eslint.config.mjs, next.config.ts, tsconfig.json) + 2 progress/ untracked
Arquitectura:  fetch fuera de client.ts -> VACÍO ; ": any" / "as any" en src -> VACÍO
next.config:   next.config.ts:7  distDir: process.env.NEXT_DIST_DIR || ".next"  (NextConfig, sin any)
```

## Tabla final de criterios (spec F036)

| # | Criterio de aceptación | Estado | Evidencia |
|---|---|---|---|
| 1 | `next.config.ts` usa `distDir` desde `NEXT_DIST_DIR`, default `.next`; sin `any`, tipado `NextConfig` | CUMPLE | `next.config.ts:7`; grep `any` en src = VACÍO |
| 2 | Aislamiento: build a `.next-ci` deja `.next` intacto | CUMPLE | `REVIEW_PROBE` sobrevivió 2 corridas de init.sh; `.next-ci/BUILD_ID` creado |
| 3 | Arnés: init.sh Fase 4 buildea a `.next-ci` y verde; `--quick` salta build; `.next-ci` gitignored | CUMPLE | 2 corridas VERDE; `--quick` salta build (ronda 1); `!! frontend/.next-ci/` |
| 4 | tsc/lint/build verdes; el build a `.next-ci` compila igual | CUMPLE | Fase 4 corrida #2 todo ✔; `pnpm lint` con `.next-ci` presente = exit 0 |
| 5 | CI: workflow sigue verde (misma corrida de `init.sh`) | CUMPLE (robusto) | init.sh ahora es verde repetible; el defecto que lo hacía frágil quedó resuelto |
| 6 | Global: `./init.sh` verde de punta a punta | CUMPLE | 2 corridas seguidas → ambas 33 ok / 0 fallos |

Criterios extra del líder (encargo): 1 next.config CUMPLE · 2 aislamiento CUMPLE ·
3 idempotencia tsconfig CUMPLE (sha estable + ambas rutas) · 4 init.sh completo verde
+ `.next` intacto + sin nueva suciedad CUMPLE (ahora repetible) · 5 `.next-ci` gitignored
CUMPLE · 6 higiene (`feature_list.json` válido, 1 in_progress F036) CUMPLE.

## Higiene del entorno tras el review

```
.next del humano   -> INTACTO (dir presente; marcador nunca desapareció)
.next-ci           -> eliminado
.next/REVIEW_PROBE -> eliminado
git status         -> M eslint.config.mjs, M next.config.ts, M tsconfig.json,
                      ?? progress/impl_F036_frontend.md, ?? progress/review_F036.md
```

## Advisory para el líder (NO bloqueante)

Al commitear F036, incluir los **tres** archivos de frontend en el mismo commit:
`frontend/eslint.config.mjs` (ignore de `.next-ci`), `frontend/next.config.ts` (distDir),
y `frontend/tsconfig.json` (con AMBAS rutas `.next/types` y `.next-ci/types`). El commit
`68b322e` solo trae los archivos de arnés (`init.sh`, `.gitignore`, spec). Si tsconfig
quedara sin commitear o revertido a solo `.next/types`, cada build a `.next-ci` re-añadiría
la ruta y ensuciaría el árbol; y sin el ignore de eslint, volvería el bloqueante.

---

## Apéndice — Análisis de la ronda 1 (RECHAZO, ya RESUELTO)

> Se conserva como historia. El bloqueante descrito aquí quedó corregido (ver arriba).

**Motivo del RECHAZO #1:** `.next-ci/` no estaba en `ignores` de ESLint. Causa raíz
aislada en la ronda 1:
```
=== .next-ci PRESENTE -> pnpm lint ===  exit 1, ✖ 4967 problems (226 errors, 4741 warnings)
=== .next-ci AUSENTE  -> pnpm lint ===  exit 0
Rutas linteadas con error: 40 dentro de .next-ci/ (p.ej. .next-ci/server/app/page.js,
   .next-ci/server/chunks/199.js, .next-ci/server/webpack-runtime.js)
frontend/eslint.config.mjs ignores (ronda 1): [node_modules/**, .next/**, out/**,
   build/**, next-env.d.ts, src/lib/api/schema.d.ts]   # faltaba .next-ci/**
```
El bug estaba enmascarado en el informe original del implementer porque hacía
`rm -rf .next-ci` ANTES de lintear (informe línea 111), por lo que su `pnpm lint`
nunca veía `.next-ci/`. En la ronda 1, `./init.sh --quick` con `.next-ci` presente daba
`✔ 31 ok  ✘ 1 fallos` (ROJO) precisamente por este lint. La corrida completa quedaba
verde solo por accidente de orden (lint corre antes del build) + limpieza previa.

**Fix pedido y aplicado:** añadir `".next-ci/**"` a `ignores` en
`frontend/eslint.config.mjs` (implementer-frontend). Re-verificado en la ronda 2 con
`.next-ci/` PRESENTE (sin enmascarar): 2 corridas de `./init.sh` seguidas, ambas VERDE.
