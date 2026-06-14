# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F014** — API de zonas (GET /api/zones, POST /api/zones/resolve)
**Spec:** `specs/F014-api-zonas.md`

## Plan F014 (contract-first, capas backend + frontend)
1. **backend** → `implementer-backend`: `apps/geo/api.py` (router sin ORM) + `schemas.py`
   (ZoneOut, ResolveIn) + lógica de resolución en `services.py`; montar router en
   `config/api.py`; **regenerar `backend/openapi.json`**. Tests de ambos endpoints + 404.
2. **frontend** → `implementer-frontend`: `pnpm gen:api` para sincronizar `schema.d.ts`
   (sin UI; la UI de zona es F019). Verificar sin drift.
3. **reviewer** → `./init.sh` (Fase 5 sin drift) + criterios.

**Estado:** F014 `in_progress`. Orquestando capa backend. (M3: F013 ✅ → **F014** → F015…)
