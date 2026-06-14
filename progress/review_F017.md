Veredicto: APROBADO

# Review F017 — API de listas de cotización (re-revisión)

> Re-revisión tras corrección del líder en `init.sh` (commit `37ecf36`,
> confirmado como HEAD). El RECHAZO anterior fue un **falso positivo del propio
> grep de arquitectura de la Fase 3**: matcheaba el decorador Ninja
> `@router.delete("/...")` por el substring `.delete(`. El fix distingue el
> `.delete()` del ORM (parens vacíos) y filtra las líneas de decoradores HTTP.
> El código de F017 NO cambió: se re-verificó todo desde cero, ejecutando los
> comandos uno mismo.

## Resumen de evidencia ejecutada

- `./init.sh` (modo full, sin `--e2e`): **VERDE — 31 ok, 0 fallos, 4 pendientes**
  (los pendientes son Fase 0/2 de entorno MVP: jq y docker ausentes — no fallos).
- Fase 3 → `✔ arquitectura: routers (api.py) sin llamadas al ORM`.
- Fase 5 → `✔ tipos TS sincronizados con backend/openapi.json` (sin drift).
- `uv run pytest apps/lists -q` → 28 passed (17 en `test_api.py` de F017 + 11 de
  `test_models.py` de F009). Suite backend completa → 75 passed, sin regresiones.

## Criterios de aceptación (specs/F017-api-listas.md) — uno por uno

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | Flujo completo: crear lista, agregar 2 items (snapshot), editar cantidad, quitar item (204), detalle con subtotal/total, borrar lista (204) | CUMPLE | `test_flujo_completo_crear_items_editar_quitar_detalle_borrar` — 201 al crear; ítem1 `captured_price=198.50`, `line_total=1985.00`; ítem2 `191.00`/`382.00`; PATCH cantidad 10→5 recalcula `line_total=992.50`; detalle `subtotal/total=1374.50`; DELETE item → 204; subtotal pasa a `992.50`; DELETE lista → 204; GET posterior → `[]` y 404 |
| 2 | Snapshot inmutable: nueva PriceObservation tras agregar NO cambia `captured_price` | CUMPLE | `test_snapshot_inmutable_ante_nueva_observacion` — tras crear obs. de `999.99`, el ítem sigue en `198.50` y `subtotal=198.50`. En `services._serializar_item` el precio sale de las columnas `item.captured_price/captured_at` (snapshot), nunca del precio en vivo; el test fallaría si se releyera el catálogo |
| 3 | Scoping: sesión B no ve/modifica lista de A → 404 | CUMPLE | `test_scoping_sesion_b_no_ve_lista_de_a` (B obtiene `[]`), `..._no_accede_detalle_de_a` (404), `..._no_modifica_lista_de_a` (PATCH/DELETE 404; A intacta), `..._no_modifica_item_de_a` (PATCH/DELETE ítem 404). `services._lista_de_sesion` filtra por `session_key` y no distingue ajena de inexistente |
| 4 | Falta `X-Session-Key` donde se requiere → 400 | CUMPLE | `test_sin_header_session_key_400_en_get/_en_post/_en_items` (3 tests, todos 400). `api._require_session_key` lanza `HttpError(400)` |
| 5 | quantity 0/negativa → 422 | CUMPLE | `test_quantity_cero_es_422`, `test_quantity_negativa_es_422`, `test_patch_item_quantity_invalida_es_422`. `schemas` usa `Field(ge=1)` |
| 6 | Sin observación → 422 "sin precio para snapshot" | CUMPLE | `test_agregar_item_sin_observacion_es_422`; SKU inexistente → `test_agregar_item_sku_inexistente_es_404`; lista inexistente → `test_detalle_lista_inexistente_es_404` |
| 7 | Router sin ORM, lógica en services, `response=` explícito | CUMPLE | grep `\.objects\|\.save(\|\.filter(\|\.create(\|\.delete(\s*)` en `apps/lists/api.py` filtrando decoradores → **VACIO**. Las 2 únicas apariciones de `.delete(` son decoradores `@router.delete(...)` (líneas 92 y 149). Todos los 8 endpoints declaran `response=` (incl. `{204: None}`). Fase 3 de init.sh: VERDE |
| 8 | `openapi.json` con rutas `/api/lists*`; sin drift (Fase 5) | CUMPLE | `openapi.json` líneas 190/282/428/487 → `/api/lists`, `/api/lists/{list_id}`, `/api/lists/{list_id}/items`, `/api/lists/{list_id}/items/{item_id}` (8 endpoints); 7 schemas `UserList*`. Fase 5: `✔ tipos TS sincronizados` (sin drift) |
| 9 | Frontend: `client.ts` con `apiPost/apiPatch/apiDelete` tipados; `fetch` solo en client.ts; cero `any` | CUMPLE | `client.ts` exporta `apiPost`/`apiPatch`/`apiDelete` con tipos derivados de `paths` (sin tipos a mano). grep `fetch(` fuera de client.ts → VACIO (único `fetch` en línea 132). grep `: any`/`as any` en `src` (excl. generado) → VACIO. Fase 4: tsc/lint/build/test:unit VERDE |
| 10 | `./init.sh` verde | CUMPLE | Ver output abajo: 0 fallos |

## Snapshot inmutable — verificación de columnas

`apps/lists/services.agregar_item` copia `captured_price=observacion.price` y
`captured_at=observacion.captured_at` a la fila `UserListItem` al crear. Ni
`actualizar_item` (solo toca `quantity`) ni `_serializar_item` releen
`PriceObservation`. La inmutabilidad es estructural, no incidental.

## Scoping de archivos (capas permitidas)

`git status --porcelain` confirma que solo se tocaron capas backend/frontend:

```
 M backend/apps/lists/services.py
 M backend/config/api.py
 M backend/openapi.json
 M frontend/src/lib/api/client.ts
 M frontend/src/lib/api/schema.d.ts
?? backend/apps/lists/api.py
?? backend/apps/lists/schemas.py
?? backend/apps/lists/tests/test_api.py
?? progress/impl_F017_backend.md
?? progress/impl_F017_frontend.md
?? progress/review_F017.md
```

Ningún archivo fuera de las capas permitidas (los `progress/*.md` son los
informes de impl/review, esperados). `schema.d.ts` es generado, no a mano.

## CHECKPOINTS.md — punto por punto

| Sección | Punto | Estado |
|---------|-------|--------|
| Global | `./init.sh` verde de punta a punta | CUMPLE (0 fallos) |
| Global | 1 sola feature in_progress | CUMPLE (Fase 1: `features in_progress: 1`) |
| Global | `progress/impl_<id>_<capa>.md` por capa con output real | CUMPLE (backend + frontend) |
| Global | cumple cada criterio de la spec | CUMPLE (tabla arriba) |
| Backend | `pytest` pasa, tests nuevos que fallarían sin la impl | CUMPLE (17 tests F017; asserts atados a snapshot/scoping/422/404) |
| Backend | `makemigrations --check` limpio | CUMPLE (Fase 3: `migraciones al día`; sin modelos nuevos, reusa F009) |
| Backend | `ruff check` limpio | CUMPLE (Fase 3) |
| Backend | lógica en `services.py`, no en routers | CUMPLE (todo el ORM en services; api.py solo delega) |
| Backend | api.py sin ORM | CUMPLE (grep VACIO; Fase 3 verde) |
| Backend | contrato regenerado si cambió | CUMPLE (`openapi.json` con rutas `/api/lists`) |
| Contrato | `schema.d.ts` regenerado, sin drift | CUMPLE (Fase 5 verde) |
| Contrato | frontend no declara tipos de API a mano | CUMPLE (client.ts deriva de `paths`) |
| Frontend | `tsc --noEmit` limpio | CUMPLE (Fase 4) |
| Frontend | `lint` limpio | CUMPLE (Fase 4) |
| Frontend | `build` pasa | CUMPLE (Fase 4) |
| Frontend | ningún `fetch(` fuera de client.ts; cero `any` | CUMPLE (greps VACIO; Fase 4 verde) |
| E2E | aplica solo a vertical slice | N/A (F017 no toca e2e por diseño de la spec) |
| Higiene | `feature_list.json` válido, ≤1 in_progress | CUMPLE (Fase 1) |
| Higiene | repo git inicializado | CUMPLE (Fase 0: `repositorio git inicializado`) |

## Output REAL de `./init.sh` (modo full)

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
  ✔ las 12 feature(s) 'done' tienen review APROBADO

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
  ◌ saltada (usa ./init.sh --e2e para correrla)

════════ Resumen ════════
  ✔ 31 ok   ✘ 0 fallos   ◌ 4 pendientes
  VERDE — el arnés está en estado consistente.
```

## Greps de arquitectura (deterministas, re-ejecutados por el reviewer)

```
# Backend — ORM en apps/lists/api.py (filtrando decoradores Ninja):
grep -nE "\.objects\b|\.save\(|\.filter\(|\.create\(|\.delete\(\s*\)" apps/lists/api.py \
  | grep -vE "@?(router|api)\.(get|post|put|patch|delete)\("
  → (VACIO)
# Únicas apariciones de .delete( en api.py son decoradores:
  92:@router.delete("/lists/{list_id}", response={204: None})
  149:@router.delete("/lists/{list_id}/items/{item_id}", response={204: None})

# Frontend — fetch fuera de client.ts:
grep -rnE "\bfetch\(" src --include=*.ts --include=*.tsx | grep -v "lib/api/client.ts"
  → (VACIO)   (único fetch: src/lib/api/client.ts:132)

# Frontend — ': any' / 'as any' en src:
grep -rnE ": any\b|as any" src --include=*.ts --include=*.tsx
  → (VACIO)
```

## Conclusión

Todos los criterios de la spec F017 y los checkpoints aplicables (Global +
Backend + Contrato + Frontend + Higiene) se cumplen, verificados ejecutando los
comandos. `./init.sh` termina VERDE con 0 fallos; la Fase 3 ya no produce el
falso positivo del decorador `@router.delete`. Sin observaciones de corrección.

**Veredicto: APROBADO.**
