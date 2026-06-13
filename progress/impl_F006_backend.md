# impl_F006_backend — Base + geografía y retailers

## Spec aplicada y decisiones (máx. 5 líneas)
- Spec: `specs/F006-modelo-geografia-retailers.md`. Primera feature de dominio.
- Base abstracta `TimeStampedUUIDModel` ubicada en **`apps/common/models.py`**
  (`abstract = True`; sin migración propia) — es el contrato común para F007–F009.
- Modelos de dominio (`Retailer`, `RetailerLocation`, `Zone`, `ZoneLocationMap`)
  en **`apps/geo/`** (app nueva), dejando espacio a catálogo/precios en apps propias.
- `lat`/`lng`/`centroid_*` modelados como `DecimalField(9,6)` null/blank; choices de
  Retailer vía `TextChoices`; `unique_together = (zone, retailer_location)` en el map.
- F006 NO añade endpoints → el contrato OpenAPI NO cambia (no se regeneró `openapi.json`).

## Archivos creados/modificados
Creados:
- `backend/apps/common/__init__.py`
- `backend/apps/common/apps.py`
- `backend/apps/common/models.py`  (base abstracta `TimeStampedUUIDModel`)
- `backend/apps/geo/__init__.py`
- `backend/apps/geo/apps.py`
- `backend/apps/geo/models.py`  (4 entidades de dominio)
- `backend/apps/geo/admin.py`  (registro Admin de las 4 entidades)
- `backend/apps/geo/migrations/__init__.py`
- `backend/apps/geo/migrations/0001_initial.py`  (generada y commiteable)
- `backend/apps/geo/tests/__init__.py`
- `backend/apps/geo/tests/test_models.py`  (6 tests)

Modificados:
- `backend/config/settings.py`  (INSTALLED_APPS += `apps.common`, `apps.geo`)

## ¿Cambió el contrato OpenAPI?
**NO.** No se añadieron routers/endpoints/schemas. `backend/openapi.json` intacto
(no aparece en `git status`). No procede `pnpm gen:api`.

## Output REAL de las verificaciones

### `uv run ruff check .`
```
All checks passed!
```

### `uv run python manage.py makemigrations --check --dry-run`
```
No changes detected
```
(exit=0 — migración ya generada/commiteada)

### `uv run python manage.py migrate`  (SQLite, sin Docker)
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, geo, sessions
Running migrations:
  Applying geo.0001_initial... OK
```

### `uv run pytest -q`
```
........                                                                 [100%]
```
(8 tests: 6 nuevos de geo + 2 de health. Solo geo: `uv run pytest apps/geo -q` → `......` 6 passed)

### Extra — `uv run lint-imports` (regla de capas)
```
Routers (api) no importan models directamente; delegan en services KEPT
Contracts: 1 kept, 0 broken.
```

## Deuda / seguimientos detectados
- Los tests fallan sin la implementación por diseño: importan `apps.geo.models`,
  inexistente antes de esta feature (ImportError en colección).
- Sin datos seed de Monterrey Metro (fuera de alcance por spec; carga manual vía Admin).
- F007–F009 deben heredar de `apps.common.models.TimeStampedUUIDModel`.
- Sin restricción de "una sola `is_primary` por zona" a nivel de DB; la spec solo
  pide el flag y el `unique_together`. Si el producto lo requiere, abrir feature aparte.
