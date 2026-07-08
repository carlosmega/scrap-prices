# impl_F035_backend — Resultados crudos por término scrapeado

Spec aplicada: `specs/F035-crudos-por-termino-scrapeado.md`.

## Spec aplicada y decisiones (≤5 líneas)
- Nueva FK `PriceObservation.scrape_run` (nullable, `SET_NULL`, `related_name="observations"`); migración `0003` commiteable junto al modelo.
- Ingestión: `_run_ingestion` liga cada `PriceObservation` a su `run` — cubre vivo (F033) y comando en un solo punto (ambos pasan por ahí); no hubo que threadear un parámetro nuevo porque el `run` ya es local al núcleo.
- Comando `scrape`: pasa `--category` como `search_term` del `ScrapeRun` (paga la deuda de F033; `triggered_by` sigue en default `command`).
- `_buscar_crudos`: UNIÓN de (a) RP sin canónico con observación en la zona bajo una corrida cuyo `search_term` normalizado == `q` y (b) el filtro por `raw_name`. Reusa `_normalizar` (acento/case + `.strip()`) en ambos lados. Dedup por construcción (se itera cada RP candidato una vez; se incluye si a O b). Shape de respuesta intacto.
- No toqué `_hay_datos_frescos` (fuera de alcance; el cooldown ya evita martillar el typo). El seed sigue con `scrape_run=null` (sin backfill, como dice la spec).

## Archivos creados/modificados (solo `backend/`)
Modificados:
- `backend/apps/prices/models.py` — campo `scrape_run` en `PriceObservation`.
- `backend/apps/scraping/services.py` — `scrape_run=run` en el `PriceObservation.objects.create` de `_run_ingestion`.
- `backend/apps/scraping/management/commands/scrape.py` — `ingest(..., search_term=category)` en `_ejecutar_ingestion`.
- `backend/apps/catalog/services.py` — helper `_rp_ids_por_termino_scrapeado` + `_buscar_crudos` por UNIÓN (el fix); docstrings.
- `backend/apps/scraping/tests/test_command_scrape.py` — test nuevo: comando liga observaciones a su `ScrapeRun` con `search_term=--category`.
- `backend/apps/scraping/tests/test_construrama.py` — assert actualizado: la corrida del comando ahora estampa `search_term="varilla"` (antes `is None`, deuda F033).
- `backend/apps/catalog/tests/test_live_search.py` — test nuevo (observaciones del vivo ligadas a su run) + assert de crudos actualizado a la UNIÓN F035 (el vivo bajo "alambre" ya expone todo lo scrapeado bajo ese término, no solo los nombres que dicen "alambre").

Creados:
- `backend/apps/prices/migrations/0003_priceobservation_scrape_run.py` — `AddField` scrape_run (FK nullable, SET_NULL, related_name observations).
- `backend/apps/catalog/tests/test_crudos_por_termino.py` — reproducción del bug (typo) + regresión por nombre + dedup + normalización acento/case/espacio + término ajeno no arrastra. OFFLINE (`live="never"`, sin red).

## ¿Cambió el contrato OpenAPI?
**NO.** Es lógica de selección, no de shape. Verificado: reexporté el schema y es byte-idéntico a `backend/openapi.json`; `git status` muestra `openapi.json` sin modificar. No corrí `pnpm gen:api` (no procede).

## Output REAL de las verificaciones

`uv run ruff check .`
```
All checks passed!
```

`uv run python manage.py makemigrations --check --dry-run`
```
No changes detected
```

`uv run pytest -q` (cola)
```
........................................................................ [ 34%]
........................................................................ [ 69%]
...............................................................          [100%]
207 passed in 1.44s
```

`uv run lint-imports` (cola)
```
Analyzed 102 files, 158 dependencies.
-------------------------------------

Routers (api) no importan models directamente; delegan en services KEPT

Contracts: 1 kept, 0 broken.
```

OpenAPI (chequeo de drift, no destructivo — exportado al scratchpad):
```
IDENTICO: el schema exportado coincide con backend/openapi.json en disco
(git status --porcelain backend/openapi.json → vacío)
```

## Deuda / seguimientos detectados
- `_hay_datos_frescos` sigue matcheando SOLO por nombre: tras el fix, re-buscar el typo dentro del TTL igual re-dispara el vivo hasta que aplique el cooldown (no vuelve a 0 crudos gracias a la FK, que era el objetivo). Fuera del alcance de F035; anotarlo si se quiere ahorrar corridas redundantes.
- Observaciones pre-F035 y las del seed quedan con `scrape_run=null` (sin backfill, por spec): se hallan por el filtro (b) por nombre o al re-scrapear.
- (a) normaliza `search_term` en memoria (SQLite MVP), consistente con el resto de la búsqueda; en Postgres/M5 esto migraría a unaccent/FTS.
