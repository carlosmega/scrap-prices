# F002 — Bootstrap frontend: Next.js 15 + Tailwind + shadcn/ui

## Contexto y objetivo
Crear el frontend mínimo verificable. Igual que F001: lo que importa es que
la Fase 4 de `./init.sh` quede verde.

## Alcance
**Incluye:** app Next.js 15 (App Router, TypeScript estricto, src/),
Tailwind v4, shadcn/ui inicializado, estructura de carpetas conforme a
`docs/conventions-frontend.md`, página home placeholder.
**No incluye:** consumo real de la API (eso es F003), features de dominio.

## Pasos esperados
1. **`create-next-app` aborta en un directorio no vacío**, y `frontend/` ya
   contiene `CLAUDE.md` y `.gitkeep` (que NO están en su whitelist). Procedimiento:
   - Mover temporalmente `frontend/CLAUDE.md` (y `.gitkeep`) fuera de `frontend/`.
   - `pnpm create next-app@latest . --ts --app --src-dir --tailwind --eslint`
     dentro de `frontend/`.
   - Restaurar `frontend/CLAUDE.md`. (Alternativa: scaffoldear en un tmp y copiar.)
2. `pnpm dlx shadcn@latest init` y añadir como base: button, card, input.
3. Crear estructura: `src/features/`, `src/lib/api/` (vacía por ahora).
4. Variable `NEXT_PUBLIC_API_URL` con default `http://localhost:8000`.
5. Scripts en package.json: `dev`, `build`, `lint`, y `gen:api` placeholder.
6. **Reglas ESLint de arquitectura** (mecánicas, no de prompt) en la config:
   - Prohibir `fetch(` fuera de `src/lib/api/client.ts` (p.ej.
     `no-restricted-syntax`/`no-restricted-globals` o `import/no-restricted-paths`).
   - `@typescript-eslint/no-explicit-any: error` (cero `any`).
   - Prohibir importar `src/lib/api/schema.d.ts` editado a mano fuera del flujo `gen:api`.

## Criterios de aceptación
- [ ] Frontend: `pnpm exec tsc --noEmit`, `pnpm lint` y `pnpm build` limpios.
- [ ] Frontend: `src/components/ui/` contiene los componentes shadcn instalados por CLI/MCP.
- [ ] Frontend: la home renderiza con estilos Tailwind y un componente shadcn visible.
- [ ] Frontend: las reglas ESLint de arquitectura están activas (un `fetch` fuera
      de `client.ts` o un `any` hacen fallar `pnpm lint`).

## Plan de verificación
```bash
cd frontend && pnpm install && pnpm exec tsc --noEmit && pnpm lint && pnpm build
./init.sh   # Fase 4 debe pasar de PENDIENTE a verde
```
