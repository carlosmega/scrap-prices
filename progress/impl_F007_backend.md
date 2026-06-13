# impl F007 backend — Modelo de catálogo

## Spec aplicada y decisiones (máx. 5 líneas)
- Spec `specs/F007-modelo-catalogo.md`: `Category`, `CanonicalProduct`, `RetailerProduct`, todos heredando `apps.common.models.TimeStampedUUIDModel`.
- App nueva `apps/catalog/` (coherente con el patrón un-dominio-una-app de `apps/geo`); registrada en `INSTALLED_APPS`.
- Matching manual en Admin (PRD D1): `RetailerProduct.canonical_product` editable en el listado + `autocomplete` + acción masiva que marca `match_status=manual`; filtro por `match_status`/`retailer`.
- `on_delete`: `RetailerProduct.retailer` CASCADE; `CanonicalProduct.category` PROTECT (no perder canónicos por borrar categoría); `RetailerProduct.canonical_product` SET_NULL (el SKU sobrevive si se borra el canónico). `unit` como `TextChoices` extensible; `specs` JSONField default dict.
- Varilla NO hardcodeada: solo aparece como dato en los tests/fixtures; la curación real es en Admin.

## Archivos creados/modificados
- Creado: `backend/apps/catalog/__init__.py`
- Creado: `backend/apps/catalog/apps.py`
- Creado: `backend/apps/catalog/models.py`
- Creado: `backend/apps/catalog/admin.py`
- Creado: `backend/apps/catalog/migrations/__init__.py`
- Creado: `backend/apps/catalog/migrations/0001_initial.py`
- Creado: `backend/apps/catalog/tests/__init__.py`
- Creado: `backend/apps/catalog/tests/test_models.py`
- Modificado: `backend/config/settings.py` (añade `apps.catalog` a `INSTALLED_APPS`)

## ¿Cambió el contrato OpenAPI?
NO. La feature no añade endpoints Ninja (sin `api.py`/`schemas.py`). `backend/openapi.json` no se regenera. `pnpm gen:api` NO es necesario.

## Output REAL de verificaciones

### uv run ruff check .
```
All checks passed!
===EXIT: 0===
```

### uv run python manage.py makemigrations --check --dry-run
```
No changes detected
===EXIT: 0===
```

### uv run python manage.py migrate  (SQLite)
```
Operations to perform:
  Apply all migrations: admin, auth, catalog, contenttypes, geo, sessions
Running migrations:
  Applying catalog.0001_initial... OK
===EXIT: 0===
```

### uv run pytest -q
```
.................                                                        [100%]
===EXIT: 0===
```
(17 tests en total; los 9 nuevos de `apps/catalog/tests/test_models.py` incluidos —
verificado con `uv run pytest apps/catalog -q` → 9 passed.)

### uv run lint-imports  (contrato de capas, extra)
```
Contracts: 1 kept, 0 broken.
===EXIT: 0===
```

## Deuda / seguimientos detectados
- `unit` modelada como choices extensibles; si crece, evaluar tabla `Unit` propia (fase posterior, según la spec).
- Matching automático con `rapidfuzz` y `match_confidence` poblado quedan fuera de MVP (la columna ya existe, nullable).
- Carga de SKUs reales la produce el scraping (M2); en MVP la curación es 100% manual en Admin.
