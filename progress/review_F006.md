# Veredicto: APROBADO

Review de **F006** — Modelo M0: base abstracta `TimeStampedUUIDModel` + geografía
y retailers (`Retailer`, `RetailerLocation`, `Zone`, `ZoneLocationMap`) + Admin.
Capa única backend (no toca contrato/frontend/e2e). Verificaciones re-ejecutadas
por el reviewer; no se confió en el output pegado por el implementer.

> Nota de entorno: el header del arnés decía "Is directory a git repo: No", pero
> `git rev-parse --is-inside-work-tree` devolvió `true` y la Fase 0 de `init.sh`
> lo confirma. El repo existe; el diff del reviewer es ejecutable. No es bloqueo.

## Criterios de aceptación de `specs/F006` (uno por uno)

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | Base abstracta `TimeStampedUUIDModel` (UUID PK `editable=False`, `created_at` auto_now_add, `updated_at` auto_now, `is_active` default True, `abstract=True`) | CUMPLE | `backend/apps/common/models.py:13-26` — campos exactos y `class Meta: abstract = True` |
| 2 | Las 4 entidades heredan la base, con campos exactos del PRD §8 | CUMPLE | `backend/apps/geo/models.py`: `Retailer` (16-42), `RetailerLocation` (45-66, FK related_name `locations`), `Zone` (69-86), `ZoneLocationMap` (89-109, FK related_names `location_maps`/`zone_maps`, `is_primary` default False) |
| 3 | `unique_together = (zone, retailer_location)` en el map | CUMPLE | `models.py:105`; migración `0001_initial.py:84` `'unique_together': {('zone', 'retailer_location')}` |
| 4 | `makemigrations` generó migración y `migrate` corre limpio (SQLite, sin Docker) | CUMPLE | `geo/migrations/0001_initial.py` presente; fresh migrate aplicó `geo.0001_initial... OK` desde cero (DB temporal `reviewer_fresh.sqlite3`, luego eliminada). `migrate` sobre db actual: `No migrations to apply` (exit 0) |
| 5 | `makemigrations --check --dry-run` limpio | CUMPLE | `uv run python manage.py makemigrations --check --dry-run` → `No changes detected` (exit 0) |
| 6 | Las 4 entidades registradas en Admin con `list_display`/`list_filter`; `scraper_status` filtrable en Retailer | CUMPLE | Verificado en runtime (`admin.site._registry`): las 4 registradas; `RetailerAdmin.list_filter=('scraper_status','pricing_model','is_active')` → `scraper_status filterable on Retailer: True`. `backend/apps/geo/admin.py:12-39` |
| 7 | Tests crean Retailer+RetailerLocation, Zone y un ZoneLocationMap que los une; verifican `is_primary` y `unique_together` (duplicado → IntegrityError) | CUMPLE | `backend/apps/geo/tests/test_models.py`: une zona↔ubicación (67-77), `is_primary` True/default-False (75, 81-84), `unique_together` lanza `IntegrityError` (87-93), soft-delete `is_active` (96-103), base abstracta UUID/timestamps (48-56) |
| 8 | Los tests fallarían sin la implementación (regla git-stash-mental) | CUMPLE | El test importa a nivel de módulo `from apps.geo.models import Retailer, RetailerLocation, Zone, ZoneLocationMap` (AST confirma import top-level de los 4 nombres). Sin la implementación, la colección de pytest aborta con ImportError. No son tests vacíos: aserciones sobre relaciones reales y `pytest.raises(IntegrityError)` |
| 9 | `uv run pytest` pasa | CUMPLE | `uv run pytest -q` → `........` 8 passed (6 geo + 2 health). `uv run pytest apps/geo -q` → `......` 6 passed |
| 10 | `uv run ruff check .` limpio | CUMPLE | `All checks passed!` (exit 0) |
| 11 | No se añade router/endpoint; el contrato OpenAPI NO cambia | CUMPLE | No hay `api.py` ni schemas nuevos en `apps/geo`/`apps/common`. `git status --porcelain backend/openapi.json` → vacío (no listado). `init.sh` Fase 5 VERDE sin drift |

## Sección Backend de `CHECKPOINTS.md` (punto por punto)

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `uv run pytest` pasa; tests nuevos que fallarían sin la implementación | CUMPLE | 8 passed; import top-level de `apps.geo.models` (ver criterio 8) |
| `makemigrations --check --dry-run` limpio | CUMPLE | `No changes detected` |
| `uv run ruff check .` limpio | CUMPLE | `All checks passed!` |
| Lógica de negocio en `services.py`, no en routers | CUMPLE (N/A) | F006 no añade routers ni servicios; la lógica de modelo vive en `models.py` (ORM en models/tests es correcto) |
| Arquitectura: `api.py` sin llamadas al ORM | CUMPLE | `grep -rnE "\.objects\|\.save\(\|\.filter\(\|\.create\(\|\.delete\(" backend/apps/*/api.py backend/config/api.py` → VACÍO (exit 1). `init.sh` Fase 3: "routers (api.py) sin llamadas al ORM" |
| `corsheaders` con `CORS_ALLOWED_ORIGINS` desde env | CUMPLE (N/A) | F006 no toca settings de CORS; ya estaba configurado en features previas. El único cambio en `settings.py` es `INSTALLED_APPS += apps.common, apps.geo` |
| Migraciones commiteadas junto al modelo | CUMPLE | `geo/migrations/0001_initial.py` acompaña a `geo/models.py` (ambos en el diff de la feature, pendientes de commit del líder al cerrar) |
| Si cambió el contrato: `openapi.json` regenerado | N/A | El contrato no cambió (ver criterio 11) |

## Diff / aislamiento de capa

`git status --porcelain`:
```
 M backend/config/settings.py
?? backend/apps/common/
?? backend/apps/geo/
?? progress/impl_F006_backend.md
```
Diff de `settings.py`: solo `+    "apps.common"` y `+    "apps.geo"` en `INSTALLED_APPS`.
Todo cae dentro de la capa permitida (`backend/apps/common`, `backend/apps/geo`,
`backend/config/settings.py`) + `progress/`. **No** hay tocados en `frontend/`,
`e2e/` ni `backend/openapi.json`. Higiene del arnés: `feature_list.json` válido con
1 `in_progress` (F006); `progress/current.md` refleja la sesión.

## Output REAL de `./init.sh` (modo full, sin --e2e) — exit 0

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
  ✔ las 4 feature(s) 'done' tienen review APROBADO

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

Los 4 pendientes son diferimientos esperados del MVP (jq, docker, Fase 2
infra Postgres/Redis, E2E no solicitado), no fallos. **0 fallos.**

## Conclusión

Todos los criterios de `specs/F006` y la sección Backend + Higiene de
`CHECKPOINTS.md` se cumplen con evidencia ejecutable. `./init.sh` VERDE. El
contrato OpenAPI no cambió (Fase 5 verde, `openapi.json` ausente del diff).
La arquitectura está limpia (ORM solo en `models.py`/tests, `api.py` sin ORM).
Los tests fallarían sin la implementación. **APROBADO.**
