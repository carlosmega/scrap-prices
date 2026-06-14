# F023 — Puertos fijos locales: backend 8800, frontend 3300

> Cambio operativo solicitado por el humano. Toca backend (CORS), frontend (env +
> script dev) y e2e (Playwright). El contrato OpenAPI NO cambia.

## Contexto y objetivo
Que el desarrollo local corra **siempre** con backend en `:8800` y frontend en
`:3300` (antes 8000/3000), de forma coherente en las tres capas y en el E2E.

## Estado objetivo (puertos)
- **Backend (Django runserver): 8800** (`127.0.0.1:8800`).
- **Frontend (Next dev): 3300**.
- `NEXT_PUBLIC_API_URL` por defecto → `http://localhost:8800`.
- `CORS_ALLOWED_ORIGINS` por defecto → `http://localhost:3300`.

## Alcance por capa
**Backend (`implementer-backend`):**
- `config/settings.py`: `CORS_ALLOWED_ORIGINS` default → `http://localhost:3300`
  (sigue leyéndose de env; solo cambia el default). NO toca endpoints → no regenerar openapi.json.

**Frontend (`implementer-frontend`):**
- `src/lib/env.ts`: default de `NEXT_PUBLIC_API_URL` → `http://localhost:8800`.
- `frontend/.env.local` y `frontend/.env.example`: `NEXT_PUBLIC_API_URL=http://localhost:8800`.
- `package.json`: `"dev": "next dev --port 3300"` (y `"start": "next start --port 3300"` si existe).
- Busca cualquier otra referencia a `:8000`/`:3000` en `frontend/src` y actualízala.

**E2E (`implementer-frontend`, capa e2e):**
- `e2e/playwright.config.ts`: webServer backend → `runserver 127.0.0.1:8800` con `url`
  `http://127.0.0.1:8800/api/health`; webServer frontend → `pnpm dev --port 3300` con
  `url` `http://localhost:3300`; `use.baseURL` → `http://localhost:3300`.

**Raíz/docs (líder):** `.env.example` (CORS→3300, API→8800), `AGENTS.md` (comandos
canónicos con los puertos nuevos), `README.md`, y scripts de conveniencia
`dev-backend.sh`/`dev-frontend.sh` para arrancar en los puertos fijos.

## Criterios de aceptación
- [ ] **Backend:** `CORS_ALLOWED_ORIGINS` default incluye `http://localhost:3300`;
      preflight `OPTIONS` desde `Origin: http://localhost:3300` responde
      `access-control-allow-origin: http://localhost:3300`. `ruff`/`pytest` verdes.
- [ ] **Frontend:** `pnpm dev` levanta en `:3300`; `NEXT_PUBLIC_API_URL` apunta a
      `:8800` por defecto. `tsc`/`lint`/`build`/`test:unit` verdes. Cero `:8000`/`:3000`
      residual en `frontend/src`.
- [ ] **E2E:** `./init.sh --e2e` VERDE con los servidores en `:8800`/`:3300` (las 5
      specs pasan, incluido el lazo fullstack contra `:8800`).
- [ ] `./init.sh` y `./init.sh --e2e` verdes; contrato sin drift (Fase 5).

## Plan de verificación
```bash
# backend
cd backend && uv run ruff check . && uv run pytest -q
# frontend
cd ../frontend && pnpm exec tsc --noEmit && pnpm lint && pnpm build && pnpm test:unit
# fullstack en puertos nuevos
cd .. && ./init.sh --e2e
```

## Notas y decisiones abiertas
- El default de `runserver` de Django es 8000; "siempre 8800" se logra con el
  comando/scripts de conveniencia (no hay default-port nativo). `--port`/`PORT`
  pueden sobreescribir el frontend si hace falta.
- Specs históricas (F002/F003/F004) mencionan 8000/3000 como registro; no se
  reescriben (son bitácora), pero la config viva queda en 8800/3300.
