# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** ninguna
**Plan:** —
**Estado:** 🎉 **Vertical Home Depot completo con datos REALES y visibles en la app.**
Lazo end-to-end probado en vivo: `scrape` real → 13 `PriceObservation` (source=xhr) → matching manual
de 8 varillas reales a canónicos → la búsqueda "varilla" muestra precios reales de HD ($20,068 R-42/ton).
`./init.sh` verde (offline). M2 HD: F024 infra + F025 adapter + F027 cmd + F028 tienda 1333 + F029 params búsqueda.

## Notas de la curación (estado de la BD local, db.sqlite3, gitignored)
- Matching manual hecho por script (curación, como en Admin): 8 RetailerProducts de varilla HD → canónicos 1:1.
  Quedan 5 unmatched (castillo) — no varilla. **Un "bolardo" entró porque su nombre dice "...cimentación varilla"**
  (se puede desmatchear si se quiere más limpio).
- **Unidad:** las R-42 reales son **por TONELADA** ($20,068); los 3 canónicos del seed son por pieza. NO comparar
  esos números entre unidades hasta normalizar (M5). Para HD solo, el dato es correcto con su unidad.

## Pendientes (el payoff de comparación real)
1. **Construrama (F026):** captura del body de Algolia (tu paso) → 2º retailer real.
2. **Normalización de unidad (M5):** precio por kg/pieza comparable (HD ton vs Construrama kg vs pieza).
3. **M5 resto:** auto-match rapidfuzz, Celery beat (programar scrape), CI, logging, export.
