# F036 — distDir aislado para builds de verificación (no romper `next dev`)

> SDD: la spec es el contrato. Si no está aquí, no existe.

## Contexto y objetivo

**Problema recurrente (mordió en F033 y F035):** `next dev` (el `./dev.sh` del
humano) y `next build` (`pnpm build`, que corre `./init.sh` Fase 4 — incluido el
que ejecuta cada **reviewer**) **comparten `frontend/.next/`** (distDir por
defecto). Cuando una verificación hace el build mientras el dev server corre,
reescribe `.next/` por debajo y el dev server queda sirviendo chunks rotos
(`Cannot find module './NNN.js'`, sin estilos, favicon 500).

**Objetivo:** que el build de **verificación** use un directorio separado
(`.next-ci`), de modo que ningún `./init.sh`/CI/review vuelva a corromper el
`.next/` de desarrollo del humano. Elimina el roce de raíz (mejor que la regla
frágil "no corras init.sh con dev.sh arriba").

## Alcance

**Incluye:**
- **Frontend (`next.config.ts`):** `distDir: process.env.NEXT_DIST_DIR || ".next"`
  — dev y start siguen en `.next` por defecto; solo el build de verificación lo
  cambia vía env.
- **Arnés (`init.sh`, raíz — líder):** Fase 4 corre el build con
  `NEXT_DIST_DIR=.next-ci pnpm build`, para que no toque `.next`.
- **`.gitignore`:** ignorar `.next-ci` (Next solo ignora `/.next/` por defecto).
- **CI (`.github/workflows/ci.yml`):** no requiere cambios (usa el mismo
  `init.sh`); confirmar que sigue verde.

**No incluye:**
- Cambiar el modo dev ni el puerto (F023 intacto).
- Tocar el `webServer` de Playwright (usa `pnpm dev` → `.next`, correcto; el E2E
  no hace build de producción).
- La sincronización de migraciones del dev server del humano (se maneja por
  flujo: el líder aplica migraciones al cierre — decisión del humano 2026-07-08).

## Criterios de aceptación

- [ ] **Frontend:** `next.config.ts` usa `distDir` desde `NEXT_DIST_DIR` con
      default `.next`. `pnpm dev` y `pnpm build` (sin env) siguen usando `.next`.
- [ ] **Aislamiento (la prueba clave):** con un `.next/` de dev presente,
      `NEXT_DIST_DIR=.next-ci pnpm build` genera `.next-ci/` y **deja `.next/`
      intacto** (verificable: hash/mtime del `.next/BUILD_ID` o de un chunk de dev
      no cambia; o `.next/` no existía y sigue sin existir tras el build a `.next-ci`).
- [ ] **Arnés:** `./init.sh` (completo) Fase 4 buildea a `.next-ci` y termina
      verde; `./init.sh --quick` sigue saltando el build. `.next-ci` gitignored.
- [ ] **tsc/lint/build:** `pnpm exec tsc --noEmit && pnpm lint && pnpm build`
      (dev distDir) verdes; el build a `.next-ci` también compila igual.
- [ ] **CI:** el workflow sigue verde (misma corrida de `init.sh`).
- [ ] **Global:** `./init.sh` verde de punta a punta (backend + frontend + contrato).

## Plan de verificación

```bash
# aislamiento: con dev .next presente, build de verificacion no lo toca
cd frontend && touch .next/PROBE 2>/dev/null || (mkdir -p .next && touch .next/PROBE)
NEXT_DIST_DIR=.next-ci pnpm build          # debe crear .next-ci, no tocar .next
ls .next/PROBE && echo "OK: .next intacto"; ls -d .next-ci && echo "OK: build aislado en .next-ci"
# arnes completo (idealmente con dev.sh apagado la primera vez para confirmar el flujo real):
cd .. && ./init.sh          # Fase 4 -> .next-ci; VERDE
```

## Notas y decisiones abiertas

- Roles: `next.config.ts` lo toca el **implementer-frontend**; `init.sh` y
  `.gitignore` los edita el **líder** (archivos de arnés/raíz). El reviewer
  verifica el conjunto.
- Alternativa descartada: un guard en `dev.sh`/Fase 6 que detecte el clash y
  aborte — no aísla, solo avisa; el distDir separado sí lo elimina.
- Tras F036, un `./init.sh` o review con `./dev.sh` arriba ya **no** corrompe el
  dev server (build va a `.next-ci`). El E2E (`pnpm dev`) y el dev comparten
  `.next` sin problema (ambos son dev, no build).
