# Veredicto: APROBADO

Feature **F014 — API de zonas** (Django Ninja). Revisor: verificación reejecutada
de punta a punta. Toca backend + frontend (no e2e). `./init.sh` (modo full) VERDE,
Fase 5 (contrato) VERDE sin drift.

## Criterios de aceptación (specs/F014-api-zonas.md)

| # | Criterio | Estado | Evidencia (comando / archivo) |
|---|----------|--------|-------------------------------|
| 1 | `GET /api/zones` → zonas activas como `ZoneOut[]` ordenadas por `name` (≥1 con seed: "Monterrey Metro") | CUMPLE | `services.listar_zonas_activas()` → `['Monterrey Metro']` (corrida live en test DB); test `test_listar_zonas_devuelve_solo_activas_ordenadas` asierta orden `['Guadalajara Metro','Monterrey Metro']` y filtro de inactivas; `manage.py seed` + `Zone.objects.filter(is_active=True)` → `['Monterrey Metro']`. Router `api.py:16` con `response=list[ZoneOut]` |
| 2 | `POST /api/zones/resolve` Monterrey (~25.68,-100.31) → "Monterrey Metro"; sin cobertura → 404 `{detail}` | CUMPLE | live: `resolver_zona(25.68,-100.31)` → `Monterrey Metro`; sin zonas → `None`; test `test_resolve_monterrey_devuelve_zona_mas_cercana` (200, descarta Guadalajara) y `test_resolve_sin_zonas_con_centroide_responde_404` asierta `{"detail":"aún sin cobertura"}` |
| 3 | Router `apps/geo/api.py` SIN ORM (lógica/distancia en `services.py`); `response=` explícito | CUMPLE | `grep -rnE "\.objects\|\.save\(\|\.filter\(\|\.create\(\|\.delete\(" backend/apps/*/api.py backend/config/api.py` → VACÍO (exit 1). Haversine + ORM viven en `services.py`. Ambos endpoints con `response=` (`api.py:16,22`). Fase 3 de init.sh: "arquitectura: routers sin ORM" ✔ |
| 4 | Tests de ambos endpoints + el 404; fallarían sin la implementación | CUMPLE | `test_api.py`: 4 tests (lista/orden/filtro, resolve Monterrey, 404, service ignora inactivas). Importan `apps.geo.api.router`, `apps.geo.services`, `apps.geo.models.Zone` reales → sin la implementación no importan/no resuelven. `uv run pytest apps/geo` → 10 passed |
| 5 | `backend/openapi.json` contiene `/api/zones`, `/api/zones/resolve`, `ZoneOut`, `ResolveIn` | CUMPLE | `grep -nE` en `openapi.json`: `/api/zones` (L32), `/api/zones/resolve` (L59), `ZoneOut` (L109), `ResolveIn` (L138). Shape `ZoneOut={id,name,slug,state}` (L109-137) |
| 6 | Contrato sin drift: `schema.d.ts` incluye `ZoneOut` y coincide con openapi.json (Fase 5 verde) | CUMPLE | Fase 5 de init.sh ✔ "tipos TS sincronizados". Re-corrida `pnpm gen:api`: sha256 antes=después `bbc335...d14992` (idéntico → no drift). `schema.d.ts` L83-92 `ZoneOut` = openapi exacto |
| 7 | Frontend: `fetch` solo en `client.ts`, cero `any`; tsc/lint/build/test:unit limpios | CUMPLE | `grep -rn "fetch(" frontend/src \| grep -v client.ts` → VACÍO; `grep -rn ": any\b\|as any" frontend/src` → VACÍO. Fase 4 init.sh: tsc ✔, lint ✔, vitest ✔, build ✔. `features/zones/api.ts` usa `apiGet` tipado, sin tipos a mano |
| 8 | `./init.sh` verde; ruff/pytest/tsc/lint/build limpios | CUMPLE | Ver salida abajo: 31 ok / 0 fallos. ruff ✔, pytest ✔ (44 passed full), tsc/lint/build ✔ |

## CHECKPOINTS.md

### Global
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| init.sh verde punta a punta | CUMPLE | 0 fallos (salida abajo) |
| Exactamente la feature actual in_progress | CUMPLE | `feature_list.json` válido, `in_progress: 1` (F014); Fase 1 ✔ |
| `progress/impl_<id>_<capa>.md` por capa con output real | CUMPLE | `impl_F014_backend.md` + `impl_F014_frontend.md` con outputs reales (verificados contra mi corrida) |
| Cumple cada criterio de la spec | CUMPLE | Tabla anterior, todos CUMPLE |

### Backend
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| pytest pasa, tests nuevos que fallarían sin impl | CUMPLE | 44 passed; tests geo importan router/services/models reales |
| makemigrations --check limpio | CUMPLE | Fase 3 ✔ "migraciones al día"; F014 no toca modelos (Zone es de F006) |
| ruff check limpio | CUMPLE | Fase 3 ✔ |
| Lógica en services.py, no en routers | CUMPLE | `services.py` (haversine, filtros, mapeo); `api.py` solo delega |
| api.py sin ORM / regla de capas | CUMPLE | grep VACÍO; import-linter "1 kept, 0 broken" (impl report); Fase 3 ✔ |
| corsheaders desde env | N/A | F014 no toca CORS (config de F001/F002); fuera de alcance |
| Si cambió contrato: openapi.json regenerado | CUMPLE | `openapi.json` regenerado con paths/schemas nuevos; en git diff |

### Contrato
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| schema.d.ts regenerado con gen:api, sin drift | CUMPLE | sha256 idéntico tras re-correr gen:api; Fase 5 ✔ |
| Frontend NO declara tipos de API a mano | CUMPLE | `features/zones/api.ts` infiere de `apiGet`; grep `any` VACÍO |

### Frontend
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| tsc --noEmit limpio | CUMPLE | Fase 4 ✔ |
| lint limpio | CUMPLE | Fase 4 ✔ |
| build pasa | CUMPLE | Fase 4 ✔ (build de producción) |
| shadcn por CLI en components/ui | N/A | F014 no añade componentes UI (sin UI por diseño; UI es F019) |
| Todo fetch maneja carga/error | N/A / CUMPLE | Sin UI en F014; el cliente `client.ts` ya maneja error de red y no-2xx vía `ApiError` |
| Ningún fetch fuera de client.ts; cero any | CUMPLE | greps VACÍOS; Fase 4 ✔ "fetch solo en client.ts" |

### Higiene del arnés
| Punto | Estado | Evidencia |
|-------|--------|-----------|
| feature_list.json JSON válido, ≤1 in_progress | CUMPLE | `python -c json.load` válido; in_progress=1 |
| Repo git inicializado | CUMPLE | `git rev-parse --is-inside-work-tree` → true; Fase 0 ✔ |

## Diff revisado (solo capas permitidas)

`git status --short`:
```
 M backend/config/api.py
 M backend/openapi.json
 M frontend/src/lib/api/schema.d.ts
?? backend/apps/geo/api.py
?? backend/apps/geo/schemas.py
?? backend/apps/geo/services.py
?? backend/apps/geo/tests/test_api.py
?? frontend/src/features/zones/
?? progress/impl_F014_backend.md
?? progress/impl_F014_frontend.md
```
Sin archivos fuera de la capa permitida (backend/apps/geo, config/api.py, openapi.json,
frontend schema.d.ts, features/zones, progress/).

## Greps de arquitectura (deterministas)
```
grep -rnE "\.objects|\.save\(|\.filter\(|\.create\(|\.delete\(" backend/apps/*/api.py backend/config/api.py  → VACÍO (exit 1)
grep -rn "fetch(" frontend/src --include=*.ts --include=*.tsx | grep -v "lib/api/client.ts"                  → VACÍO (exit 1)
grep -rn ": any\b|as any" frontend/src                                                                        → VACÍO (exit 1)
```

## Regla del "git stash mental"
Los tests importan los símbolos reales (`apps.geo.api.router`, `apps.geo.services`,
`apps.geo.models.Zone`) y asiertan shape exacto de `ZoneOut`, orden por nombre,
descarte de inactivas, 200 con la zona más cercana y 404 `{"detail":"aún sin cobertura"}`.
Sin la implementación no compilarían/importarían ni pasarían. Comprobación cruzada
live: `listar_zonas_activas()` → `['Monterrey Metro']`; `resolver_zona(25.68,-100.31)`
→ `Monterrey Metro`; sin zonas → `None` (404).

## Nota (no bloqueante)
El criterio menciona "coords lejanas → 404". La definición canónica de la spec
(§Contrato y líneas 20-21) es: 404 **cuando no hay zonas activas con centroide**
(sin cobertura), no un radio máximo. La implementación devuelve la zona activa más
cercana para cualquier coordenada con cobertura y 404 solo sin cobertura — consistente
con el cuerpo de la spec. El test del 404 ejercita exactamente ese caso. Sin acción.

## Output real de `./init.sh` (modo full)
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
  ✔ las 9 feature(s) 'done' tienen review APROBADO

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

Fase 5 (contrato) **VERDE sin drift** confirmada. Los 4 pendientes son esperados en
MVP (jq/docker ausentes, Fase 2 infra diferida, Fase 6 E2E saltada en modo full).
