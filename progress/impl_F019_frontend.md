# Implementación F019 — UI: selección de zona (frontend + e2e)

Spec aplicada: `specs/F019-ui-seleccion-zona.md`.

## Decisiones de UI/UX (≤5 líneas)
- Home renovada como shell: `<header>` ConstruScan + `<ZoneSelector />` + `<footer>` con `HealthIndicator` discreto. Eliminado el placeholder de F003 ("aún sin consumo de API") y la card de búsqueda deshabilitada.
- Selector con shadcn `Select` (dropdown accesible); muestra `nombre · estado` por opción y un indicador de "Zona seleccionada: <nombre>".
- Tres estados del fetch de zonas (cargando/error/datos) replicando el patrón de `HealthIndicator`.
- Persistencia con hook `useSelectedZone()` sobre `localStorage` (lazy init → sobrevive recargas; sync entre pestañas vía evento `storage`); guarda solo `{id, name}` (A1·CA3).
- Botón opcional "usar mi ubicación": `navigator.geolocation` → `resolveZone()` (apiPost); 404 → "Aún sin cobertura en tu zona" (A1·CA4).

## Reglas de capa respetadas
- Cero tipos de API a mano: `Zone`/`SelectedZone` se derivan del retorno de `fetchZones()` (que viene de `schema.d.ts`). Cero `any`.
- `fetch` solo en `src/lib/api/client.ts`; el dominio usa `apiGet`/`apiPost`. `ApiError.status === 404` distingue "sin cobertura".

## Archivos creados/modificados

Frontend:
- `frontend/src/app/page.tsx` — MOD: shell nuevo, sin placeholder F003.
- `frontend/src/app/page.test.tsx` — MOD: tests al nuevo home (heading, selector, ausencia de placeholder); mock de `@/lib/api/client`.
- `frontend/src/features/zones/api.ts` — MOD: añade `resolveZone()` (apiPost a `/api/zones/resolve`).
- `frontend/src/features/zones/types.ts` — NEW: `Zone` y `SelectedZone` derivados del contrato.
- `frontend/src/features/zones/hooks/use-zones.ts` — NEW: lista zonas, tres estados.
- `frontend/src/features/zones/hooks/use-selected-zone.ts` — NEW: persistencia en localStorage.
- `frontend/src/features/zones/hooks/use-selected-zone.test.ts` — NEW: 5 tests de la persistencia.
- `frontend/src/features/zones/components/zone-selector.tsx` — NEW: organismo selector (Client Component).

Componentes shadcn añadidos (vía CLI `pnpm dlx shadcn@latest add select`):
- `frontend/src/components/ui/select.tsx` — NEW (no editado a mano).

E2E:
- `e2e/playwright.config.ts` — MOD: webServer backend ahora corre `migrate && seed && runserver` (datos sembrados: zona "Monterrey Metro").
- `e2e/tests/zone.spec.ts` — NEW: elegir "Monterrey Metro" → seleccionada → persiste tras `page.reload()`.

## Output REAL de los comandos

### `pnpm exec tsc --noEmit` (en frontend/)
```
EXIT: 0
```

### `pnpm lint` (en frontend/)
```
$ eslint
LINT_EXIT: 0
```

### `pnpm test:unit` (en frontend/)
```
$ vitest run
 RUN  v3.2.6 C:/scrap-prices/frontend
 ✓ src/features/zones/hooks/use-selected-zone.test.ts (5 tests) 35ms
 ✓ src/app/page.test.tsx (3 tests) 99ms
 Test Files  2 passed (2)
      Tests  8 passed (8)
UNIT_EXIT: 0
```

### `pnpm build` (en frontend/)
```
$ next build
   ▲ Next.js 15.5.19
   - Environments: .env.local
 ✓ Compiled successfully in 7.8s
   Linting and checking validity of types ...
 ✓ Generating static pages (5/5)
Route (app)                                 Size  First Load JS
┌ ○ /                                    40.9 kB         143 kB
└ ○ /_not-found                            990 B         103 kB
+ First Load JS shared by all             102 kB
○  (Static)  prerendered as static content
BUILD_EXIT: 0
```

### `pnpm test:e2e` (en e2e/, backend seedeado vía webServer)
```
$ playwright test
[WebServer] [14/Jun/2026 00:03:13] "GET /api/zones HTTP/1.1" 200 117
Running 2 tests using 2 workers
[1/2] [chromium] › tests\smoke.spec.ts:9:5 › la home carga y el indicador de salud muestra ok
[2/2] [chromium] › tests\zone.spec.ts:11:5 › elegir zona y que persista tras recargar
  2 passed (25.1s)
E2E_EXIT: 0
```

### `./init.sh --e2e` (raíz) — Fase 6 verde
```
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
INIT_EXIT: 0
```

## Verificación de datos para E2E
`migrate` (sin migraciones pendientes) y `seed` (idempotente) corren OK; `GET /api/zones` devuelve `[{ "name": "Monterrey Metro", "slug": "monterrey-metro", "state": "NL", ... }]`. La única zona sembrada es Monterrey Metro, que es la que el test selecciona.

## Deuda / seguimientos
- El selector Radix (`SelectContent`) renderiza en un portal; el E2E interactúa por `role="option"` y `data-testid`, robusto, pero futuros tests sobre el dropdown deben usar esos selectores.
- Persistencia de zona vive en `localStorage` (cliente). La clave de sesión para listas (`X-Session-Key`) llega en F022; F019 solo persiste `{id, name}` de la zona.
- El botón "usar mi ubicación" (A1·CA4) quedó implementado pero NO está cubierto por E2E (geolocalización requiere permisos/mocks de contexto); su lógica 404→mensaje es verificable a futuro con `context.grantPermissions` + ruta mockeada.
