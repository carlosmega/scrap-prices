# Sesión activa — F036 distDir aislado

> El líder mantiene este archivo. Punto de retomada de la sesión.

**Feature en curso:** `F036` (in_progress) — build de verificación usa `distDir`
separado (`.next-ci`) para que `./init.sh`/CI/review no corrompan el `next dev`
del humano (`.next` compartido; mordió en F033 y F035).

## Plan (contract-first)
1. [hecho] `specs/F036-distdir-aislado-build.md`.
2. [hecho] F036 `in_progress`.
3. [hecho — LÍDER] `init.sh` Fase 4 → `NEXT_DIST_DIR=.next-ci pnpm build`;
   `.gitignore` raíz ignora `.next-ci/` (cubre `frontend/.next-ci`).
4. [en curso — IMPLEMENTER-FRONTEND] `frontend/next.config.ts`:
   `distDir: process.env.NEXT_DIST_DIR || ".next"`.
5. [pendiente] Verificar aislamiento (build a `.next-ci` no toca `.next`) + `reviewer`.

## Decisión de flujo del humano (2026-07-08)
- **"Yo (líder) te preparo el entorno en cada cierre":** al cerrar una feature
  backend, aplico su migración a `db.sqlite3` y (si hubo build) limpio `.next`, y
  aviso "listo, refresca". El humano sigue con `./dev.sh` arriba.

## Estado app / arrastre
- 34 `done` (F035 cerrada). Tu `db.sqlite3` ya tiene la migración 0003 → search
  funciona; busca "impermeabilizante" → 29 crudos.
- **Lote SIN pushear** (regla `ask`): dev.sh, F033, PRD v0.2, F034, abre F035,
  F035, abre F036 (+ cierre F036). El humano aprueba el push.
- Committer local `M081899@…local` (no enlaza a GitHub `carlosmega`).

## Próximos (tras F036)
1. Matching en Admin de SKUs reales del vivo → comparación $/kg cross-retailer.
2. Auto-match rapidfuzz (M5). 3. Deuda F031 (cotización nativa). 4. F012 opcional.

## Cómo levantar
```bash
./dev.sh   # backend :8800 + frontend :3300 (Ctrl+C detiene ambos)
# Tras F036: ./init.sh y los reviews ya NO tocan tu .next (build va a .next-ci).
```
