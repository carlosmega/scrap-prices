# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** ninguna
**Plan:** —
**Estado:** M2 Home Depot completo y operable, con la **tienda real de Monterrey (1333)** en el seed (F028).
Listo para la **corrida real de HD** en el entorno del humano:
`uv run python manage.py scrape --retailer home-depot --zone monterrey-metro --category varilla --dry-run`.
`./init.sh` verde.

## Pendientes
- **F026 Construrama:** captura del body de Algolia.
- **M5:** Celery beat (programar scrape), CI, logging, fuzzy matching, export.
- Si la corrida real de HD revela que el endpoint de búsqueda necesita `stLocId=18503`/`marketId=10`
  (recon §2.2), ajustar el adapter (follow-up).
