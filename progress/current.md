# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F003** — Pipeline de contrato (OpenAPI Ninja → tipos TS)
**Spec:** `specs/F003-contrato-tipos.md`

## Plan F003 (contract-first, capas backend + frontend)

1. **backend** → `implementer-backend`: genera y commitea `backend/openapi.json`
   (`export_openapi_schema --api config.api.api --indent 2 --output openapi.json`).
   El contrato cambia (de inexistente a existente). NO gatear con `./init.sh` full
   (Fase 5 estará roja hasta que el frontend corra gen:api): gate = backend + openapi.json válido.
2. **frontend** → `implementer-frontend`: dep `openapi-typescript`; script `gen:api` real
   (`openapi-typescript ../backend/openapi.json -o src/lib/api/schema.d.ts`); corre `pnpm gen:api`
   → `src/lib/api/schema.d.ts`. Crea `src/lib/api/client.ts` (fetch tipado, NEXT_PUBLIC_API_URL,
   manejo de error). Home consume `GET /api/health` vía client con estados carga/error/ok.
   **OJO:** el fetch debe ser client-side (o tolerar backend caído) para no romper `pnpm build`.
3. **reviewer** → re-corre `./init.sh` (Fase 5 verde: sin drift) + criterios.

Constraints: cero tipos de API a mano (todo de schema.d.ts). CORS ya configurado (F001).

**Estado:** F003 `in_progress`. Orquestando capa backend.
