# F029 — HomeDepotAdapter: params reales de búsqueda (profileName + marketId/stLocId)

> Fix descubierto en la **corrida real** del `--dry-run` (F027): el endpoint de
> búsqueda de HD devuelve 0 sin `profileName` + `marketId` + `stLocId` (id interno).
> Confirmado en vivo: con `profileName=HCL_V2_findProductsBySearchTermWithPrice`,
> `marketId=10` y `stLocId=18503` → 13 varillas con precio; sin ellos → `total:0`.

## Contexto y objetivo
El adapter (F025) arma la URL de búsqueda solo con `physicalStoreId` (= `external_id`
= 1333). La búsqueda real de HCL Commerce necesita además: el **perfil con precio**, y
los identificadores de tienda `marketId` (10) y `stLocId` (18503, **distinto** del
`external_id`/`physicalStoreId` 1333). Hay que poder almacenar esos params por tienda
y enviarlos.

## Alcance
**Incluye:**
1. **geo (`apps/geo/models.py`):** añadir a `RetailerLocation` un campo
   `extra = JSONField(default=dict, blank=True)` para params de routing específicos
   del retailer (no caben en los campos base). **Migración** generada y commiteada.
2. **seed (`apps/core/services.py`):** la `RetailerLocation` de HD Monterrey fija
   `extra = {"market_id": "10", "st_loc_id": "18503"}` (idempotente). (`external_id`
   sigue siendo `1333` = physicalStoreId.)
3. **adapter (`apps/scraping/homedepot.py`):** `_build_search_url` incluye
   `profileName=HCL_V2_findProductsBySearchTermWithPrice`, `limit`/`offset`, y
   `marketId`/`stLocId` leídos de `location.extra` (`market_id`/`st_loc_id`). Si faltan
   en `extra`, fallback razonable (omitir o usar physicalStoreId) — pero el seed los provee.

**No incluye:** Construrama; cambios al parser (el shape ya es correcto); endpoints/API.

## Criterios de aceptación
- [ ] **Backend:** `RetailerLocation.extra` (JSONField) + migración commiteada;
      `makemigrations --check` limpio tras generarla.
- [ ] **Backend:** tras `seed`, la location de HD Monterrey tiene
      `extra == {"market_id": "10", "st_loc_id": "18503"}`. Idempotente.
- [ ] **Backend:** test unit de `_build_search_url` (location con ese `extra`) → la URL
      contiene `profileName=HCL_V2_findProductsBySearchTermWithPrice`, `marketId=10`,
      `stLocId=18503`, `physicalStoreId=1333`, `searchTerm=varilla`, `limit`/`offset`.
- [ ] **Backend:** los tests offline existentes (parser, ingestión MockTransport, comando)
      siguen verdes; `ruff` limpio; contrato OpenAPI sin cambios.
- [ ] **(Confirmación en vivo, la hace el líder, no CI):** `scrape --dry-run` devuelve
      varillas reales (≈13) — ya validado el endpoint manualmente.

## Plan de verificación
```bash
cd backend && uv run python manage.py makemigrations && uv run python manage.py migrate
uv run python manage.py seed && uv run pytest apps -q && uv run ruff check .
./init.sh
# Confirmación en vivo (líder, red):
# uv run python manage.py scrape --retailer home-depot --zone monterrey-metro --category varilla --dry-run  -> ~13 productos
```

## Notas
- `extra` es genérico: Construrama (F026) lo usará para su distribuidor/ciudad.
- `stLocId` (18503) ≠ `external_id`/`physicalStoreId` (1333): son ids distintos de la
  misma tienda en HCL Commerce (recon F010 §3).
