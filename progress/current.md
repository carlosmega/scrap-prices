# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F018** — API retailers interno (GET /api/retailers)
**Spec:** `specs/F018-api-retailers.md`

## Plan F018 (contract-first, backend + frontend; último de M3)
1. backend: `GET /api/retailers` → RetailerOut[] (scraper_status, pricing_model, orden por name)
   en apps/geo (api/schemas/services). Sin ORM en router. Regenera openapi.json.
2. frontend: `pnpm gen:api`. Sin drift.
3. reviewer: `./init.sh` Fase 5 sin drift + criterios.

**Estado:** F018 `in_progress`. Cierra M3 (F013–F018). Luego M4 UI (F019–F022).
