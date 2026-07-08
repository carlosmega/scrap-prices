# Sesión activa — F033 Búsqueda en vivo bajo demanda

> El líder mantiene este archivo. Punto de retomada de la sesión.

**Feature en curso:** `F033` (in_progress) — búsqueda en vivo bajo demanda
(live-on-miss, cache-through). **Pivote de producto decidido por el humano
2026-07-07**: "busco cemento → la app consulta HD y Construrama en vivo, ingesta
y me muestra los precios; acepto la latencia". Reemplaza el §1 del PRD (scraping
solo programado).

## Decisiones de producto (cerradas con el humano, AskUserQuestion)
1. **Auto si faltan datos:** BD primero; sin datos frescos (TTL 24 h) para
   término+zona → scrape en vivo de ambos retailers dentro del request (~2–25 s),
   con cooldown 15 min por término (aunque halle 0). `live=never` como escape.
2. **Crudos por tienda:** los hallazgos sin matchear se muestran en una sección
   por retailer (nombre crudo, precio nativo, disponibilidad, frescura, link,
   agregar-a-cotización). La comparación $/kg sigue requiriendo curación en Admin.

## Plan (contract-first)
1. [hecho] `specs/F033-busqueda-en-vivo.md` (contrato completo: SearchOut,
   RawRetailerResultOut, LiveSearchInfoOut, gatillo TTL/cooldown, ScrapeRun
   +search_term/+triggered_by, guardrails intactos).
2. [hecho] F033 `in_progress`.
3. [en curso] `implementer-backend` → orquestador en vivo + contrato + migración
   + tests offline; regenera openapi.json y corre pnpm gen:api.
4. [pendiente] `implementer-frontend` → estados de carga largos, sección cruda,
   badge live, add-to-quote crudo, E2E sin red (seed +1 unmatched).
5. [pendiente] `reviewer` → APROBADO → done → history.
6. Máx 3 ciclos de review; al 3º escalo al humano.

## Arrastre
- F026 Construrama cerrada y pusheada; CI verde (run 28914381859).
- `dev.sh` commiteado local (`1f48449`) SIN pushear (regla ask para push).
- Committer local `M081899@…local` (no enlaza a cuenta GitHub).

## Cómo levantar
```bash
./dev.sh   # backend :8800 + frontend :3300 (Ctrl+C detiene ambos)
```
