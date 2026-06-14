# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F016** — API detalle de producto + historial (GET /api/products/{id})
**Spec:** `specs/F016-api-detalle-producto.md`

## Plan F016 (contract-first, backend + frontend)
1. backend: `/api/products/{id}?zone_id=` → ProductDetailOut (canónico+specs, prices por retailer
   reusando F015, history últimas N obs orden -captured_at). 404 producto/zona. Regenera openapi.json.
2. frontend: `pnpm gen:api` (sin UI; la UI de detalle es F021). Sin drift.
3. reviewer: `./init.sh` Fase 5 sin drift + criterios.

**Estado:** F016 `in_progress`. M3: F013 ✅ F014 ✅ F015 ✅ → **F016** → F017 → F018.
