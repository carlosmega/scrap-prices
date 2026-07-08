# Sesión activa — HANDOFF

> El líder mantiene este archivo. Es el punto de retomada para la próxima sesión.

**Feature en curso:** ninguna. **`feature_list.json`:** 29 `done`, pendientes
`F012` (opcional) y `F026` (Construrama, bloqueada).

**Estado del arnés:** VERDE. `init.sh --quick` local (32 ok / 0 fallos) y
**CI en GitHub Actions corriendo `init.sh --e2e` en verde** (run `28907565411`,
`conclusion=success`, 2m4s). Working tree limpio, `main` sincronizado con
`origin/main`.

## Novedad de esta sesión
- **F032 · CI (GitHub Actions)** cerrada, APROBADO 1er ciclo. `.github/workflows/ci.yml`:
  job `verify` (ubuntu) instala uv + Node 24 + pnpm 11 + Chromium de Playwright y
  corre `bash init.sh --e2e` en cada push a `main`, cada PR y `workflow_dispatch`;
  sube `playwright-report` como artefacto si falla. Primera corrida verde contra
  el commit del workflow.
- **2 hotfixes de arnés** (fuera del flujo de features, pusheados):
  - `d951a03` restaura bit `+x` en `init.sh` y hooks (un checkout nuevo arrancaba
    en ROJO: `guard-feature.sh` no ejecutable).
  - `435d25c` Fase 2 de `init.sh` ya no exige Docker (daba falso-ROJO por puertos
    5432/6379 ocupados; el MVP corre en SQLite). Ahora Fase 2 es `pendiente`.

## Próximos pasos (orden sugerido)
1. **F026 ConstruramaAdapter** — BLOQUEADA: falta que el humano capture el **body
   de la respuesta de Algolia** (`njvy3eu5dw-dsn.algolia.net`, índice
   `construrama_mx`) con "Save HAR with content". Es el mayor valor de producto
   (comparación cross-retailer *real*, hoy solo Home Depot está en vivo).
2. **Auto-match (rapidfuzz)** para no curar SKUs a mano (M5, sin spec aún).
3. **Deuda de F031:** normalizar la **cotización** (`apps/lists`) — hoy "Agregar 1"
   de un SKU listado por tonelada mete 1 tonelada al carrito. Requiere decisión de
   producto (¿cantidad en piezas?).
4. `F012` (script recon read-only) opcional.

## Follow-ups no bloqueantes
- **CI:** subir las actions de terceros a majors v5 (`checkout`, `setup-node`,
  `pnpm/action-setup`) cuando estén estables — GitHub avisa deprecación del
  runtime Node 20. No falla el job.
- **Atribución git:** los commits de esta sesión (`d951a03`, `435d25c`, `8e67b10`)
  quedaron con committer `M081899@…local`, no enlazados a la cuenta GitHub
  `carlosmega`. Ya están en `origin/main`; corregirlo ahora requeriría reescribir
  historia publicada (decisión del humano).

## Cómo levantar (local)
```bash
./dev-backend.sh    # :8800  (migrate + seed + runserver)
./dev-frontend.sh   # :3300  -> http://localhost:3300
```
