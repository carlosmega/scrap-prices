# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F002** — Bootstrap frontend (Next.js 15 + Tailwind + shadcn/ui + Vitest)
**Spec:** `specs/F002-bootstrap-frontend.md`

## Plan F002

Orquestación: capa única `frontend` → `implementer-frontend` → `reviewer`.

Constraints (ya en la spec):
- `create-next-app` aborta en dir no vacío: mover `frontend/CLAUDE.md` + `.gitkeep` fuera, scaffold, restaurar `CLAUDE.md`.
- Scripts: `dev`, `build`, `lint`, `gen:api` (placeholder), `test:unit` (= `vitest run`).
- **Vitest + Testing Library** con test de humo; **ESLint de arquitectura** (no `fetch` fuera de `lib/api/client.ts`, cero `any`).
- shadcn vía CLI/MCP: button, card, input. `NEXT_PUBLIC_API_URL` default `http://localhost:8000`.
- Estructura: `src/features/`, `src/lib/api/` (vacía; el consumo de API es F003). Home placeholder con Tailwind + un componente shadcn.
- Entorno: `pnpm 11.6.0` instalado. `jq`/`docker` ausentes a propósito (no se necesitan en frontend).

Criterios de cierre: `./init.sh` verde (Fase 4) + `tsc --noEmit`/`lint`/`build`/`test:unit` limpios + review APROBADO.

**Estado:** F002 `in_progress`. Lanzando `implementer-frontend`.
