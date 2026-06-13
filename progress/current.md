# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F004** — Bootstrap E2E (Playwright + smoke fullstack)
**Spec:** `specs/F004-bootstrap-e2e.md`

## Plan F004 (capa única e2e → implementer-frontend)

1. Proyecto `e2e/` con su propio `package.json`, `@playwright/test`, script `test:e2e` (= `playwright test`).
2. `playwright.config.ts` con `webServer` (array de 2): backend (`uv run python manage.py runserver 127.0.0.1:8000`, cwd `../backend`) y frontend (`pnpm dev`, cwd `../frontend`, :3000). `baseURL` http://localhost:3000, `reuseExistingServer: !process.env.CI`, timeouts generosos.
3. Instalar navegador: `pnpm exec playwright install chromium`.
4. Smoke `e2e/tests/smoke.spec.ts`: abrir `/` (título/heading visible) + el indicador de salud muestra **"ok"** (aquí SÍ corre el backend → camino "ok" de F003 ejercitado).
5. Reporte HTML en `e2e/playwright-report` (gitignored).

Cierre: `pnpm test:e2e` desde `e2e/` pasa + `./init.sh --e2e` Fase 6 verde + review APROBADO.

Notas: backend SQLite/sin-Docker; `/api/health` es estático (no necesita migrate). CORS para :3000 ya configurado (F001).

**Estado:** F004 `in_progress`. Lanzando `implementer-frontend` (capa e2e).
