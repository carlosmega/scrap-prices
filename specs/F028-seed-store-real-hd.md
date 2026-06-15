# F028 — Seed: código real de la tienda HD de Monterrey (external_id 1333)

> Pequeño fix para que la corrida real de F027 (`manage.py scrape`) pegue a la
> tienda correcta de Home Depot. El recon F010 (`docs/recon/homedepot.md` §3)
> identificó la tienda de Monterrey: `external_id = 1333` (el valor que HD acepta
> como `physicalStoreId` para precio). El seed (F013) usa un placeholder `store-2034`.

## Contexto y objetivo
El comando `scrape` usa `RetailerLocation.external_id` como `physicalStoreId`. Con el
placeholder, la corrida real consultaría una tienda inexistente. Cambiar el seed al
código real desbloquea la prueba en vivo.

## Alcance
**Incluye (backend, `apps/core/services.py::seed_demo`):**
- La `RetailerLocation` de Home Depot en Monterrey usa `external_id="1333"` (no `store-2034`).
  Conservar `name`/`city`/`state` (Monterrey, NL). Sigue idempotente.
- Ajustar cualquier test que asevere `store-2034`.

**No incluye:** cambios al adapter (F025) ni a la URL (ya manda `physicalStoreId`); el id
interno `18503`/`marketId 10` del recon NO se almacenan (el modelo `RetailerLocation` no
tiene esos campos; `external_id=1333` es lo que usa el adapter). Construrama sin cambios.

## Criterios de aceptación
- [ ] **Backend:** tras `seed`, la `RetailerLocation` de HD en `monterrey-metro` tiene
      `external_id="1333"`; el `ZoneLocationMap` primario sigue apuntando a ella.
- [ ] **Backend:** seed sigue **idempotente** (2ª corrida no duplica). Test lo verifica.
- [ ] **Backend:** `ruff`/`pytest` verdes; `makemigrations --check` limpio; contrato sin cambios.

## Plan de verificación
```bash
cd backend && uv run python manage.py seed && uv run pytest apps -q
uv run python manage.py shell -c "from apps.geo.models import RetailerLocation; print(RetailerLocation.objects.get(retailer__slug='home-depot', city='Monterrey').external_id)"  # -> 1333
./init.sh
```

## Notas
- Si la corrida en vivo revela que el endpoint de búsqueda necesita además `stLocId=18503`
  o `marketId=10` (recon §2.2), eso será un ajuste posterior del adapter (no de esta feature).
