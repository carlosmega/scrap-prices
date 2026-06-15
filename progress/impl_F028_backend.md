# Informe — F028 (backend): seed con código real de tienda HD Monterrey

## Spec aplicada y decisiones (máx. 5 líneas)
- Spec: `specs/F028-seed-store-real-hd.md`. En `seed_demo` la `RetailerLocation` de HD
  Monterrey usa `external_id="1333"` (recon F010 §3) en vez del placeholder `store-2034`.
- Decisión idempotencia: la clave de `update_or_create` pasó de `(retailer, external_id)`
  a `(retailer, name)` con `external_id` movido a `defaults`. Así la clave de lookup es
  estable (no es el valor que cambia) y re-sembrar ACTUALIZA el external_id en sitio en
  vez de crear una fila huérfana junto a la vieja `store-2034`.
- Sin endpoints tocados → contrato OpenAPI sin cambios. Construrama y el adapter (F025) intactos.

## Archivos creados/modificados
- `backend/apps/core/services.py` — `seed_demo`: lookup de la HD location re-keyeado a
  `(retailer, name="Home Depot Valle Oriente")`, `external_id="1333"` en defaults. Comentario explicando la elección de clave.
- `backend/apps/core/tests/test_seed.py` — asserts nuevos: `hd_loc.external_id == "1333"`,
  `city`/`state` Monterrey/NL; en el test de idempotencia, tras 2ª corrida queda exactamente
  1 location HD con external_id `1333` (cubre el caso de la fila huérfana).

## ¿Cambió el contrato OpenAPI?
NO. No se tocaron schemas ni rutas; no hay endpoints. No se regeneró `openapi.json`.

## Output REAL

### uv run python manage.py migrate
```
Operations to perform:
  Apply all migrations: admin, auth, catalog, contenttypes, geo, lists, prices, sessions
Running migrations:
  No migrations to apply.
```

### uv run python manage.py seed (1ª corrida)
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

### uv run python manage.py seed (2ª corrida)
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

### Verificación idempotencia (shell): 1 location HD, external_id == '1333'
```
count = 1
external_id = '1333'
name = 'Home Depot Valle Oriente'
city = 'Monterrey' state = 'NL'
```

### Prueba del caso huérfano (DB legacy con 'store-2034' → re-seed)
```
antes  count = 1 ext = store-2034
--- re-seed sobre DB legacy ---
Seed demo aplicado (idempotente).
  ...
  locations: 2
  ...
despues count = 1 ext = 1333
```
Confirma: la fila vieja se ACTUALIZA en sitio (count sigue 1), no queda huérfana.

### uv run ruff check .
```
All checks passed!
```

### uv run python manage.py makemigrations --check --dry-run
```
No changes detected
```

### uv run pytest apps
```
118 passed in 2.34s
```

## Deuda / seguimientos
- El recon §3 menciona metadatos de apoyo (`physicalStoreId` interno `18503`, `marketId 10`)
  que el modelo `RetailerLocation` no almacena. La spec lo deja explícitamente fuera de F028;
  si la corrida en vivo (F027) los necesita, será un ajuste posterior del adapter/modelo, no del seed.
- La clave de lookup `(retailer, name)` no está respaldada por un `unique_together` en el modelo;
  funciona porque el seed usa nombres únicos por retailer. Si en el futuro se siembran varias
  tiendas HD con riesgo de nombre repetido, conviene una constraint o volver a un external_id estable.
