# Veredicto: APROBADO

Review de **F008 — Modelo M0: precios y auditoría de scraping** (`PriceObservation`,
`ScrapeRun` + Admin). Capa única backend. Verificación re-ejecutada por el reviewer,
no parafraseada del implementer.

Insumos: `specs/F008-modelo-precios-scraping.md`, `CHECKPOINTS.md` (Global + Backend +
Higiene), `progress/impl_F008_backend.md`. Modo `./init.sh` full (sin `--e2e`).

---

## Criterios de aceptación de la spec — uno por uno

| # | Criterio (spec F008) | Estado | Evidencia |
|---|----------------------|--------|-----------|
| 1 | `PriceObservation` y `ScrapeRun` en `models.py`, heredan la base abstracta | CUMPLE | `models.py:21` y `:79` heredan `TimeStampedUUIDModel` (`apps/common/models.py:13`); la migración `0001_initial.py:21-24,40-43` materializa `id` UUID + `created_at`/`updated_at`/`is_active`. Test `test_price_observation_hereda_base_y_price_decimal` valida `id` UUID y timestamps. |
| 2 | `price` es **Decimal** (no float), max_digits 12, decimal_places 2 | CUMPLE | `models.py:54` `DecimalField(max_digits=12, decimal_places=2)`; migración `:44`. Test `test_..._price_decimal` afirma `isinstance(obs.price, Decimal)` y `== Decimal("199.99")`. |
| 3 | `source` choices `xhr`/`html`/`playwright` | CUMPLE | `models.py:30-33` `TextChoices`; migración `:47` `choices=[('xhr',...),('html',...),('playwright',...)]`. |
| 4 | `raw_payload` es JSON (`default=dict`) | CUMPLE | `models.py:62` `JSONField(default=dict, blank=True)`; migración `:49`. |
| 5 | Campos exactos `PriceObservation` (FKs + related_name `observations`, currency MXN, is_available, captured_at indexado) | CUMPLE | `models.py:35-62`: `retailer_product` CASCADE related_name `observations`, `zone`/`retailer_location` SET_NULL null/blank related_name `observations`, `currency` default `MXN`, `is_available` default True, `captured_at` `db_index=True`. Test `test_observations_related_name` valida los 3 related_name. |
| 6 | Campos exactos `ScrapeRun` (retailer FK related_name `scrape_runs`, zone null, started_at, finished_at null, status choices, items_found default 0, errors default list) | CUMPLE | `models.py:87-103`; migración `:25-31`. Test `test_scrape_run_defaults` valida `items_found==0`, `errors==[]`, `zone is None`, `finished_at is None`. |
| 7 | **Índice compuesto `(retailer_product, zone, -captured_at)` aparece en la migración** | CUMPLE | `0001_initial.py:56` `models.Index(fields=['retailer_product', 'zone', '-captured_at'], name='price_obs_rp_zone_capt_idx')`. (No solo en `models.py:66-72`: confirmado dentro de la migración como exige la spec.) |
| 8 | Admin `ScrapeRun`: list_display(retailer, zona, status, items_found, started_at) + list_filter(status/retailer) | CUMPLE | `admin.py:31-32` `list_display=("retailer","zone","status","items_found","started_at")`, `list_filter=("status","retailer")`. |
| 9 | Admin `PriceObservation`: filtros por retailer_product/zone y orden `-captured_at` | CUMPLE | `admin.py:23` `list_filter=("retailer_product","zone","source","is_available")` (incluye los dos exigidos), `admin.py:25` `ordering=("-captured_at",)`. |
| 10 | Test: "última observación por producto+zona" devuelve la más reciente | CUMPLE | `test_ultima_observacion_devuelve_la_mas_reciente` crea 3 obs con `captured_at` crecientes y afirma `services.ultima_observacion(sku, zona) == reciente` y que el histórico (3 filas) se conserva. |
| 11 | Test: `ScrapeRun` partial con `errors` no vacío | CUMPLE | `test_scrape_run_partial_con_errores`: status PARTIAL, `errors` con 2 elementos, `len(run.errors)==2`. |
| 12 | Test: `raw_payload` persiste como JSON | CUMPLE | `test_raw_payload_persiste_como_json` con dict anidado + listas; tras `refresh_from_db()` afirma igualdad y `raw_payload["fields"]["stock"] is True`. |
| 13 | Helper "última observación" vive en `services.py` (no en api.py) | CUMPLE | `grep "def ultima_observacion" apps/` → solo `apps/prices/services.py:13`. No existe `apps/prices/api.py` (`ls apps/prices/api.py` → No such file). |
| 14 | Los tests fallarían sin la implementación | CUMPLE | `test_ultima_observacion_aisla_por_zona` inserta una obs con `captured_at` MAYOR en *otra* zona y afirma que NO es devuelta → falla si el helper no filtra por zona o no ordena `-captured_at` (no es tautológico, ejercita el filtro + orden reales). `test_..._mas_reciente` falla si se devolviera `.first()` sin `order_by`. |
| 15 | `migrate` limpio (fresh migrate en DB temporal) | CUMPLE | Fresh migrate desde cero sobre `sqlite:///tmp_review_f008.sqlite3`: `Applying prices.0001_initial... OK` (geo y catalog aplican antes; deps correctas en migración `:12-15`). DB temporal eliminada tras la corrida. |
| 16 | `makemigrations --check --dry-run` limpio | CUMPLE | `./init.sh` Fase 3: "migraciones al día (makemigrations --check)" ✔. |
| 17 | `uv run pytest` pasa | CUMPLE | `./init.sh` Fase 3: "pytest" ✔ (suite completa). `pytest apps/prices` aislado: 9 tests, todos pasan. |
| 18 | `ruff check .` limpio | CUMPLE | `./init.sh` Fase 3: "ruff check" ✔. |
| 19 | No cambia el contrato OpenAPI (sin endpoints) | CUMPLE | `git status --short backend/openapi.json` → vacío (sin cambios). No hay `api.py`/`schemas.py` en `apps/prices`. `./init.sh` Fase 5: "tipos TS sincronizados con backend/openapi.json" ✔. |
| 20 | Referencia correcta a `apps/geo` (Zone, RetailerLocation, Retailer) y `apps/catalog` (RetailerProduct) | CUMPLE | `models.py:16-18` importa de `apps.catalog.models` y `apps.geo.models`; los modelos existen (`geo/models.py:16,45,69`, `catalog/models.py:66`) y todos heredan `TimeStampedUUIDModel`. |

---

## CHECKPOINTS.md — sección Global

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `./init.sh` verde de punta a punta | CUMPLE | Resumen: 31 ok, 0 fallos, 4 pendientes; "VERDE"; exit 0 (output abajo). |
| Solo la feature actual pasó a revisión; ninguna otra cambió | CUMPLE | `feature_list.json`: F008 `in_progress`, F009 `pending`, F001-F007 `done` (sin tocar). Fase 1: "features in_progress: 1 (máximo 1)" ✔. |
| Existe `progress/impl_F008_backend.md` con output real | CUMPLE | Presente, con outputs de ruff/makemigrations/migrate/pytest/lint-imports e índice. |
| Cumple cada criterio de la spec | CUMPLE | Tabla de 20 filas arriba. |

## CHECKPOINTS.md — sección Backend

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `uv run pytest` pasa; tests nuevos que fallarían sin la implementación | CUMPLE | Ver criterios 14 y 17. |
| `makemigrations --check --dry-run` limpio | CUMPLE | Fase 3 ✔. |
| `ruff check .` limpio | CUMPLE | Fase 3 ✔. |
| Lógica de negocio en `services.py`, no en routers | CUMPLE | `ultima_observacion` solo en `services.py:13`; sin `api.py` en la app. |
| `api.py` sin llamadas al ORM; regla de capas pasa | CUMPLE | `grep -rnE "\.objects\|\.save\(\|\.filter\(\|\.create\(\|\.delete\(" backend/apps/*/api.py backend/config/api.py` → VACÍO (exit 1). Fase 3: "routers (api.py) sin llamadas al ORM" ✔. |
| `corsheaders` con `CORS_ALLOWED_ORIGINS` desde env | NO VERIFICABLE (fuera de alcance F008) | F008 no toca CORS; ya establecido en bootstrap previo. Sin regresión: settings.py solo añade `"apps.prices"` a `INSTALLED_APPS`. |
| Si cambió el contrato: openapi regenerado | NO APLICA | El contrato no cambió (criterio 19). |
| Migraciones commiteadas junto al modelo | CUMPLE (en working tree) | `0001_initial.py` presente junto al modelo. Nota: el repo aún no ha *commiteado* `apps/prices/` (aparece como `??` untracked) — es responsabilidad del líder commitear al marcar `done`; no es un fallo de la implementación. |

## CHECKPOINTS.md — Higiene del arnés

| Punto | Estado | Evidencia |
|-------|--------|-----------|
| `feature_list.json` JSON válido con ≤ 1 `in_progress` | CUMPLE | Fase 1 ✔ (1 in_progress). |
| `progress/current.md` refleja la sesión | NO VERIFICADO POR EL REVISOR | Responsabilidad del líder; fuera del veredicto de implementación. |
| Toda feature `done` tiene review APROBADO | CUMPLE | Fase 1: "las 6 feature(s) 'done' tienen review APROBADO" ✔. |
| Repo inicializado como git | CUMPLE | Fase 0: "repositorio git inicializado" ✔. |

---

## Arquitectura limpia — greps deterministas

```
$ grep -rnE "\.objects|\.save\(|\.filter\(|\.create\(|\.delete\(" backend/apps/*/api.py backend/config/api.py
(sin salida — exit 1)   → VACÍO. ORM nunca en routers.

$ grep -rn "fetch(" frontend/src --include=*.ts --include=*.tsx | grep -v "lib/api/client.ts"
(sin salida)            → VACÍO. (F008 no toca frontend; sin regresión.)
```

`ultima_observacion` usa el ORM (`PriceObservation.objects.filter(...).order_by("-captured_at").first()`)
correctamente dentro de `services.py:23-27`, no en un router.

---

## Alcance del diff (`git status`)

```
 M backend/config/settings.py        (solo +"apps.prices" en INSTALLED_APPS)
?? backend/apps/prices/              (app nueva: models/services/admin/migrations/tests)
?? progress/impl_F008_backend.md
```

Sin archivos fuera de la capa permitida (`backend/` + `progress/`). **`backend/openapi.json`
NO aparece** en el diff — correcto, F008 no añade endpoints.

---

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
  ✔ las 6 feature(s) 'done' tienen review APROBADO

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

=== init.sh exit code: 0 ===
```

Las 4 pendientes (jq, docker × Fase 0, Fase 2 infra, Fase 6 E2E) son esperadas en el
entorno MVP (SQLite/sin-Docker) y para una feature de capa única backend; no son fallos.

---

## Conclusión

Los 20 criterios de la spec CUMPLEN con evidencia ejecutable; las secciones Global,
Backend e Higiene de `CHECKPOINTS.md` aplicables están satisfechas; `./init.sh` termina
VERDE (exit 0); el índice compuesto está en la migración; el helper de negocio vive en
`services.py`; no hay ORM en routers; el contrato OpenAPI no cambió; el diff está dentro
de la capa permitida.

Observación no bloqueante para el líder: `backend/apps/prices/` está como `??` (untracked)
y `settings.py` como ` M` sin commitear. El criterio "migraciones commiteadas" se cumple en
el working tree; el commit corresponde al líder al marcar la feature `done` (Fase 1 de
`init.sh` ya está verde porque F008 aún no es `done`).

**Veredicto: APROBADO**
