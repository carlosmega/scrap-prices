# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F017** — API listas de cotización (CRUD listas + items, anónimo/sesión)
**Spec:** `specs/F017-api-listas.md`

## Plan F017 (contract-first, backend + frontend; slice grande, 8 endpoints)
1. backend: CRUD /api/lists + /api/lists/{id} + /api/lists/{id}/items. Identidad anónima
   por header `X-Session-Key` (→ UserList.session_key, F009). Snapshot inmutable de precio al
   agregar item (última obs en la zona de la lista). subtotal/total (reusa services F009).
   404 cross-session, 422 validación, 400 sin header. Router sin ORM. Regenera openapi.json.
2. frontend: `pnpm gen:api` + **extiende client.ts** con apiPost/apiPatch/apiDelete tipados
   (fetch solo en client.ts). Sin UI (la UI de lista es F022). Sin drift.
3. reviewer: `./init.sh` Fase 5 sin drift + criterios (snapshot inmutable, scoping sesión).

**Estado:** F017 `in_progress`. M3: F013–F016 ✅ → **F017** → F018.
