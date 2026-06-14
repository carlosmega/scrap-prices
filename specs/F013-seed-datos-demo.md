# F013 — Seed de datos demo (Monterrey Metro · varilla)

> Milestone M3. Deriva del PRD §8 (modelo), §10 (zona piloto Monterrey Metro),
> §14 (categoría piloto: varilla). Foundational: da datos realistas para que la
> API (F014–F018) y la UI (F019–F022) sean demostrables **sin scraping real**.

## Contexto y objetivo
Mientras M1/M2 (scraping) están gated por recon humano + ToS, la app necesita
datos para construirse y verse. Esta feature crea un **management command
idempotente** que siembra el grafo mínimo del PRD para la zona piloto.

## Alcance
**Incluye:** `uv run python manage.py seed` (idempotente vía `get_or_create`) que crea:
- **Retailers:** Home Depot (`home-depot`, `pricing_model=zone_cookie`) y Construrama
  (`construrama`, `pricing_model=distributor_subpath`), ambos `scraper_status=active`.
- **RetailerLocation:** ≥1 por retailer en Monterrey (HD store + distribuidor Construrama con `subpath`).
- **Zone:** "Monterrey Metro" (`monterrey-metro`, `state=NL`, centroide aprox.).
- **ZoneLocationMap:** une la zona con cada location (`is_primary=True` la principal).
- **Category:** "Varilla".
- **CanonicalProduct:** 3–5 varillas (p.ej. 3/8" 12m, 1/2" 12m, 1/4" 6m) con `specs`
  (calibre/diámetro/longitud) y `unit=pieza`.
- **RetailerProduct:** 1 por (canónico × retailer), `match_status=manual` (matcheados),
  con `external_sku`, `raw_name`, `url`.
- **PriceObservation:** ≥2 por (retailer_product × zona) con distintos `captured_at`
  (para que haya historial y "última observación"), `price` Decimal, `currency=MXN`,
  `is_available=True`, `raw_payload={"seed": true}`.

**No incluye:** endpoints (F014+), UI, scraping. Datos curados a mano (no de retailers reales).

## Decisiones fijadas
- `PriceObservation.source`: usar un valor existente del choice (`xhr`) y marcar
  `raw_payload={"seed": true}` para distinguir el dato sembrado de uno real.
  (No se añade un choice nuevo: no tocar el modelo de F008.)
- Precios verosímiles pero ficticios (no se afirma que sean precios reales de HD/Construrama).
- Idempotente: correr `seed` dos veces no duplica filas ni falla.

## Criterios de aceptación
- [ ] `uv run python manage.py seed` corre limpio y es **idempotente** (2ª corrida no duplica).
- [ ] Tras seed existen: 2 Retailer, ≥2 RetailerLocation, 1 Zone "Monterrey Metro",
      ZoneLocationMap, 1 Category, ≥3 CanonicalProduct, RetailerProduct matcheados para
      ambos retailers, y ≥2 PriceObservation por retailer_product en la zona.
- [ ] Test (`@pytest.mark.django_db`) que ejecuta `call_command("seed")` y verifica los
      conteos + que `services.ultima_observacion` (F008) devuelve la más reciente; y que
      una 2ª llamada a `seed` no cambia los conteos (idempotencia).
- [ ] `ruff check` limpio; `makemigrations --check --dry-run` limpio (no nuevos modelos).
- [ ] No cambia el contrato OpenAPI (sin endpoints).

## Plan de verificación
```bash
cd backend
uv run python manage.py migrate
uv run python manage.py seed && uv run python manage.py seed   # idempotente
uv run pytest apps -q && uv run ruff check .
./init.sh   # verde
```

## Notas y decisiones abiertas
- El comando vive donde sea coherente (p.ej. `apps/<app>/management/commands/seed.py`).
  Si la lógica de armado crece, puede apoyarse en helpers de `services.py`.
- Cuando llegue M2, el scraping real produce `PriceObservation` con `source` real; el
  seed seguirá sirviendo para dev/tests/E2E (datos deterministas).
