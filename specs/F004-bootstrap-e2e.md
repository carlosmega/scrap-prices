# F004 — Bootstrap E2E: Playwright + smoke test fullstack

## Contexto y objetivo
Cerrar el lazo de verificación: una prueba que ejercita backend y frontend
juntos, ejecutable con `./init.sh --e2e`.

## Alcance
**Incluye:** proyecto Playwright en `e2e/` con su propio package.json,
configuración webServer que levanta backend (`uv run python manage.py
runserver`) y frontend (`pnpm dev`), un smoke test.
**No incluye:** suites por feature (cada vertical slice trae la suya).

## Smoke test mínimo
1. Abrir `/` → la página carga (título visible).
2. El indicador de salud de la API muestra "ok" (requiere F003).

## Criterios de aceptación
- [ ] E2E: `pnpm test:e2e` desde `e2e/` levanta todo y pasa en local con docker compose arriba.
- [ ] E2E: `./init.sh --e2e` ejecuta la Fase 6 en verde.
- [ ] E2E: el reporte HTML de Playwright queda en e2e/playwright-report (gitignored).

## Plan de verificación
```bash
docker compose up -d && ./init.sh --e2e
```
