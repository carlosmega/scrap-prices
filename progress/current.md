# Sesión activa — HANDOFF

> El líder mantiene este archivo. Punto de retomada para la próxima sesión.

**Feature en curso:** ninguna. **`feature_list.json`:** 31 `done`, pendiente
`F012` (opcional).

**Estado del arnés:** VERDE — `./init.sh --e2e` re-ejecutado por el reviewer
(35 ok / 0 fallos). Backend 186 tests, vitest 57, E2E 8/8.

## Novedad de esta sesión (cronológico)
- 2 hotfixes de arnés (`+x`, Fase 2 sin Docker) · **F032 CI** (Actions verde en
  cada push) · **F026 ConstruramaAdapter** (2º retailer) · `dev.sh` único ·
  **PRD v0.2** (pivote) · **F033 Búsqueda en vivo bajo demanda** (cerrada,
  APROBADO; ver history).
- `backend/.env` local (gitignored) con `CONSTRURAMA_ALGOLIA_SEARCH_KEY` de la
  captura HAR del humano → el vivo de Construrama funciona en dev.

## La app HOY
Buscar un término sin datos (p.ej. "cemento") consulta HD+Construrama EN VIVO
(~2–25 s), ingesta y muestra: canónicos comparados $/kg + crudos por tienda
(add-to-quote incluido). Término con datos frescos = instantáneo de BD.

## Pendiente operativo
- **TODO el lote SIN pushear** (regla `ask`): dev.sh, apertura F033, PRD v0.2,
  feature F033 completa y cierre. El humano aprueba el push.
- Prueba de humo del humano pendiente: `./dev.sh` → buscar "cemento" (primera
  corrida real del vivo con red).
- Committer local `M081899@…local` (no enlaza a GitHub `carlosmega`).

## Próximos pasos sugeridos
1. **Chore (hallazgo del reviewer):** `next dev` + `pnpm build` comparten
   `.next/` → correr `init.sh`/reviews con `./dev.sh` arriba corrompe el dev
   server (mordió 2 veces en F033). Candidatos: distDir separado para builds de
   verificación, guard en dev.sh, o health-check de chunks en Fase 6.
2. **Matching en Admin** de los SKUs reales que traiga el vivo (cemento, etc.)
   → habilita comparación $/kg cross-retailer de lo nuevo. Luego auto-match
   (rapidfuzz, M5).
3. **Deuda F031:** cotización en precio nativo ("Agregar 1" de SKU por tonelada
   = 1 tonelada).
4. Celery Beat como refresco programado (PRD v0.2 lo degradó a complemento M5).
5. `F012` opcional.

## Cómo levantar
```bash
./dev.sh   # backend :8800 + frontend :3300 (Ctrl+C detiene ambos)
# OJO: no correr ./init.sh ni reviews mientras dev.sh esté arriba (ver chore #1)
```
