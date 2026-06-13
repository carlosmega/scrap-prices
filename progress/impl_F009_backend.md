# impl F009 backend — Modelo de listas de cotización (anónimo / sesión)

## Spec aplicada y decisiones (máx. 5 líneas)
- Spec: `specs/F009-modelo-listas-cotizacion.md`. Modelos `UserList` / `UserListItem` heredando `apps.common.models.TimeStampedUUIDModel`.
- **Anónimo / sesión (decisión de producto del MVP):** `UserList` NO tiene `user`/`user_fk`; se identifica por `session_key` (CharField, `db_index=True`). El login propio se difiere a fase posterior.
- App nueva `apps/lists/` (label `lists`, single-word como `geo`/`catalog`/`prices`); registrada en `INSTALLED_APPS`.
- Snapshot inmutable: `captured_price` (Decimal 12,2) + `captured_at` (DateTime) se copian al crear el ítem; nunca se releen del catálogo (CA2). `quantity` PositiveInteger default 1, `notes` blank.
- Subtotal (`sum(quantity * captured_price)`) vive en `apps/lists/services.py` (`subtotal_lista`), no en el modelo ni en routers. Sin endpoints Ninja → contrato OpenAPI intacto.

## Archivos creados / modificados
- Creado `backend/apps/lists/__init__.py`
- Creado `backend/apps/lists/apps.py`
- Creado `backend/apps/lists/models.py` (`UserList`, `UserListItem`)
- Creado `backend/apps/lists/services.py` (`subtotal_lista`)
- Creado `backend/apps/lists/admin.py` (`UserListAdmin` con inline `UserListItemInline`; `UserListItemAdmin`)
- Creado `backend/apps/lists/migrations/__init__.py`
- Creado `backend/apps/lists/migrations/0001_initial.py`
- Creado `backend/apps/lists/tests/__init__.py`
- Creado `backend/apps/lists/tests/test_models.py` (11 tests)
- Modificado `backend/config/settings.py` (añadido `"apps.lists"` a `INSTALLED_APPS`)

## ¿Cambió el contrato OpenAPI?
**NO.** No se añadió ningún `api.py`/router ni schema en `apps/lists/`. No se regeneró `backend/openapi.json` (no procede). No hace falta `pnpm gen:api` en frontend.

## Output REAL de verificación

### `uv run ruff check .`
```
All checks passed!
```

### `uv run python manage.py makemigrations --check --dry-run`
```
No changes detected
```

### `uv run python manage.py migrate`
```
Operations to perform:
  Apply all migrations: admin, auth, catalog, contenttypes, geo, lists, prices, sessions
Running migrations:
  Applying lists.0001_initial... OK
```

### `uv run pytest -q`
```
.....................................                                    [100%]
37 passed in 0.54s
```

### `uv run lint-imports` (regla de capas, refuerzo de arquitectura)
```
Routers (api) no importan models directamente; delegan en services KEPT

Contracts: 1 kept, 0 broken.
```

## Deuda / seguimientos detectados
- Sin `api.py`/`schemas.py`/`tasks.py` en `apps/lists/` (fuera de alcance de F009; los endpoints de listas/ítems son M4). Si el reviewer espera el set completo de archivos por dominio, queda como seguimiento de la feature de API.
- Cuando se añada login (fase posterior): agregar `user = FK→User(null=True)` a `UserList` sin romper este contrato (nota de la spec §Modelo).
- `UserListItem.retailer_product` usa `on_delete=CASCADE`: al borrar un `RetailerProduct` desaparecen sus ítems en listas. Si producto prefiere conservar el snapshot histórico tras borrar el SKU, revisar a `SET_NULL` en una feature futura (no pedido por la spec).
