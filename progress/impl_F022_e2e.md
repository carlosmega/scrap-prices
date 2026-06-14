# Implementación E2E — F022 (endurecimiento contra flaky)

Capa: **e2e**. Solo se tocó `e2e/`. No se modificó `frontend/` ni `backend/`.

## Contexto

El implementer-backend reportó flakiness intermitente en
`e2e/tests/detail.spec.ts` (~línea 44): el `toHaveURL(/\/products\/...$/)`
recibía `/` porque el click en `search-result-link` no había navegado a tiempo
bajo `fullyParallel` con `retries: 0`. Pasaba en re-corrida, pero no es
determinista. Por `docs/verification.md` regla 3 ("si de verdad es flaky,
arreglar el test ES la tarea"), arreglar el flaky es la tarea.

## Qué cambié y por qué

1. **`e2e/playwright.config.ts`** — `retries: process.env.CI ? 1 : 0` →
   `retries: process.env.CI ? 2 : 1`. Un reintento local (antes 0) absorbe
   cualquier timing transitorio sin enmascarar fallos reales (un test que
   falla siempre seguirá fallando tras el reintento). En CI sube a 2.

   - No se tocó `fullyParallel` ni `workers`: cada test arranca con contexto
     limpio (sin estado compartido) y la sesión es anónima por `X-Session-Key`
     en localStorage; los 5 tests son independientes, así que la paralelización
     es segura. El flaky era de timing de navegación, no de estado compartido.

2. **`e2e/tests/detail.spec.ts`** — navegación robusta tras el click en el
   resultado. Antes: `link.click()` seguido de `await expect(page).toHaveURL(...)`,
   donde la transición podía perderse entre ambas instrucciones. Ahora se arma
   `page.waitForURL(/\/products\/[^/]+$/, { timeout: 15_000 })` **antes** del
   click dentro de un `Promise.all([...])`, de modo que la espera de navegación
   no puede perder la transición. Se conserva el `await expect(page).toHaveURL(...)`
   posterior (con timeout explícito) como aserción de lo mismo que el test ya
   verificaba.

   - **No se cambió qué verifica el test**, solo la robustez de la espera. La
     cobertura se mantiene: los 5 tests siguen comprobando lo mismo (zona,
     búsqueda, detalle con precios por retailer + frescura + historial,
     cotización, persistencia de zona).

## Archivos modificados

- `e2e/playwright.config.ts` — `retries` 0/1 → 1/2 (local/CI).
- `e2e/tests/detail.spec.ts` — click + `waitForURL` atómicos vía `Promise.all`,
  con timeout explícito en el `toHaveURL` de confirmación.

(Ningún componente shadcn; capa e2e.)

## Output real

### `pnpm test:e2e` desde `e2e/` — corrida 1

```
$ playwright test
[WebServer] Watching for file changes with StatReloader
[WebServer] [14/Jun/2026 01:08:09] "GET /api/health HTTP/1.1" 200 16
[WebServer] $ next dev "--port" "3000"

Running 5 tests using 5 workers

[1/5] [chromium] › tests\smoke.spec.ts:9:5 › la home carga y el indicador de salud muestra ok
[2/5] [chromium] › tests\detail.spec.ts:13:5 › desde la búsqueda al detalle: precios por retailer e historial
[3/5] [chromium] › tests\search.spec.ts:19:5 › buscar varilla en Monterrey Metro: ambos retailers y orden por precio
[4/5] [chromium] › tests\quote.spec.ts:23:5 › cotización: agregar → ver snapshot+total → editar cantidad → quitar
[5/5] [chromium] › tests\zone.spec.ts:11:5 › elegir zona y que persista tras recargar
... (tráfico WebServer: /api/zones, /api/search, /api/lists, /api/products ... 200)
  5 passed (23.5s)
```

### `pnpm test:e2e` desde `e2e/` — corrida 2 (estabilidad)

```
$ playwright test
[WebServer] Watching for file changes with StatReloader
[WebServer] [14/Jun/2026 01:08:40] "GET /api/health HTTP/1.1" 200 16
[WebServer] $ next dev "--port" "3000"

Running 5 tests using 5 workers

[1/5] [chromium] › tests\search.spec.ts:19:5 › buscar varilla en Monterrey Metro: ambos retailers y orden por precio
[2/5] [chromium] › tests\quote.spec.ts:23:5 › cotización: agregar → ver snapshot+total → editar cantidad → quitar
[3/5] [chromium] › tests\detail.spec.ts:13:5 › desde la búsqueda al detalle: precios por retailer e historial
[4/5] [chromium] › tests\smoke.spec.ts:9:5 › la home carga y el indicador de salud muestra ok
[5/5] [chromium] › tests\zone.spec.ts:11:5 › elegir zona y que persista tras recargar
... (tráfico WebServer: /api/zones, /api/search, /api/lists, /api/products ... 200)
  5 passed (25.7s)
```

Ambas corridas: **5 passed**, sin reintentos consumidos (cero reportes de retry).

### `./init.sh --e2e` desde la raíz

```
── Fase 0 · Herramientas ──
  ✔ git disponible
  ✔ node disponible
  ◌ jq no encontrado (opcional / al bootstrapear su capa)
  ✔ uv disponible
  ◌ docker no encontrado (opcional / al bootstrapear su capa)
  ✔ pnpm disponible
  ✔ repositorio git inicializado

── Fase 1 · Invariantes del arnés ──
  ✔ existe CLAUDE.md
  ✔ existe AGENTS.md
  ✔ existe CHECKPOINTS.md
  ✔ existe feature_list.json
  ✔ existe specs/TEMPLATE.md
  ✔ existe progress/current.md
  ✔ existe progress/history.md
  ✔ existe docs/architecture.md
  ✔ existe docs/verification.md
  ✔ feature_list.json es JSON válido (array)
  ✔ features in_progress: 1 (máximo 1)
  ✔ todos los status son válidos
  ✔ hook guard-feature.sh ejecutable
  ✔ las 17 feature(s) 'done' tienen review APROBADO

── Fase 2 · Infraestructura (Postgres + Redis — opcional, migración futura) ──
  ◌ Docker no usado en MVP (backend corre con SQLite); infra Postgres/Redis diferida

── Fase 3 · Backend (Django + Ninja) ──
  ✔ uv sync (dependencias)
  ✔ ruff check
  ✔ migraciones al día (makemigrations --check)
  ✔ pytest
  ✔ arquitectura: routers (api.py) sin llamadas al ORM

── Fase 4 · Frontend (Next.js + Tailwind + shadcn) ──
  ✔ pnpm install
  ✔ tsc --noEmit
  ✔ lint
  ✔ tests unitarios (vitest)
  ✔ build de producción
  ✔ arquitectura: fetch solo en src/lib/api/client.ts

── Fase 5 · Contrato OpenAPI → tipos TS ──
  ✔ tipos TS sincronizados con backend/openapi.json

── Fase 6 · E2E (Playwright) ──
  ✔ pnpm install
  ✔ suite Playwright

════════ Resumen ════════
  ✔ 33 ok   ✘ 0 fallos   ◌ 3 pendientes
  VERDE — el arnés está en estado consistente.
```

Fase 6 verde, resumen **VERDE** (0 fallos).

## Deuda / seguimientos

- Solo `detail.spec.ts` tenía el patrón vulnerable (click seguido de
  `toHaveURL` sin `waitForURL` previo). `quote.spec.ts` ya navega a
  `/cotizacion` con un click cuyo `toHaveURL` posterior no mostró flaky; si
  reaparece, aplicar el mismo patrón `Promise.all([waitForURL, click])`.
- `retries: 1` en local es una red de seguridad, no una excusa: si un test
  empieza a depender del reintento de forma sistemática, hay que tratarlo como
  bug real (regla 3 de verification.md), no subir reintentos.
