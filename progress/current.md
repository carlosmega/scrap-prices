# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F023** — Puertos fijos locales (backend 8800, frontend 3300)
**Spec:** `specs/F023-puertos-fijos.md`

## Plan F023 (3 capas: backend + frontend + e2e)
Objetivo: dev local SIEMPRE en backend `:8800` / frontend `:3300`.
1. **backend** → CORS_ALLOWED_ORIGINS default → http://localhost:3300 (settings.py). No toca contrato.
2. **frontend** → NEXT_PUBLIC_API_URL default → http://localhost:8800 (env.ts + .env files);
   `dev`/`start` con `--port 3300`. + **e2e** playwright.config: backend 8800, frontend 3300, baseURL.
3. **líder** → .env.example, AGENTS.md, README, scripts dev-backend.sh/dev-frontend.sh.
4. **reviewer** → `./init.sh --e2e` verde en puertos nuevos + preflight CORS desde :3300.

Orden: backend (CORS) primero, luego frontend+e2e (el E2E en :3300 necesita CORS que permita :3300).

**Estado:** F023 `in_progress`. Lanzando capa backend.
