Veredicto: APROBADO

# Review F021 — UI: detalle de producto + historial de precio

Capas: **frontend + e2e**. Spec: `specs/F021-ui-detalle-producto.md`.
Revisión ejecutada por el reviewer (comandos propios, no resúmenes del implementer).
Fecha de corrida: 2026-06-14.

## Resumen del veredicto

Todos los criterios de la spec CUMPLEN. `./init.sh --e2e` termina **VERDE**
(33 ok · 0 fallos · 3 pendientes), con **Fase 6 verde** (smoke + zone + search +
detail, los 4 specs pasan) y **Fase 5 sin drift** (F021 no añade endpoints;
`backend/openapi.json` y `schema.d.ts` intactos). Los 3 pendientes son esperados
del entorno MVP (jq y docker opcionales; Fase 2 Postgres/Redis diferida) — no son
fallos. `git status` confirma que F021 solo toca `frontend/`, `e2e/` y `progress/`;
cero cambios en `backend/`.

## Criterios de aceptación de la spec → estado → evidencia

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | Detalle muestra `specs`, precios actuales por retailer (frescura + enlace ficha con rel noopener) e historial ordenado reciente→antiguo | CUMPLE | `product-specs.tsx` (specs aplanados vía `specEntries`); `product-prices.tsx` líneas 35-43 (`<a target="_blank" rel="noopener noreferrer">`) + líneas 50-51 frescura vía `freshnessLabel`; `product-history.tsx` `sortRecentFirst` (descendente por `captured_at`). E2E `detail.spec.ts:55-72` verifica 2 precios, frescura "actualizado hace", `target=_blank`, `rel=/noopener/`, ≥1 fila de historial. |
| 2 | Se navega a `/products/{id}` desde un resultado de búsqueda (F020 con next/link) | CUMPLE | `result-card.tsx:10,31-37` (`<Link href={"/products/${product.id}"} data-testid="search-result-link">`). E2E `detail.spec.ts:41,44` click en `search-result-link` → `toHaveURL(/\/products\/[^/]+$/)`. |
| 3 | Estados cargando/error/datos; 404 → mensaje amable; sin zona → invita a elegir | CUMPLE | `use-product-detail.ts:20-25` máquina de estados `no-zone\|loading\|ready\|not-found\|error`; 404 mapeado vía `ApiError.status===404` (líneas 54-56). `product-detail.tsx` renderiza los 5 estados con `data-testid` (`product-needs-zone`, `product-loading`, `product-not-found`, `product-error`, `product-detail`). |
| 4 | Datos de `schema.d.ts` (cero `any`, cero tipos a mano); `fetch` solo en `client.ts` (helper `apiGetPath`) | CUMPLE | grep `: any\|as any` en `frontend/src` → VACÍO (EXIT=1). grep `fetch(` fuera de `client.ts` → VACÍO (EXIT=1); único `fetch(` en `client.ts:207`. `apiGetPath` (`client.ts:273-291`) deriva path/query/respuesta de `paths` del contrato. `types.ts` infiere todo de `Awaited<ReturnType<typeof fetchProductDetail>>`. Único import de `./schema` está en `client.ts:19`. Contrato `ProductDetailOut`/`CanonicalProductDetailOut`/`PriceByRetailerOut`/`PriceHistoryPointOut` existe en `schema.d.ts:307-404`. |
| 5 | E2E `detail.spec.ts` pasa (búsqueda → detalle → precios por retailer + historial); Fase 6 verde | CUMPLE | `detail.spec.ts:13` PASA (7.1s); golpea `GET /api/products/{id}?zone_id=` 200. Fase 6 verde en `./init.sh --e2e`. |
| 6 | `tsc`/`lint`/`build`/`test:unit` limpios; `./init.sh` y `./init.sh --e2e` verdes | CUMPLE | Fase 4 de `init.sh`: tsc, lint, vitest, build, arquitectura — todos ✔. Resumen VERDE. |

## CHECKPOINTS.md → estado → evidencia

### Global
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `./init.sh` verde de punta a punta | CUMPLE | `--e2e`: 33 ok · 0 fallos · VERDE. |
| Solo la feature actual cambió de estado | CUMPLE | `feature_list.json`: F021 único `in_progress` (count=1); F022/F010-F012 siguen `pending`. |
| Existe `progress/impl_<id>_<capa>.md` con output real | CUMPLE | `progress/impl_F021_frontend.md` (frontend+e2e) con outputs. |
| Cumple cada criterio de la spec | CUMPLE | Tabla anterior. |

### Frontend
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `tsc --noEmit` limpio | CUMPLE | Fase 4 ✔. |
| `lint` limpio | CUMPLE | Fase 4 ✔. |
| `build` pasa | CUMPLE | Fase 4 ✔ (ruta `/products/[id]` 2.53 kB dinámica). |
| shadcn vía CLI en `src/components/ui/` | CUMPLE | No se añadieron componentes; reusa `card.tsx`/`button.tsx` ya instalados. |
| Todo fetch maneja carga y error | CUMPLE | `use-product-detail.ts` cubre loading/error/not-found/no-zone. |
| Ningún `fetch(` fuera de `client.ts`; cero `any` | CUMPLE | Greps deterministas VACÍOS (ver criterio 4). Fase 4 arquitectura ✔. |

### Contrato (¿cambió la API?)
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| Sin drift; no se regeneró por innecesario | CUMPLE | F021 no añade endpoints. `git status` de `backend/openapi.json` y `schema.d.ts` VACÍO (intactos). Fase 5 ✔ "tipos TS sincronizados". |

### E2E
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| Smoke pasa con `--e2e` | CUMPLE | `smoke.spec.ts` ✓ (3.3s). |
| Feature tiene test E2E propio del flujo feliz | CUMPLE | `e2e/tests/detail.spec.ts` ✓ (7.1s), búsqueda→detalle→precios+historial. |

### Higiene del arnés
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `feature_list.json` JSON válido con ≤1 `in_progress` | CUMPLE | Fase 1 ✔ "features in_progress: 1 (máximo 1)" + JSON válido. |
| `progress/current.md` refleja la sesión | CUMPLE | Fase 1 ✔ existe. |
| Toda `done` tiene review APROBADO | CUMPLE | Fase 1 ✔ "las 16 feature(s) 'done' tienen review APROBADO". |
| Repo git inicializado | CUMPLE | Fase 0 ✔ "repositorio git inicializado"; `git rev-parse` EXIT=0. |

## Verificaciones deterministas (greps de arquitectura) — corrida del reviewer

```
$ grep -rn "fetch(" frontend/src --include=*.ts --include=*.tsx | grep -v "lib/api/client.ts"
(VACÍO) EXIT=1  → OK

$ grep -rn ": any\b\|as any" frontend/src
(VACÍO) EXIT=1  → OK

$ grep -rnE "\bfetch\(" frontend/src
frontend/src/lib/api/client.ts:207:    response = await fetch(buildUrl(path), {
  → único fetch, en el cliente

$ grep -rn "api/schema|\"./schema\"" frontend/src
frontend/src/lib/api/client.ts:19: import type { paths } from "./schema";
  → único import del contrato, en el cliente (resto deriva vía types.ts)
```

Regla "git stash mental": `detail.spec.ts` falla sin la implementación — sus
selectores (`product-detail`, `product-retailer-price` x2, `product-retailer-link`,
`product-history-row`, `search-result-link`) solo existen en los componentes nuevos
y en el `<Link>` añadido a `result-card.tsx`. El assert `prices.count()===2` y los
atributos `target/rel` del enlace verifican comportamiento real, no humo.

## Alcance del diff (git status / git diff)

```
 M frontend/src/features/search/components/result-card.tsx
 M frontend/src/lib/api/client.ts
?? e2e/tests/detail.spec.ts
?? frontend/src/app/products/
?? frontend/src/features/products/
?? progress/impl_F021_frontend.md
```
Solo `frontend/`, `e2e/` y `progress/`. Cero archivos bajo `backend/`
(`git status --porcelain backend/` VACÍO; sin untracked). Capas permitidas.

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
  ✔ las 16 feature(s) 'done' tienen review APROBADO

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

### Detalle de la suite Playwright (corrida directa del reviewer)

```
Running 4 tests using 4 workers
  ✓  4 [chromium] › tests\smoke.spec.ts:9:5 › la home carga y el indicador de salud muestra ok (3.3s)
  ✓  3 [chromium] › tests\search.spec.ts:19:5 › buscar varilla en Monterrey Metro: ambos retailers y orden por precio (4.1s)
  ✓  2 [chromium] › tests\zone.spec.ts:11:5 › elegir zona y que persista tras recargar (5.9s)
  ✓  1 [chromium] › tests\detail.spec.ts:13:5 › desde la búsqueda al detalle: precios por retailer e historial (7.1s)
       [WebServer] "GET /api/products/160623a6-...?zone_id=615b0e10-... HTTP/1.1" 200 1746
  4 passed (25.6s)
E2E_EXIT=0
```

Los tests unitarios previos siguen verdes (Fase 4 ✔ vitest: 17 tests en 3 archivos,
incluyendo `relative-time.test.ts`, `use-selected-zone.test.ts`, `page.test.tsx`).
