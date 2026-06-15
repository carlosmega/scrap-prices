# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** ninguna
**Plan:** —
**Estado:** 🎉 **Pipeline de Home Depot funcionando end-to-end CONTRA EL SITIO REAL.**
`scrape` (corrida real desde el sandbox, con red) ingirió **13 productos reales** de varilla de HD
Monterrey → 13 `PriceObservation` (source=xhr) + `ScrapeRun` ok. Validado por el líder en vivo.
`./init.sh` verde (offline). M2 Home Depot completo: F024 infra + F025 adapter + F027 comando +
F028 tienda 1333 + F029 params de búsqueda.

## Detalle / siguiente paso del dominio
- Los 13 `RetailerProduct` scrapeados quedan **`unmatched`**: el matching a `CanonicalProduct` es
  **manual en Admin** (decisión MVP, D1/§11). Hasta matchearlos, la búsqueda de la UI (que es sobre
  canónicos) sigue mostrando los 3 canónicos del seed. Para ver precios reales comparados:
  curar el match `RetailerProduct → CanonicalProduct` en `/admin` (o, fase posterior, fuzzy con rapidfuzz).

## Pendientes
- **Matching manual** de los SKUs reales de HD a canónicos (Admin) para que la comparación muestre datos reales.
- **F026 Construrama:** captura del body de Algolia.
- **M5:** Celery beat (programar `scrape`), CI, logging, fuzzy matching (auto-match), export CSV.
- La BD local (`db.sqlite3`, gitignored) ya tiene datos reales de HD de esta corrida.
