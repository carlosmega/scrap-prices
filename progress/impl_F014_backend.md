# impl F014 backend — API de zonas

## Spec aplicada y decisiones
Spec: `specs/F014-api-zonas.md`. Dos endpoints Ninja sobre `Zone`.
- `GET /api/zones`: zonas `is_active`, ordenadas por `name`, como `ZoneOut[]`.
- `POST /api/zones/resolve` (`{lat,lng}`): zona activa con centroide más cercano
  por **haversine** (sin PostGIS); solo considera zonas activas con centroide.
- 404 `{"detail":"aún sin cobertura"}` vía `ninja.errors.HttpError` si no hay
  candidata. Router delgado SIN ORM: toda la lógica/distancia vive en `services.py`.

## Archivos creados/modificados
- `backend/apps/geo/schemas.py` (nuevo): `ZoneOut` (id str, name, slug, state), `ResolveIn` (lat, lng).
- `backend/apps/geo/services.py` (nuevo): `listar_zonas_activas()`, `resolver_zona(lat,lng)`, haversine.
- `backend/apps/geo/api.py` (nuevo): `Router` geo, 2 endpoints con `response=` explícito, sin ORM.
- `backend/apps/geo/tests/test_api.py` (nuevo): 5 tests (GET lista/orden/filtro, resolve Monterrey, 404, service ignora inactivas).
- `backend/config/api.py` (mod): monta `geo_router` en `""` → rutas `/api/zones` y `/api/zones/resolve`.
- `backend/openapi.json` (regenerado): nuevos paths + schemas `ZoneOut`/`ResolveIn`.

## ¿Cambió el contrato OpenAPI?
**SÍ.** Regenerado con `export_openapi_schema`. Contiene `/api/zones`,
`/api/zones/resolve`, `ZoneOut` y `ResolveIn`. El líder debe disparar la capa
frontend (`pnpm gen:api`) antes del implementer-frontend; Fase 5 de `init.sh`
quedará en drift hasta entonces.

## Output real de verificaciones

### uv run ruff check .
```
All checks passed!
```

### uv run python manage.py makemigrations --check --dry-run
```
No changes detected
```

### uv run pytest apps/geo -q
```
..........                                                               [100%]
============================= 10 passed in 0.27s ==============================
```

### uv run pytest -q (suite completa, sanity)
```
............................................                             [100%]
44 passed
```

### Extra: contrato de capas (import-linter)
```
Routers (api) no importan models directamente; delegan en services KEPT
Contracts: 1 kept, 0 broken.
```

### Confirmación openapi.json
`grep` confirma: `"/api/zones"` (L32), `"/api/zones/resolve"` (L59),
`"ZoneOut"` (L109), `"ResolveIn"` (L138).

## Deuda / seguimientos
- Contrato cambiado → pendiente `pnpm gen:api` en frontend (responsabilidad del líder/F-frontend).
- Geocoding por dirección y PostGIS quedan diferidos por la spec (fuera de alcance).
- No corrí `./init.sh` completo a propósito: Fase 5 estaría roja hasta el gen:api del frontend.
