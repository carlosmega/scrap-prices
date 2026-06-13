# impl F004 — Bootstrap E2E (capa e2e)

## Spec aplicada
`specs/F004-bootstrap-e2e.md`: proyecto Playwright en `e2e/` con su propio
`package.json`, `webServer` que levanta backend (SQLite, sin Docker) + frontend,
y un smoke test del flujo mínimo (home carga + indicador de salud "ok").

## Decisiones de implementación
- `webServer` como array de 2 procesos tal como exige la tarea: backend
  `uv run python manage.py runserver 127.0.0.1:8000` con `url` =
  `http://127.0.0.1:8000/api/health` (verificado: responde **200 directo**,
  `{"status": "ok"}`, sin redirect a slash), y frontend `pnpm dev --port 3000`
  con `url` = `http://localhost:3000`. Ambos `timeout: 120000`,
  `reuseExistingServer: !process.env.CI`.
- `@playwright/test` se resolvió a la versión real instalada (1.60.0); el
  `package.json` quedó pineado a `^1.60.0` para no dejar drift contra el
  lockfile. Navegador chromium ya cacheado (chromium-1223, el que pide 1.60.0).
- El smoke verifica el heading por rol (`getByRole("heading", {name:"ConstruScan"})`)
  y el estado "ok" con `getByText(/ok/i)` (timeout 15s) — `HealthIndicator`
  renderiza "Backend: ok" en el estado de datos (`health.value` = `data.status`).
- Reporter HTML a `e2e/playwright-report` (ya gitignored vía
  `playwright-report/` en la raíz). Solo se versionan fuentes:
  `package.json`, `playwright.config.ts`, `pnpm-lock.yaml`, `tests/`.

## Archivos creados
- `e2e/package.json` — script `"test:e2e": "playwright test"`, dep `@playwright/test ^1.60.0`.
- `e2e/playwright.config.ts` — webServer array (backend+frontend), `baseURL`, proyecto chromium, reporter html.
- `e2e/tests/smoke.spec.ts` — smoke fullstack.
- `e2e/pnpm-lock.yaml` — generado por `pnpm install`.

No se tocó `backend/` ni código de `frontend/`.

## Output REAL de los comandos

### 1. `pnpm install` (en `e2e/`)
```
Packages: +3
+++
Progress: resolved 4, reused 0, downloaded 2, added 2
Progress: resolved 4, reused 0, downloaded 3, added 3, done

devDependencies:
+ @playwright/test 1.60.0

Done in 5s using pnpm v11.6.0
```
(tras pinear a ^1.60.0, `pnpm install` → "Already up to date", lockfile OK)

### 2. `pnpm exec playwright install chromium` (en `e2e/`)
```
(sin descarga: chromium-1223 ya en C:\Users\m081899\AppData\Local\ms-playwright)
EXIT=0
```
Confirmado con `--dry-run`:
```
Chrome for Testing 148.0.7778.96 (playwright chromium v1223)
  Install location:    C:\Users\m081899\AppData\Local\ms-playwright\chromium-1223
```

### 3. `pnpm test:e2e` (desde `e2e/`, Playwright levanta backend+frontend)
```
$ playwright test
[WebServer] Watching for file changes with StatReloader
[WebServer] [13/Jun/2026 14:46:43] "GET /api/health HTTP/1.1" 200 16
[WebServer] $ next dev "--port" "3000"

Running 1 test using 1 worker

[1/1] [chromium] › tests\smoke.spec.ts:9:5 › la home carga y el indicador de salud muestra ok
[WebServer] [13/Jun/2026 14:47:00] "GET /api/health HTTP/1.1" 200 16

  1 passed (21.5s)
EXIT=0
```
(el primer GET /api/health 200 es el health-check del webServer; el segundo es
el fetch client-side del navegador durante el test → el lazo fullstack real.)

### 4. `./init.sh --e2e` (desde la raíz) — Fase 6 en VERDE
```
── Fase 6 · E2E (Playwright) ──
  ✔ pnpm install
  ✔ suite Playwright

════════ Resumen ════════
  ✔ 33 ok   ✘ 0 fallos   ◌ 3 pendientes
  VERDE — el arnés está en estado consistente.
INIT_EXIT=0
```
(Fase 3 backend, Fase 4 frontend, Fase 5 contrato: todas verdes también.)

## Verificación de artefactos
- `e2e/playwright-report/index.html` generado (526 KB).
- `git check-ignore` confirma que `e2e/playwright-report`, `e2e/test-results`
  y `e2e/node_modules` están ignorados.

## Deuda / seguimientos
- Suites E2E por slice vertical (M4+) aún no existen; F004 solo monta el smoke
  base, como dicta la spec ("No incluye: suites por feature").
- `reuseExistingServer` deja servidores vivos en local entre corridas; si un
  `runserver`/`next dev` previo quedó en el puerto, se reusa. En CI (`process.env.CI`)
  siempre arranca limpio. Sin impacto en el gate.
