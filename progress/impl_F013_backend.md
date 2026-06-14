# impl F013 backend — Seed de datos demo (Monterrey Metro · varilla)

## Spec aplicada y decisiones
- Spec: `specs/F013-seed-datos-demo.md`. Management command idempotente `seed`.
- App elegida: `apps.core` (transversal); cruza geo+catalog+prices, no pertenece a un solo dominio.
- Lógica de armado en `apps/core/services.py::seed_demo()`; el command es delgado (solo invoca + reporta).
- Idempotencia vía `update_or_create` con claves naturales estables (slug, retailer+external_id,
  retailer+external_sku, retailer_product+zone+captured_at). 2ª corrida crea 0 observaciones.
- `PriceObservation`: source=`xhr`, `raw_payload={"seed": true}`, currency MXN, Decimal, is_available=True.

## Archivos creados/modificados
- CREADO `backend/apps/core/management/__init__.py`
- CREADO `backend/apps/core/management/commands/__init__.py`
- CREADO `backend/apps/core/management/commands/seed.py` (command delgado, `@transaction.atomic`)
- MODIFICADO `backend/apps/core/services.py` (añadido `seed_demo()` + datos curados; se conserva `get_health`)
- CREADO `backend/apps/core/tests/test_seed.py` (grafo + ultima_observacion + idempotencia)

Grafo sembrado: 2 Retailer, 2 RetailerLocation, 1 Zone, 2 ZoneLocationMap (1 primaria),
1 Category, 3 CanonicalProduct, 6 RetailerProduct (manual), 18 PriceObservation (3 por rp×zona).

## ¿Cambió el contrato OpenAPI?
NO. Sin endpoints, sin schemas, sin rutas. No se regeneró `openapi.json`.

## Output REAL de verificaciones

### uv run python manage.py migrate
```
Operations to perform:
  Apply all migrations: admin, auth, catalog, contenttypes, geo, lists, prices, sessions
Running migrations:
  No migrations to apply.
```

### uv run python manage.py seed  (1ª corrida)
```
Seed demo aplicado (idempotente).
  retailers: 2
  locations: 2
  zones: 1
  zone_maps: 2
  categories: 1
  canonical_products: 3
  retailer_products: 6
  observations: 18
  observations_created: 18
```

### uv run python manage.py seed  (2ª corrida — idempotente)
```
Seed demo aplicado (idempotente).
  retailers: 2
  locations: 2
  zones: 1
  zone_maps: 2
  categories: 1
  canonical_products: 3
  retailer_products: 6
  observations: 18
  observations_created: 0
```

### uv run ruff check .
```
All checks passed!
```

### uv run python manage.py makemigrations --check --dry-run
```
No changes detected
```

### uv run pytest
```
........................................                                 [100%]
40 passed in 0.47s
```

(El test `apps/core/tests/test_seed.py` falla sin el command: `CommandError: Unknown command: 'seed'`,
verificado antes de implementar.)

## Deuda / seguimientos
- Ninguna bloqueante. Cuando llegue M2, el scraping real producirá PriceObservation con source real;
  el seed se distingue por `raw_payload={"seed": true}` y seguirá sirviendo para dev/tests/E2E.
- Posible mejora futura: flag `--clear` para reiniciar el dataset demo; no pedido por la spec.
