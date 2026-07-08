# Sesión activa — HANDOFF

> El líder mantiene este archivo. Punto de retomada para la próxima sesión.

**Feature en curso:** ninguna. **`feature_list.json`:** 34 `done`, pendiente
`F012` (opcional).

**Estado del arnés:** VERDE. `./init.sh` **verde repetible** (F036 eliminó el
roce del `.next`). Backend 207 tests, vitest 57, E2E 8/8.

## La app HOY
Busca un término; si no hay datos frescos consulta HD+Construrama en vivo, ingesta
y muestra canónicos comparados + crudos por tienda. Resuelto en esta ronda de QA:
- **F034:** enlaces a la ficha de HD abren la página real (`seo.href`), no 404.
- **F035:** crudos se muestran por término scrapeado (typo/fuzzy del retailer ya no
  los oculta). Busca "impermeabilizante" → 29.
- **F036:** `./init.sh`/reviews ya NO corrompen tu `next dev` (build va a `.next-ci`).

## Decisión de flujo (2026-07-08)
Yo (líder) preparo el entorno en cada cierre: aplico migraciones a `db.sqlite3` y
limpio `.next` si hizo falta. Con F036, el `.next` ya no se ensucia por reviews.

## Pendiente operativo — PUSH
**Lote SIN pushear** (regla `ask`), en orden. Commits de líder/features:
`1f48449` dev.sh · `339d21b` abre F033 · `0223f3c` PRD v0.2 · `b41e67e` F033 ·
`af6151e` abre F034 · `e318a22` F034 · `a9503d7` abre F035 · `a847d04` F035 ·
`68b322e` abre F036 · (+ cierre F036 que hace el líder ahora). El humano aprueba.
Committer local `M081899@…local` (no enlaza a GitHub `carlosmega`).

## Próximos pasos sugeridos
1. **Matching en Admin** de los SKUs reales del vivo (cemento, impermeabilizante…)
   → habilita comparación $/kg cross-retailer. Luego auto-match (rapidfuzz, M5).
2. **Deuda F031:** cotización en precio nativo.
3. **Deuda F035:** `_hay_datos_frescos` matchea por nombre → re-buscar un typo dentro
   del TTL re-dispara el vivo hasta el cooldown (no vuelve a 0 gracias a la FK).
4. Celery Beat como refresco programado. 5. `F012` opcional.

## Cómo levantar
```bash
./dev.sh   # backend :8800 + frontend :3300 (Ctrl+C detiene ambos)
# Ya puedes correr ./init.sh con dev.sh arriba: no te toca el .next (F036).
```
