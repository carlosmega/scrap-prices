# impl F027 backend — comando `manage.py scrape`

## Spec aplicada y decisiones (máx. 5 líneas)
Spec: `specs/F027-cmd-scrape.md`. Comando delgado que envuelve la ingestión F025.
- **Registro de adapters**: `INGEST_REGISTRY = {"home-depot": services.ingest_homedepot}`; slug sin entrada (construrama) → aviso WARNING "adapter no disponible aún", `return` sin CommandError ni stacktrace.
- **--dry-run**: llama a `adapter.fetch_products_with_prices` (solo lectura) e imprime sku/nombre/precio/disponibilidad; NUNCA llama a `ingest_homedepot` → 0 escrituras garantizadas (no PriceObservation/RetailerProduct/ScrapeRun).
- **stop-if-blocked**: `RetailerBlockedError` (403/429) → `CommandError` con motivo, sin reintentar (el PoliteClient ya no reintenta bloqueos); aplica en ambos modos.
- Seam de testeo: `build_adapter(slug)` se parchea con `monkeypatch` para inyectar `HomeDepotAdapter` sobre `httpx.MockTransport` (sin red).

## Archivos creados/modificados
Creados (solo dentro de `backend/`):
- `backend/apps/scraping/management/__init__.py`
- `backend/apps/scraping/management/commands/__init__.py`
- `backend/apps/scraping/management/commands/scrape.py`
- `backend/apps/scraping/tests/test_command_scrape.py`

Sin cambios en modelos, schemas, rutas ni servicios existentes.

## ¿Cambió el contrato OpenAPI?
**NO.** No se tocaron schemas, rutas ni endpoints (es un management command). No se regeneró `openapi.json`; no procede disparar `pnpm gen:api`.

## Output REAL de las verificaciones

### `uv run ruff check .`
```
All checks passed!
```

### `uv run python manage.py makemigrations --check --dry-run`
```
No changes detected
```

### `uv run pytest apps/scraping -q`
```
.........................................                                [100%]
```

### `uv run pytest apps/scraping/tests/test_command_scrape.py -v` (detalle de los tests nuevos)
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.0, pluggy-1.6.0
django: version: 6.0.6, settings: config.settings (from ini)
rootdir: C:\scrap-prices\backend
configfile: pyproject.toml
plugins: anyio-4.13.0, django-4.12.0
collected 8 items

apps\scraping\tests\test_command_scrape.py ........                      [100%]

============================== 8 passed in 0.75s ==============================
```

### `uv run pytest -q` (suite completa del backend, para CHECKPOINTS)
```
........................................................................ [ 61%]
..............................................                           [100%]
```

### `uv run python manage.py scrape --help` (confirma los args)
```
usage: manage.py scrape [-h] --retailer RETAILER --zone ZONE
                        [--category CATEGORY] [--dry-run] [--version]
                        [-v {0,1,2,3}] [--settings SETTINGS]
                        [--pythonpath PYTHONPATH] [--traceback] [--no-color]
                        [--force-color] [--skip-checks]

Corre la ingestion de scraping respetuoso (F025) para un
retailer/zona/categoria. Con --dry-run hace el fetch real e imprime lo que
traeria sin escribir en la BD.

options:
  -h, --help            show this help message and exit
  --retailer RETAILER   Slug del retailer a scrapear (p.ej. home-depot).
  --zone ZONE           Slug de la zona interna a scrapear (p.ej. monterrey-metro).
  --category CATEGORY   Termino/categoria a buscar (default: varilla).
  --dry-run             Fetch real e imprime lo que traeria, SIN escribir en la BD.
  ...
```
(Args confirmados: `--retailer` requerido, `--zone` requerido, `--category` default `varilla`, `--dry-run` flag. El mojibake de acentos en `--help` es solo el encoding cp1252 de la consola Windows; el código fuente es UTF-8 correcto.)

## Tests (offline, sin red real) — cobertura de criterios de aceptación
- `test_dry_run_imprime_y_no_escribe`: imprime 4 productos, conteos de PriceObservation/RetailerProduct/ScrapeRun sin cambios.
- `test_corrida_real_crea_observations_y_run_ok`: crea 4 PriceObservation + 4 RetailerProduct, ScrapeRun ok (items_found=4).
- `test_retailer_inexistente_command_error` / `test_zona_inexistente_command_error` / `test_sin_location_primaria_command_error`: CommandError claro.
- `test_slug_sin_adapter_avisa_sin_reventar`: construrama → "no disponible aún", 0 corridas, sin excepción.
- `test_429_reporta_bloqueo_y_sale_con_error_sin_evadir` y `test_429_en_dry_run_tambien_reporta_bloqueo`: MockTransport 429 → CommandError "stop-if-blocked", una sola petición (`calls["n"] == 1`), 0 escrituras.

## Deuda / seguimientos
- El comando reutiliza `fetch_products_with_prices` para el dry-run (solo lectura). Cuando F026 sume el adapter de Construrama, basta añadir su entrada en `INGEST_REGISTRY` y el branch en `build_adapter`; el flujo del comando no cambia.
- `build_adapter` tiene un branch por slug (hoy solo `home-depot`); si crecen los retailers conviene moverlo a un registro de factories paralelo a `INGEST_REGISTRY`. No bloqueante para F027.
- Corrida con red real (HD en vivo) queda para el entorno del humano, según el plan de verificación de la spec; aquí todo es offline.
```
