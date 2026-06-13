# Veredicto: APROBADO

Review de **F007 — Modelo de catálogo (Category, CanonicalProduct, RetailerProduct + curación manual en Admin)**.
Capa única: backend. Revisor: re-ejecutó todas las verificaciones (no parafrasea al implementer).

## Resumen ejecutivo

`./init.sh` (modo full, sin `--e2e`) termina **VERDE** (31 ok · 0 fallos · 4 pendientes), exit 0.
Los 3 modelos heredan `apps.common.models.TimeStampedUUIDModel` y `RetailerProduct.retailer` referencia
correctamente `apps.geo.models.Retailer`. La curación manual SKU↔canónico es operable en Django Admin.
El diff queda confinado a `backend/` (catalog + 1 línea de settings.py) y `progress/`. `backend/openapi.json`
**no cambió** y la Fase 5 (contrato) está verde sin regenerar tipos: F007 no añade endpoints. Los pendientes
(jq, docker) son del entorno MVP (SQLite/sin-Docker), no fallos.

## Criterios de aceptación de `specs/F007-modelo-catalogo.md`

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | Las 3 entidades en `models.py` heredando la base de F006; `migrate` corre limpio | CUMPLE | `backend/apps/catalog/models.py`: `Category`, `CanonicalProduct`, `RetailerProduct` todas `class X(TimeStampedUUIDModel)`. Fresh migrate en DB temporal: `geo.0001_initial` → `catalog.0001_initial` → todo `OK`, exit 0. `manage.py check` → 0 issues. |
| 2 | Campos/relaciones exactos (PRD §8) | CUMPLE | `Category`: name, slug(unique), parent(self-FK, null/blank, related_name `children`). `CanonicalProduct`: name, category(FK→Category, related_name `products`), unit(TextChoices pieza/saco/m/kg), specs(JSONField default dict). `RetailerProduct`: retailer(FK→geo.Retailer, related_name `products`), external_sku, raw_name, url(blank), unit_raw(blank), brand(blank), canonical_product(FK→CanonicalProduct, null/blank, SET_NULL, related_name `retailer_products`), match_status(TextChoices unmatched/auto/manual/rejected, default unmatched), match_confidence(Float null/blank), `unique_together=(retailer, external_sku)`. Verificado en `models.py` y `migrations/0001_initial.py`. |
| 3 | Admin `RetailerProduct`: `list_filter` por match_status + retailer, `search_fields` raw_name/external_sku, capacidad de asignar canónico (D1); Admin de CanonicalProduct y Category navegables | CUMPLE | `backend/apps/catalog/admin.py`: `RetailerProductAdmin` con `list_filter=("match_status","retailer","is_active")`, `search_fields=("raw_name","external_sku","brand")`, `list_editable=("canonical_product",)` + `autocomplete_fields=("canonical_product",)` + acción masiva `asignar_a_canonico_manual` que marca `match_status=manual`. `CategoryAdmin` y `CanonicalProductAdmin` registrados y con `search_fields` (requisito de los autocompletes). `manage.py check` → 0 issues (no `admin.E040`). |
| 4 | Tests: crear Category "Varilla", un CanonicalProduct, dos RetailerProduct unmatched, asignarlos → manual; y verificar unique_together | CUMPLE | `backend/apps/catalog/tests/test_models.py`: `test_matching_manual_dos_retailers_a_un_canonico` (dos SKUs unmatched → manual, agrupados por `retailer_products`) y `test_retailer_product_unique_together` (duplicado lanza IntegrityError). 9 tests, todos passed. |
| 5 | `uv run pytest` pasa, `ruff check .` limpio, `makemigrations --check --dry-run` limpio | CUMPLE | `pytest -q` suite completa: 17 passed, exit 0. `pytest apps/catalog -v`: 9 passed. `ruff check .`: "All checks passed!", exit 0. `makemigrations --check --dry-run`: "No changes detected", exit 0. |
| 6 | No cambia el contrato OpenAPI (sin endpoints) | CUMPLE | `git status --porcelain backend/openapi.json` → vacío (sin cambios). `apps/catalog/` no tiene `api.py` ni `schemas.py`. `./init.sh` Fase 5 verde sin regenerar tipos. |

## Sección Backend de `CHECKPOINTS.md`

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `uv run pytest` pasa; tests nuevos que fallarían sin la implementación | CUMPLE | 17 passed. "git stash mental": `test_models.py` importa `from apps.catalog.models import CanonicalProduct, Category, RetailerProduct` a nivel de módulo → sin los modelos, la colección del módulo erroraría. Dependencia real, no test vacío. |
| `makemigrations --check --dry-run` limpio | CUMPLE | "No changes detected", exit 0. |
| `ruff check .` limpio | CUMPLE | "All checks passed!", exit 0. |
| Lógica de negocio en `services.py`, no en routers | NO APLICA | F007 es solo modelos + Admin; no añade routers ni services. |
| `api.py` sin ORM (`.objects`/`.save(`/`.filter(`/`.create(`/`.delete(`) | CUMPLE | `grep -rnE "\.objects\|\.save\(\|\.filter\(\|\.create\(\|\.delete\(" backend/apps/*/api.py backend/config/api.py` → VACÍO (exit 1). `./init.sh` Fase 3: "arquitectura: routers (api.py) sin llamadas al ORM". |
| `corsheaders` configurado | NO APLICA / SIN REGRESIÓN | F007 no toca CORS; el único cambio en settings.py es `+ "apps.catalog",`. |
| Migraciones commiteadas junto al modelo | CUMPLE | `migrations/0001_initial.py` presente como untracked junto a `models.py` (ambos nuevos en el mismo dir). |

## Higiene del arnés

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `feature_list.json` JSON válido, ≤1 in_progress | CUMPLE | `./init.sh` Fase 1: "feature_list.json es JSON válido (array)", "features in_progress: 1 (máximo 1)". Solo F007 está `in_progress`. |
| Features `done` con review APROBADO | CUMPLE | Fase 1: "las 5 feature(s) 'done' tienen review APROBADO". |
| Repo git inicializado | CUMPLE | `git rev-parse --is-inside-work-tree` → true. Fase 0: "repositorio git inicializado". |

## Diff (alcance de archivos tocados)

`git status --porcelain`:

```
 M backend/config/settings.py
?? backend/apps/catalog/
?? progress/impl_F007_backend.md
```

`git diff backend/config/settings.py` (única modificación de archivo existente):

```
@@ -47,6 +47,7 @@ INSTALLED_APPS = [
     "apps.core",
     "apps.common",
     "apps.geo",
+    "apps.catalog",
 ]
```

Untracked dentro de `backend/apps/catalog/`: `__init__.py`, `apps.py`, `models.py`, `admin.py`,
`migrations/__init__.py`, `migrations/0001_initial.py`, `tests/__init__.py`, `tests/test_models.py`.

Todo dentro de la capa permitida (backend: catalog + settings.py) + progress/. **`backend/openapi.json`
NO aparece.** Sin archivos fuera de la capa.

## Greps de arquitectura (deterministas)

- ORM en routers: `grep -rnE "\.objects|\.save\(|\.filter\(|\.create\(|\.delete\(" backend/apps/*/api.py backend/config/api.py` → **VACÍO** (exit 1). CUMPLE.
- No hay `api.py`/`schemas.py` en `apps/catalog/` (sin superficie de contrato). CUMPLE.
- (Frontend/`fetch`/`any`: N/A — F007 no toca frontend.)

## Verificación de migración fresca (DB temporal)

Primer intento con `DATABASE_URL` de ruta absoluta Windows falló por `sqlite3.OperationalError: unable to
open database file` — artefacto de parseo de la URL (`sqlite:///C:/...`), NO defecto de la migración.
Reintento con ruta relativa (patrón del proyecto, `sqlite:///db.sqlite3` per `backend/CLAUDE.md`) corrió limpio:
todas las migraciones aplicadas `OK`, `catalog.0001_initial [X]`. DB temporal eliminada tras la prueba.

## Output REAL de `./init.sh` (modo full, sin --e2e)

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
  ✔ las 5 feature(s) 'done' tienen review APROBADO

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

===INIT_EXIT:0===
```

## Conclusión

Todos los criterios de la spec CUMPLEN, la sección Backend e Higiene de CHECKPOINTS cumplen,
los greps de arquitectura dan vacío, el diff está confinado a la capa permitida, `openapi.json`
no cambió y `./init.sh` termina VERDE. **APROBADO.**
