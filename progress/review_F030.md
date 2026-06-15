# Review F030 — Fix hydration mismatch (hooks de localStorage SSR-safe)

**Veredicto: APROBADO**

Capas: frontend + e2e. Spec: `specs/F030-fix-hydration.md`.
Revisor: re-ejecuté `./init.sh --e2e` y todas las verificaciones deterministas
yo mismo (no acepté el output del implementer como evidencia).

---

## Criterios de la spec / CHECKPOINTS → estado → evidencia

| # | Criterio | Estado | Evidencia (comando / archivo) |
|---|----------|--------|-------------------------------|
| 1 | `useSelectedZone` SSR-safe: primer render usa default (`null`), lee `localStorage` tras montar vía `useSyncExternalStore` con `getServerSnapshot` que devuelve el default | **CUMPLE** | `frontend/src/features/zones/hooks/use-selected-zone.ts:95-97` (`getServerSnapshot()` retorna `null`); `:134-138` (`useSyncExternalStore(subscribe, getClientSnapshot, getServerSnapshot)`); `getClientSnapshot` lee `localStorage` solo tras montar/suscribir (`:84-89`). `git diff` confirma el reemplazo de `useState(readStoredZone)`+`useEffect` por el patrón canónico. |
| 2 | `useQuote` SSR-safe: server snapshot = `idle` (referencia estable) | **CUMPLE** | `frontend/src/features/lists/hooks/use-quote.ts:57` (`SERVER_SNAPSHOT = { status: "idle" }`); `:75-77` (`getQuoteServerSnapshot` retorna esa referencia estable); `:182-186` (`useSyncExternalStore`). |
| 3 | Componentes no ramifican markup distinto SSR vs primer render cliente | **CUMPLE** | `frontend/src/features/search/components/search-panel.tsx:42` ramifica sobre `zoneId === null`; con el hook SSR-safe `selectedZone` es `null` en SSR y primer paint → ambos renderizan la rama "Elige tu zona". |
| 4 | Guardia E2E: pre-setea zona en `localStorage` (`addInitScript`), captura `console`/`pageerror`, navega a `/`, FALLA si hay `/hydration|did not match/i` | **CUMPLE** | `e2e/tests/hydration.spec.ts:31-39` (`addInitScript` setea la zona antes del bundle); `:43-52` (listeners `console`+`pageerror` con `HYDRATION_PATTERN`); `:54` (`goto("/")`); `:73-76` (`expect(hydrationErrors).toHaveLength(0)`). |
| 5 | El test tiene dientes ("git stash mental") | **CUMPLE** | Doble aserción load-bearing: `:64-67` exige que el panel muestre "Monterrey Metro" tras hidratar (prueba que SÍ se lee `localStorage` post-mount, no que se quedó en default); `:73-76` falla ante cualquier mensaje de hidratación. Sin el fix, el lazy-initializer leía `localStorage` en el primer render cliente vs default en SSR → React emite "Hydration failed" en consola → el gate lo atrapa. |
| 6 | Persistencia de zona sigue (F019: elegir → recargar → persiste) | **CUMPLE** | `e2e/tests/zone.spec.ts:36-39` (reload + `selected-zone` contiene "Monterrey Metro"); pasa en la corrida. Persistencia preservada: `use-selected-zone.ts:140-158` siguen escribiendo `localStorage` en `selectZone`/`clearZone`. Unit: `use-selected-zone.test.ts:35-46` "recupera la zona persistida en montaje nuevo". |
| 7 | Persistencia de cotización sigue (F022) | **CUMPLE** | `e2e/tests/quote.spec.ts:23` (agregar → snapshot+total → editar → quitar) pasa; `use-quote.ts:96-105,130-133` conservan caché del `defaultListId` en `localStorage`. |
| 8 | `pnpm exec tsc --noEmit` limpio | **CUMPLE** | `./init.sh --e2e` Fase 4 `✔ tsc --noEmit`. |
| 9 | `pnpm lint` limpio | **CUMPLE** | Fase 4 `✔ lint`. |
| 10 | `pnpm build` pasa | **CUMPLE** | Fase 4 `✔ build de producción`. |
| 11 | `pnpm test:unit` limpio | **CUMPLE** | Fase 4 `✔ tests unitarios (vitest)`. |
| 12 | `fetch` solo en `client.ts` | **CUMPLE** | `grep -rnE "\bfetch\(" frontend/src` (`.ts` + `.tsx`) → solo `frontend/src/lib/api/client.ts:233`. Fase 4 `✔ arquitectura: fetch solo en src/lib/api/client.ts`. |
| 13 | Cero `any` en `frontend/src` | **CUMPLE** | `grep -rn ": any\b\|as any" frontend/src` → VACÍO (No matches found). |
| 14 | `./init.sh --e2e` VERDE; nuevo spec de hidratación + previos pasan | **CUMPLE** | Resumen: `✔ 33 ok ✘ 0 fallos ◌ 3 pendientes — VERDE`. `playwright test --list`: 6 tests incl. `hydration.spec.ts`. |
| 15 | Diff solo en `frontend/`, `e2e/` y `progress/` (no backend/contrato) | **CUMPLE** | `git status --porcelain`: `M frontend/src/features/lists/hooks/use-quote.ts`, `M frontend/src/features/zones/hooks/use-selected-zone.ts`, `?? e2e/tests/hydration.spec.ts`, `?? progress/impl_F030_frontend.md`. Cero archivos en `backend/`. |
| 16 | Fase 5 (contrato) sin cambios | **CUMPLE** | `backend/openapi.json` y `schema.d.ts` intactos (no aparecen en `git status`); Fase 5 `✔ tipos TS sincronizados`. |
| 17 | `feature_list.json` JSON válido con ≤ 1 `in_progress` | **CUMPLE** | Fase 1 `✔ feature_list.json es JSON válido (array)` y `✔ features in_progress: 1 (máximo 1)`. F030 es la única `in_progress`. |
| 18 | Repo git inicializado (Fase 0) | **CUMPLE** | Fase 0 `✔ repositorio git inicializado`. (La cabecera de entorno decía "no git", pero `git rev-parse --is-inside-work-tree` → `true`; el diff del revisor es ejecutable.) |

**Backend (CHECKPOINTS):** N/A — F030 no toca backend. La Fase 3 corrió verde de
todos modos (`✔ pytest`, `✔ ruff`, `✔ arquitectura: routers sin ORM`).

---

## Verificaciones deterministas (corridas por el revisor)

```
$ grep -rnE "\bfetch\(" frontend/src (--include=*.ts --include=*.tsx)
frontend/src/lib/api/client.ts:233:    response = await fetch(buildUrl(path), {
  → fetch SOLO en client.ts. OK.

$ grep -rn ": any\b|as any" frontend/src
  → (vacío) No matches found. OK.

$ git status --porcelain=v1
 M frontend/src/features/lists/hooks/use-quote.ts
 M frontend/src/features/zones/hooks/use-selected-zone.ts
?? e2e/tests/hydration.spec.ts
?? progress/impl_F030_frontend.md
  → Diff acotado a frontend/ + e2e/ + progress/. Sin tocar backend/contrato. OK.

$ git rev-parse --is-inside-work-tree
true

$ cd e2e && pnpm exec playwright test --list
  detail.spec.ts, hydration.spec.ts, quote.spec.ts, search.spec.ts,
  smoke.spec.ts, zone.spec.ts  → Total: 6 tests in 6 files
```

---

## Output real de `./init.sh --e2e` (corrida del revisor)

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
  ✔ las 26 feature(s) 'done' tienen review APROBADO

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

Los 3 pendientes (`◌`) son `jq`, `docker` e infra Postgres/Redis: esperados en el
entorno MVP (SQLite / sin-Docker / sin-jq). No son fallos.

---

## Conclusión

Los 18 puntos aplicables CUMPLEN. Los hooks `useSelectedZone` y `useQuote` usan
`useSyncExternalStore` con `getServerSnapshot` que devuelve el default, eliminando
el desajuste de hidratación de raíz sin perder persistencia ni sync cross-tab/in-tab.
La guardia E2E tiene dientes reales (doble aserción: refleja la zona tras hidratar +
gate de cero errores de hidratación). El arnés corre VERDE de punta a punta con `--e2e`.
El diff está acotado a las capas permitidas (frontend + e2e + progress).

**APROBADO.**
