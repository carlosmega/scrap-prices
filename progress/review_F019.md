Veredicto: APROBADO

# Review F019 — UI: selección de zona (persistente en sesión)

Feature: F019 (capas: frontend + e2e). Spec: `specs/F019-ui-seleccion-zona.md`.
Revisor: re-ejecutó la verificación global (`./init.sh --e2e`) y greps deterministas;
no se confió en el output pegado por el implementer.

## Resultado de la corrida real

`./init.sh --e2e` terminó **VERDE** (INIT_EXIT=0): **33 ok · 0 fallos · 3 pendientes**.
Los 3 pendientes son esperados en el MVP SQLite/sin-Docker (jq, docker, Fase 2),
no fallos. **Fase 6 (Playwright) verde**; la suite corrió 2 specs (smoke F004 +
zona F019), ambas pasaron.

## Criterios de aceptación de la spec

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | Home muestra el selector; elegir "Monterrey Metro" queda seleccionada y persiste tras recargar | CUMPLE | `frontend/src/app/page.tsx:25` renderiza `<ZoneSelector />`. `e2e/tests/zone.spec.ts` abre `/`, elige la opción `/monterrey metro/i`, asevera `selected-zone` contiene "Monterrey Metro", hace `page.reload()` (línea 36) y vuelve a aseverar (líneas 37-39). La suite Playwright pasó en mi corrida real (`pnpm test:e2e` → `2 passed`, `zone.spec.ts` incluido). |
| 2 | Selector maneja carga/error/datos; tipos de `schema.d.ts` (cero a mano), cero `any`, `fetch` solo en `client.ts` | CUMPLE | `use-zones.ts` expone `loading`/`ready`/`error` y `zone-selector.tsx` renderiza los tres (líneas 109-196). `types.ts:11` deriva `Zone` de `Awaited<ReturnType<typeof fetchZones>>` → `ZoneOut` (`schema.d.ts:244`, campos `id/name/slug/state`). `grep ": any\|as any" frontend/src` → VACÍO. `grep "\bfetch(" frontend/src` salvo `client.ts` → VACÍO. |
| 3 | Ya no queda el placeholder de F003 en la home | CUMPLE | `grep -ni "aún sin consumo\|sin consumo de api\|placeholder" frontend/src/app/page.tsx` → VACÍO (RC=1). El texto solo aparece en `page.test.tsx:40` como aserción negativa (`queryByText(/aún sin consumo de api/i)).not.toBeInTheDocument()`). |
| 4 | `pnpm test:e2e` (backend seedeado) pasa selección+persistencia; `./init.sh --e2e` Fase 6 verde | CUMPLE | `playwright.config.ts:34-35` el webServer de backend corre `migrate && seed && runserver`. Logs `GET /api/zones HTTP/1.1 200` confirman datos sembrados. Fase 6 verde en mi corrida (ver output abajo). |
| 5 | `tsc --noEmit`, `lint`, `build`, `test:unit` limpios; `./init.sh` y `--e2e` verdes | CUMPLE | Fase 4 de `init.sh` (mi corrida): `tsc --noEmit` ✔, `lint` ✔, `tests unitarios (vitest)` ✔, `build de producción` ✔. Fase 6 ✔. Resumen VERDE. |

## CHECKPOINTS.md

### Global
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `./init.sh` verde de punta a punta | CUMPLE | `./init.sh --e2e` → 0 fallos, VERDE (output abajo). |
| Exactamente la feature actual `in_progress`; ninguna otra cambió | CUMPLE | `feature_list.json`: F019 `in_progress`; Fase 1 `features in_progress: 1 (máximo 1)` ✔. |
| Existe `progress/impl_<id>_<capa>.md` por capa con output real | CUMPLE | `progress/impl_F019_frontend.md` presente (cubre frontend + e2e, las dos capas las llevó el implementer-frontend). |
| Cumple la spec criterio por criterio | CUMPLE | Tabla de criterios arriba: 5/5 CUMPLE. |

### Frontend
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `tsc --noEmit` limpio | CUMPLE | Fase 4 ✔ (mi corrida). |
| `lint` limpio | CUMPLE | Fase 4 ✔. |
| `build` pasa | CUMPLE | Fase 4 `build de producción` ✔. |
| Componentes shadcn vía CLI en `src/components/ui/` | CUMPLE | `src/components/ui/select.tsx` presente (6679 bytes), junto a button/card/input. No editado a mano (impl reporta `pnpm dlx shadcn add select`). |
| Todo fetch maneja carga y error | CUMPLE | `use-zones.ts` y `use-selected-zone.ts` manejan estados; `zone-selector.tsx` muestra carga/error/no-cobertura. |
| Ningún `fetch(` fuera de `client.ts`; cero `any` | CUMPLE | Greps deterministas → VACÍO ambos; Fase 4 `arquitectura: fetch solo en src/lib/api/client.ts` ✔. |

### Contrato
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `schema.d.ts` sin drift vs `backend/openapi.json` | CUMPLE | Fase 5 `tipos TS sincronizados con backend/openapi.json` ✔. (F019 no cambió el contrato; usa `ZoneOut`/`ResolveIn` ya existentes.) |
| Frontend no declara tipos de API a mano | CUMPLE | `types.ts` deriva todo de `fetchZones()`; cero formas de API escritas a mano. |

### E2E
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| Smoke de `e2e/` pasa con `--e2e` | CUMPLE | `smoke.spec.ts` pasó (mi corrida: `2 passed`). |
| Test E2E propio del flujo feliz | CUMPLE | `e2e/tests/zone.spec.ts` cubre selección + persistencia tras `page.reload()`. |

### Higiene del arnés
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `feature_list.json` válido con ≤1 `in_progress` | CUMPLE | Fase 1 ✔. |
| `progress/current.md` refleja la realidad | NO VERIFICABLE (fuera del alcance del review; lo mantiene el líder) | Existe (Fase 1 ✔). |
| Toda feature `done` tiene su review APROBADO | CUMPLE | Fase 1 `las 14 feature(s) 'done' tienen review APROBADO` ✔. |
| Repo git inicializado | CUMPLE | Fase 0 `repositorio git inicializado` ✔. |

## Diff y aislamiento de capa

`git status --porcelain`:
```
 M e2e/playwright.config.ts
 M frontend/src/app/page.test.tsx
 M frontend/src/app/page.tsx
 M frontend/src/features/zones/api.ts
?? e2e/tests/zone.spec.ts
?? frontend/src/components/ui/select.tsx
?? frontend/src/features/zones/components/
?? frontend/src/features/zones/hooks/
?? frontend/src/features/zones/types.ts
?? progress/impl_F019_frontend.md
```
Solo `frontend/`, `e2e/` y `progress/`. **Cero archivos en `backend/`** — correcto:
F019 no toca backend.

## Greps de arquitectura (deterministas)

- `grep -rn "fetch(" frontend/src --include=*.ts --include=*.tsx | grep -v "lib/api/client.ts"` → **VACÍO** (RC=1).
- `grep -rnE "\bfetch\(" frontend/src ... | grep -v client.ts` → **VACÍO** (RC=1).
- `grep -rn ": any\b\|as any" frontend/src` → **VACÍO** (RC=1).
- `grep -ni "aún sin consumo\|sin consumo de api\|placeholder" frontend/src/app/page.tsx` → **VACÍO** (RC=1).

## Tests que sí prueban algo (regla "git stash mental")

- `use-selected-zone.test.ts`: el test "recupera la zona persistida en un montaje
  nuevo (sobrevive recarga)" siembra `localStorage` y verifica que un hook recién
  montado la lee. Sin el lazy-initializer de `useSelectedZone` (línea 58-60), este
  test fallaría → prueba la persistencia, no humo.
- `zone.spec.ts`: el `page.reload()` + re-aserción fallaría si la selección viviera
  solo en estado React (se perdería al recargar). Ejercita el requisito real A1·CA3.
- `page.test.tsx`: aserción negativa del placeholder F003 fallaría si el texto
  siguiera en la home.

## Output REAL de `./init.sh --e2e`

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
  ✔ las 14 feature(s) 'done' tienen review APROBADO

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

INIT_EXIT=0
```

### Detalle de Fase 6 (corrida directa `pnpm test:e2e` para ver las specs)

```
Running 2 tests using 2 workers
[1/2] [chromium] › tests\zone.spec.ts:11:5 › elegir zona y que persista tras recargar
[2/2] [chromium] › tests\smoke.spec.ts:9:5 › la home carga y el indicador de salud muestra ok
[WebServer] [14/Jun/2026 00:08:41] "GET /api/zones HTTP/1.1" 200 117
  2 passed (17.7s)
E2E_EXIT=0
```
El `GET /api/zones 200` confirma backend levantado con `migrate`+`seed` (datos reales).

## Conclusión

Todos los criterios de la spec y los puntos aplicables de CHECKPOINTS.md (Global,
Frontend, Contrato, E2E, Higiene) CUMPLEN. La verificación global (`./init.sh --e2e`)
termina VERDE con Fase 6 (Playwright) verde y la suite ejerciendo smoke F004 + el
test de zona con persistencia. Diff aislado a frontend/e2e/progress. Arquitectura
limpia confirmada por greps deterministas. **APROBADO.**
