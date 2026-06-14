# Informe implementer-backend — F018 (API de retailers)

**Spec aplicada:** `specs/F018-api-retailers.md` — `GET /api/retailers` → `RetailerOut[]`.

## Decisiones tomadas

- `RetailerOut` con shape EXACTO de la spec: `id: str, name, slug, pricing_model,
  scraper_status, is_active: bool`. Los enums (`pricing_model`, `scraper_status`)
  se exponen como `str` (valores `zone_cookie`/`distributor_subpath`,
  `active`/`paused`/`non_viable`) según contrato.
- `listar_retailers()` devuelve TODOS los retailers (NO filtra `is_active`,
  a diferencia de zonas) ordenados por `name`, para diagnóstico. `is_active` se
  hereda de `TimeStampedUUIDModel`, no requirió migración.
- Router delgado: ruta `/retailers` declarada en `apps/geo/api.py` (router montado
  con prefijo `""`; URL final `/api/retailers`), `response=list[RetailerOut]`
  explícito, sin ORM; toda la lógica en `services.py`.
- Test independiente del seed (crea sus propios retailers, incluye uno inactivo).

## Archivos creados/modificados

- `backend/apps/geo/schemas.py` (mod): + `RetailerOut`.
- `backend/apps/geo/services.py` (mod): + `listar_retailers()` y `_retailer_to_out()`.
- `backend/apps/geo/api.py` (mod): + ruta `GET /retailers`.
- `backend/apps/geo/tests/test_retailers_api.py` (nuevo): 2 tests (todos los
  retailers, orden por name, shape exacto, inactivo incluido).
- `backend/openapi.json` (regenerado).

## ¿Cambió el contrato OpenAPI?

**SÍ.** Nuevo path `/api/retailers` (GET) y nuevo schema `RetailerOut`.
El líder debe disparar `pnpm gen:api` en frontend antes del implementer-frontend.

Verificado en `backend/openapi.json`:
- `"/api/retailers"` presente (línea 59), GET → `array` de `$ref RetailerOut`.
- `RetailerOut` (línea 677) con `required: [id, name, slug, pricing_model,
  scraper_status, is_active]`, tipos `string`/`boolean` correctos.

## Output REAL de verificación

### `uv run ruff check .`
```
All checks passed!
```

### `uv run python manage.py makemigrations --check --dry-run`
```
No changes detected
```

### `uv run pytest apps/geo`
```
............                                                             [100%]
12 passed in 1.28s
```

(Test file nuevo aislado:)
```
apps\geo\tests\test_retailers_api.py ..                                  [100%]
============================== 2 passed in 2.32s ==============================
```

### Confirmación contrato
```
59:    "/api/retailers": {
71:                    "$ref": "#/components/schemas/RetailerOut"
677:      "RetailerOut": {
713:        "title": "RetailerOut",
```

## Deuda / seguimientos

- "Interno" sin auth en MVP (endpoint público); proteger (admin/staff) cuando
  exista login/roles (RNF/§14). Ya anotado en la spec como deuda abierta.
- Pendiente del líder: `pnpm gen:api` en frontend (contrato cambió) + Fase 5
  sin drift, antes de implementer-frontend.
- El seed NO crea retailers inactivos; el criterio "≥2 retailers (Home Depot,
  Construrama)" del seed se cubre con los 2 activos. El caso `is_active=false`
  se valida vía factory en el test (no vía seed).
