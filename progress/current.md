# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** ninguna
**Plan:** —
**Estado:** **M2 Home Depot completo y operable** (F024 infra + F025 adapter/ingestión + F027 comando
`manage.py scrape`). Todo respetuoso (UA honesto, rate-limit, stop-if-blocked) y probado offline.
`./init.sh` verde.

## Siguiente acción = del humano: corrida real de HD en su entorno
```
cd backend && uv run python manage.py seed
uv run python manage.py scrape --retailer home-depot --zone monterrey-metro --category varilla --dry-run
# si se ve bien (sin --dry-run, ingiere a PriceObservation):
uv run python manage.py scrape --retailer home-depot --zone monterrey-metro --category varilla
```

## Pendientes
- **F026 Construrama:** bloqueada por captura del body de Algolia (2ª captura HAR o ejemplo).
- **F012:** script recon (opcional, superado).
- **M5:** Celery beat (programar `scrape`), CI (GitHub Actions con `./init.sh`), logging/observabilidad, fuzzy matching, export CSV.
