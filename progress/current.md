# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F015** — API de búsqueda (GET /api/search)
**Spec:** `specs/F015-api-busqueda.md`

## Plan F015 (contract-first, capas backend + frontend)
1. **backend**: `/api/search?q=&zone_id=&sort=` — canónicos + precio más fresco por retailer
   en la zona (reusa `apps/prices/services.ultima_observacion`). q tolerante a acentos (SQLite
   icontains + normalización). sort por precio/nombre. retailer sin obs → price null. 404 zona.
   Lógica en services, router sin ORM. Regenerar openapi.json.
2. **frontend**: `pnpm gen:api` (sin UI; la UI de búsqueda es F020). Sin drift.
3. **reviewer**: `./init.sh` Fase 5 sin drift + criterios.

**Estado:** F015 `in_progress`. M3: F013 ✅ F014 ✅ → **F015** (búsqueda, capacidad central).
