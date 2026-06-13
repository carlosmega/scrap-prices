# frontend/CLAUDE.md — Reglas operativas de esta capa

Estás trabajando dentro del frontend (Next.js 15 + Tailwind v4 + shadcn/ui).
Las convenciones completas viven en `../docs/conventions-frontend.md`;
esto es lo no negociable:

1. Tipos de API SOLO desde `src/lib/api/schema.d.ts` (generado). Si el tipo
   no existe, el contrato está desactualizado: corre `pnpm gen:api` o reporta
   blocked — jamás lo declares a mano.
2. Fetch SOLO a través de `src/lib/api/client.ts`.
3. Features en `src/features/<dominio>/`; `src/components/ui/` es de shadcn
   y se instala por CLI/MCP, no se escribe a mano.
4. Server Components por defecto; `"use client"` lo más abajo posible.
5. Verificación local mínima antes de reportar:
   `pnpm exec tsc --noEmit && pnpm lint && pnpm build`
