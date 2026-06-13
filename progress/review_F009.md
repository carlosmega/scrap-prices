Veredicto: APROBADO

# Review F009 — Modelo de listas de cotización (anónimo / sesión)

Capa: backend (única). Revisor: reviewer del arnés. Fecha: 2026-06-13.
Verificación re-ejecutada por el revisor (no se aceptó el output del implementer
como evidencia): `./init.sh` modo full (sin `--e2e`), fresh migrate en DB temporal,
greps deterministas de arquitectura y `git status`/`git diff`.

## Criterios de aceptación de `specs/F009-modelo-listas-cotizacion.md`

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | `UserList` y `UserListItem` en `models.py` heredando la base abstracta | CUMPLE | `backend/apps/lists/models.py:24` y `:59` — ambas heredan `TimeStampedUUIDModel` (importado de `apps.common.models`, `backend/apps/common/models.py:13`). |
| 2 | MVP anónimo/sesión: `UserList` NO exige `user_fk` (lista creable sin usuario) | CUMPLE | Modelo no declara `user`/`user_fk`. Test `test_crear_lista_anonima_con_session_key_y_zona` (test_models.py:64) crea `UserList.objects.create(session_key=..., zone=...)` sin user y `test_lista_zona_nula_permitida` (:245) crea con solo `session_key`; ambos verdes. Assert explícito `"user"`/`"user_fk"` not in fields (:72-74). |
| 3 | `session_key` indexado | CUMPLE | `models.py:37` `CharField(... db_index=True)`; migración `0001_initial.py:25` `db_index=True`; test `test_session_key_indexado` (:82). |
| 4 | `zone` FK→Zone null/blank, related_name `user_lists` | CUMPLE | `models.py:39-45` (`on_delete=SET_NULL, null, blank, related_name="user_lists"`); migración `0001_initial.py:28` apunta a `geo.zone`. (Zone vive en `apps/geo`, ref. correcta de F006.) |
| 5 | `status` choices, default `open` | CUMPLE | `models.py:31-50` `Status.OPEN` default; migración `:27`. |
| 6 | Item: `user_list` FK related_name `items`; `retailer_product` FK→RetailerProduct related_name `list_items` | CUMPLE | `models.py:68-77`; migración `:45-46` (`catalog.retailerproduct`, `lists.userlist`). RetailerProduct vive en `apps/catalog` (ref. correcta de F007). Test `:107-110` valida ambos related_name. |
| 7 | `quantity` PositiveInteger default 1 | CUMPLE | `models.py:78`; test `test_quantity_default_uno` (:119). |
| 8 | Snapshot `captured_price` Decimal(12,2) + `captured_at` DateTime, inmutables | CUMPLE | `models.py:81-84`. Inmutabilidad probada: `test_captured_price_es_snapshot_inmutable_ante_observaciones` (:132, nueva PriceObservation a 999.99 no cambia el snapshot) y `test_captured_price_no_cambia_si_cambia_el_sku` (:160). Campo almacenado, no propiedad derivada del catálogo → el test fallaría si se leyera el precio en vivo. |
| 9 | Django Admin de `UserList` con inline `UserListItem` navegable | CUMPLE | `backend/apps/lists/admin.py` — `UserListAdmin` con `inlines=(UserListItemInline,)`, `search_fields=("session_key","name")`; admin se carga durante `pytest`/`init.sh` (system check sin errores). |
| 10 | Tests crear lista, agregar/quitar items, cantidades, snapshot | CUMPLE | `test_agregar_y_quitar_items_con_cantidades` (:89, agrega 2 y borra 1), más los de quantity/snapshot/cascada. 11 tests en `apps/lists`, todos verdes. |
| 11 | Subtotal (`sum(quantity*captured_price)`) en `services.py`, no en modelo ni router | CUMPLE | `backend/apps/lists/services.py:12` `subtotal_lista`. Tests `test_subtotal_lista_suma_cantidad_por_precio` (:178, =2652.50) y `test_subtotal_usa_snapshot_no_precio_en_vivo` (:208). No existe `api.py` en `apps/lists`. |
| 12 | `pytest` pasa, `ruff` limpio, `makemigrations --check --dry-run` limpio | CUMPLE | Revisor: `ruff check` ok, `makemigrations --check --dry-run` → "No changes detected" (EXIT=0), `pytest apps/lists -q` → 11 passed. `./init.sh` Fase 3 toda verde. |
| 13 | No cambia el contrato OpenAPI (sin endpoints) | CUMPLE | `git status --porcelain backend/openapi.json` → vacío (sin cambios). `./init.sh` Fase 5 verde sin drift. No hay `api.py`/`schemas.py` en `apps/lists`. |

## CHECKPOINTS.md — Global

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `./init.sh` verde de punta a punta | CUMPLE | Resumen: 31 ok, 0 fallos, 4 pendientes (jq/docker/infra/e2e, opcionales MVP). INIT_EXIT=0. |
| Solo F009 pasó a revisión; ninguna otra cambió | CUMPLE | `feature_list.json`: 7 `done` + F009 `in_progress` (único). Fase 1: "features in_progress: 1 (máximo 1)". |
| `progress/impl_F009_backend.md` con output real | CUMPLE | Existe, con output de ruff/makemigrations/migrate/pytest/lint-imports. |
| Cumple la spec criterio por criterio | CUMPLE | Tabla de spec arriba: 13/13 CUMPLE. |

## CHECKPOINTS.md — Backend

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `pytest` pasa; tests nuevos fallarían sin la implementación | CUMPLE | Tests de snapshot (campo almacenado vs. lectura en vivo) y de `subtotal_lista` (servicio inexistente) tienen dientes; pasan tras la implementación. |
| `makemigrations --check --dry-run` limpio | CUMPLE | "No changes detected", EXIT=0 (re-ejecutado por revisor). |
| `ruff check .` limpio | CUMPLE | "All checks passed!" (Fase 3 verde). |
| Lógica de negocio en `services.py`, no en routers | CUMPLE | `subtotal_lista` en `services.py`; sin `api.py` en `apps/lists`. |
| Arquitectura: `api.py` sin ORM | CUMPLE | `grep -rnE "\.objects\|\.save\(\|\.filter\(\|\.create\(\|\.delete\(" backend/apps/*/api.py backend/config/api.py` → VACÍO (exit 1). Fase 3 grep verde. (El único `.all()` está en `services.py:19`, capa permitida.) |
| Migraciones generadas y migrate limpio | CUMPLE | Fresh migrate en DB temporal aplicó `lists.0001_initial... OK` desde cero, EXIT=0. Migración commiteable junto al modelo. |
| `corsheaders`/contrato | N/A / CUMPLE | F009 no toca CORS ni contrato; `backend/openapi.json` sin cambios. |

## CHECKPOINTS.md — Higiene del arnés

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `feature_list.json` JSON válido, ≤ 1 `in_progress` | CUMPLE | Fase 1 verde; 1 in_progress. |
| Repo git inicializado | CUMPLE | `git rev-parse --is-inside-work-tree` → true; Fase 0 "repositorio git inicializado". |

## git status / git diff (alcance de capa)

```
 M backend/config/settings.py        # solo: +"apps.lists" en INSTALLED_APPS
?? backend/apps/lists/               # app nueva (modelos/services/admin/migración/tests)
?? progress/impl_F009_backend.md
```

Diff de `settings.py` (única línea funcional):
```
+    "apps.lists",
```

Sin archivos fuera de la capa backend permitida. `backend/openapi.json` NO aparece
(correcto: F009 no añade endpoints). Sin cambios en `frontend/` ni `e2e/`.

## Nota de nomenclatura (no bloqueante)

El insumo del líder mencionó "referencia `apps/catalog`/`apps/prices`". En el
codebase real `Zone`/`Retailer` viven en `apps/geo` (F006) y `RetailerProduct` en
`apps/catalog` (F007); `apps/prices` aporta `PriceObservation`, usado por los tests
de snapshot. La spec referencia `Zone` (geo) y `RetailerProduct` (catalog), y el
modelo los importa correctamente (`models.py:19-21`). No hay discrepancia: las
referencias del modelo coinciden con la estructura de dominio y con la spec.

## Output REAL de `./init.sh` (re-ejecutado por el revisor)

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
  ✔ las 7 feature(s) 'done' tienen review APROBADO

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

INIT_EXIT=0
```

## Verificaciones complementarias del revisor

- Fresh migrate (DB temporal): `lists.0001_initial... OK`, EXIT=0 (db temporal eliminada).
- `makemigrations --check --dry-run`: "No changes detected", EXIT=0.
- `pytest apps/lists -q`: 11 passed.
- Grep ORM en api.py: VACÍO.
- `git status --porcelain backend/openapi.json`: VACÍO (sin cambios de contrato).

## Conclusión

Todos los criterios de la spec (13/13) y los puntos aplicables de CHECKPOINTS
(Global + Backend + Higiene) se cumplen con evidencia ejecutable. `./init.sh`
termina VERDE. El contrato OpenAPI no cambió. Sin archivos fuera de la capa
backend. **APROBADO.**
