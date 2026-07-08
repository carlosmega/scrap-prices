# Sesión activa — HANDOFF

> El líder mantiene este archivo. Punto de retomada para la próxima sesión.

**Feature en curso:** ninguna. **`feature_list.json`:** 32 `done`, pendiente
`F012` (opcional).

**Estado del arnés:** VERDE — `./init.sh` 33 ok / 0 fallos (F034 backend-only).
Backend 200 tests, vitest 57, E2E 8/8 (última corrida --e2e en F033).

## Novedad de esta sesión (cronológico)
2 hotfixes de arnés (`+x`, Fase 2 sin Docker) · **F032 CI** · **F026 Construrama**
(2º retailer) · `dev.sh` único · **PRD v0.2** (pivote) · **F033 Búsqueda en vivo
bajo demanda** · **F034 Fix URL ficha Home Depot** (bug de uso real: `/p/{sku}`
404 → `seo.href` real; ver history).

## La app HOY
Buscar un término consulta HD+Construrama en vivo si no hay datos frescos, ingesta
y muestra canónicos comparados + crudos por tienda. Los enlaces a la ficha de HD
ahora abren la página real (seo.href), no 404. `backend/.env` (gitignored) tiene
la key de Construrama.

## Pendiente operativo
- **TODO el lote SIN pushear** (regla `ask`). Commits locales en orden:
  `1f48449` dev.sh · `339d21b` abre F033 · `0223f3c` PRD v0.2 · `b41e67e` F033 ·
  `af6151e` abre F034 · (falta el commit de cierre F034 que hace el líder ahora).
- Para limpiar las URLs viejas de HD en la BD del humano: re-buscar el producto
  (el vivo re-ingesta con refresh) o `./dev.sh` (re-seed).
- Committer local `M081899@…local` (no enlaza a GitHub `carlosmega`).

## Próximos pasos sugeridos
1. **Chore (hallazgo F033):** `next dev` + `pnpm build` comparten `.next/` →
   no correr `init.sh`/reviews con `./dev.sh` arriba. distDir separado / guard.
2. **Matching en Admin** de SKUs reales que traiga el vivo → comparación $/kg
   cross-retailer. Luego auto-match (rapidfuzz, M5).
3. **Deuda F031:** normalizar la cotización (precio nativo hoy).
4. Celery Beat como refresco programado (PRD v0.2 lo degradó a complemento M5).
5. `F012` opcional.

## Cómo levantar
```bash
./dev.sh   # backend :8800 + frontend :3300 (Ctrl+C detiene ambos)
# OJO: no correr ./init.sh ni reviews con dev.sh arriba (chore #1)
```
