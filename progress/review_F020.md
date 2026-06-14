# Veredicto: APROBADO

Revisión de **F020 — UI: búsqueda + resultados comparados por retailer**
(frontend + e2e) contra `specs/F020-ui-busqueda-resultados.md` y `CHECKPOINTS.md`.
Toda la evidencia fue **regenerada por el reviewer** (no se aceptó output pegado
por el implementer).

---

## Criterios de aceptación (spec F020)

| # | Criterio | Estado | Evidencia (comando / archivo) |
|---|----------|--------|-------------------------------|
| 1 | Con zona: buscar "varilla" muestra resultados; cada uno con precios por retailer (HD + Construrama), unidad, disponibilidad y frescura "actualizado hace X"; ordenable por precio (menor primero) | CUMPLE | `e2e/tests/search.spec.ts` (líneas 43-77: elige MTY, `sort=price`, busca varilla, exige ambos retailers con `retailer-price` count=2, frescura `actualizado hace`, y `prices[0] === min(prices)`). Render: `search/components/result-card.tsx` (nombre+`unit`, `is_available`→"disponible"/"sin disponibilidad", `freshnessLabel(captured_at)`, `sortPricesAsc`). E2E PASA en Fase 6. |
| 2 | Sin zona: invita a elegir y no rompe; retailer sin precio → indicado; estados cargando/error/vacío/datos presentes | CUMPLE | `search/components/search-panel.tsx`: rama `zoneId === null` → tarjeta "Primero selecciona una zona" sin buscar (`data-testid="search-needs-zone"`); estados `idle/loading/error/empty/ready` renderizados (líneas 121-178). `result-card.tsx` líneas 67-74: "sin precio en tu zona" (`retailer-no-price`). `use-search.ts`: máquina de estados idle/loading/ready/empty/error + reset a idle al perder zona. |
| 3 | Datos de `schema.d.ts` (cero `any`, cero tipos a mano); `fetch` solo en `client.ts`; test unit del helper "hace X" | CUMPLE | Greps deterministas VACÍOS (ver abajo). Tipos derivados: `search/types.ts` (`Awaited<ReturnType<typeof fetchSearch>>`), `search/api.ts` (`apiGetQuery("/api/search", …)` infiere del contrato), `client.ts` `apiGetQuery` deriva query de `paths[P]["get"].parameters.query`. `fetch` ÚNICO en `client.ts` (línea 164). Unit test: `search/relative-time.test.ts` (9 casos, PASA). |
| 4 | E2E `search.spec.ts` pasa (varilla en MTY, ambos retailers, orden por precio); `./init.sh --e2e` Fase 6 verde | CUMPLE | `pnpm exec playwright test --list` → 3 specs (search/smoke/zone). `./init.sh --e2e` Fase 6: `✔ suite Playwright`. Resumen VERDE 33 ok / 0 fallos. |
| 5 | `tsc`/`lint`/`build`/`test:unit` limpios; `./init.sh --e2e` verde | CUMPLE | Fase 4: `✔ tsc --noEmit`, `✔ lint`, `✔ build de producción`, `✔ tests unitarios (vitest)`. Vitest: 17 passed (3 archivos). |

---

## CHECKPOINTS.md — secciones aplicables

### Global
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `./init.sh` verde de punta a punta | CUMPLE | `./init.sh --e2e` → VERDE, 0 fallos (output completo abajo). |
| Exactamente 1 feature in_progress | CUMPLE | Fase 1: `✔ features in_progress: 1 (máximo 1)`. |
| `progress/impl_<id>_<capa>.md` con output real | CUMPLE | `progress/impl_F020_frontend.md` presente con verificaciones; el reviewer reprodujo cada una. |
| Cumple su spec criterio a criterio | CUMPLE | Tabla de criterios arriba (5/5). |

### Frontend
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `tsc --noEmit` limpio | CUMPLE | Fase 4 `✔ tsc --noEmit`. |
| `lint` limpio | CUMPLE | Fase 4 `✔ lint`. |
| `build` pasa | CUMPLE | Fase 4 `✔ build de producción`. |
| shadcn vía CLI en `src/components/ui/` | CUMPLE | Reutiliza `Card/Input/Button` ya instalados; el orden es `<select>` nativo (no componente a mano). |
| Todo fetch maneja carga y error | CUMPLE | `use-search.ts` estados loading/error; `search-panel.tsx` renderiza ambos; `client.ts` normaliza red/no-2xx a `ApiError`. |
| Ningún `fetch(` fuera de `client.ts`; cero `any` | CUMPLE | Greps VACÍOS (abajo) + Fase 4 `✔ arquitectura: fetch solo en src/lib/api/client.ts`. |

### Contrato (¿cambió la API?) — NO cambió
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `backend/openapi.json` sin tocar | CUMPLE | `git diff --stat HEAD -- backend/openapi.json` VACÍO; `git status --short backend/` VACÍO. F020 no toca backend. |
| `schema.d.ts` sin drift / sin tipos a mano | CUMPLE | `git status --short frontend/src/lib/api/schema.d.ts` VACÍO; Fase 5 `✔ tipos TS sincronizados con backend/openapi.json`. |

### E2E
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| Smoke pasa con `--e2e` | CUMPLE | Fase 6 `✔ suite Playwright` incluye `smoke.spec.ts`. |
| Feature tiene ≥1 E2E del flujo feliz | CUMPLE | `e2e/tests/search.spec.ts` (flujo feliz B1). |

### Higiene del arnés
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `feature_list.json` válido, ≤1 in_progress | CUMPLE | Fase 1 `✔ feature_list.json es JSON válido`, `✔ in_progress: 1`. |
| Repo git inicializado | CUMPLE | Fase 0 `✔ repositorio git inicializado`; `git rev-parse` → true. |
| Features `done` con review APROBADO | CUMPLE | Fase 1 `✔ las 15 feature(s) 'done' tienen review APROBADO`. |

---

## Verificaciones deterministas del reviewer

### Greps de arquitectura (ambos deben dar VACÍO)
```
$ grep -rn "fetch(" frontend/src --include=*.ts --include=*.tsx | grep -v "lib/api/client.ts"
(vacío — exit 1)

$ grep -rnE ": any\b|as any" frontend/src
(vacío — exit 1)
```

### Alcance del diff (solo frontend/ + e2e/ + progress/)
```
$ git status --short
 M frontend/src/app/page.tsx
 M frontend/src/features/zones/hooks/use-selected-zone.ts
 M frontend/src/lib/api/client.ts
?? e2e/tests/search.spec.ts
?? frontend/src/features/search/
?? progress/impl_F020_frontend.md

$ git status --short backend/        → VACÍO  (backend NO tocado)
$ git diff --stat HEAD -- backend/openapi.json → VACÍO  (contrato NO tocado)
$ git status --short frontend/src/lib/api/schema.d.ts → VACÍO  (sin drift)
```
Nada fuera de la capa permitida (frontend + e2e). El cambio en
`use-selected-zone.ts` (sync in-tab) es el fix declarado y queda dentro de
frontend.

### Tests que sí prueban algo (regla del "git stash mental")
- `search/relative-time.test.ts` (9 casos): fija `NOW` y verifica minutos/horas/
  días singular/plural, futuro="hace un momento", null/inválido→null, `freshnessLabel`.
  Fallaría si el helper devolviera otra cosa → prueba real, no tautológica.
- `e2e/tests/search.spec.ts`: exige `retailer-price` count=2 (ambos retailers con
  precio) y `prices[0] === Math.min(prices)` (orden por precio). Fallaría sin la
  UI/orden implementados.
- F019 `use-selected-zone.test.ts`: **5 tests siguen verdes** tras el fix in-tab
  (persistencia, recuperación, JSON corrupto, clearZone) → sin regresión.

### Tipado del contrato (cero tipos a mano)
- `apiGetQuery("/api/search", { q, zone_id, sort })` deriva `query` de
  `schema.d.ts` → `paths["/api/search"]["get"].parameters.query` = `{ q: string;
  zone_id: string; sort?: string }` (verificado en schema, op `apps_catalog_api_buscar`).
- `SearchResult`/`RetailerPrice` se infieren de `fetchSearch` (→ `SearchResultOut[]`),
  no se declaran a mano. `SearchSort = "price" | "name"` es un narrowing de UI para
  el `<select>`, no un tipo de respuesta de la API (aceptable).
- `apiGetQuery` mantiene `fetch` exclusivamente dentro de `client.ts` (verificado:
  el único `fetch(` del repo está en `client.ts:164`).

---

## Output REAL de `./init.sh --e2e` (corrida del reviewer)

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
  ✔ las 15 feature(s) 'done' tienen review APROBADO

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

### Fase 6 — specs ejercidas (`playwright test --list`)
```
[chromium] › search.spec.ts:19 › buscar varilla en Monterrey Metro: ambos retailers y orden por precio
[chromium] › smoke.spec.ts:9  › la home carga y el indicador de salud muestra ok
[chromium] › zone.spec.ts:11  › elegir zona y que persista tras recargar
Total: 3 tests in 3 files
```
Fase 6 verde = smoke (F004) + zone (F019) + search (F020), los 3 pasan.

### Vitest (corrida del reviewer)
```
 ✓ src/features/search/relative-time.test.ts (9 tests)
 ✓ src/features/zones/hooks/use-selected-zone.test.ts (5 tests)
 ✓ src/app/page.test.tsx (3 tests)
 Test Files  3 passed (3)
      Tests  17 passed (17)
```

Los 3 pendientes (`jq`, `docker`, Fase 2) son opcionales/MVP-diferidos, no fallos,
conforme a la convención del arnés.

---

## Conclusión

Los 5 criterios de F020, las secciones Frontend + Contrato + E2E + Higiene de
`CHECKPOINTS.md`, los greps de arquitectura, el alcance del diff (sin tocar
`backend/` ni `backend/openapi.json` ni `schema.d.ts`), la no-regresión de los 5
tests de F019 y `./init.sh --e2e` VERDE con Fase 6 verde quedan todos verificados
por el reviewer. **APROBADO.**
