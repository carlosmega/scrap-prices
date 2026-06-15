# impl_F024_backend — Infraestructura de scraping (adapters, rate-limit, retries, politeness)

Spec aplicada: `specs/F024-scraping-infra.md` (M2; PRD §9.3 interfaz, §2.3 guardrails).

## Decisiones (máx. 5 líneas)
- Cliente HTTP **síncrono** sobre `httpx` (en MVP las corridas son Celery secuenciales; sync = test determinista). `sleep`/`monotonic` inyectables → el rate-limit se verifica con reloj falso, sin esperas reales.
- **Guardrails cableados**: UA honesto desde settings, rate-limit por dominio (semáforo + delay reservado), reintentos `tenacity` SOLO para `TransientScrapeError` (timeout/5xx/red); bloqueo (`403`/`429`/challenge) → `RetailerBlockedError` que NO está en la política de retry (stop-if-blocked, no evasión).
- `RetailerBlockedError` NO hereda de `TransientScrapeError` a propósito: así nunca entra al backoff.
- Helper de `ScrapeRun` **reusa** el modelo de F008 (`apps.prices.models.ScrapeRun`); NO se creó modelo nuevo → cero migraciones.
- La detección de captcha/challenge es para **detenerse**, no para resolver/evadir (cero solving, cero rotación de identidad, cero fingerprint falso).

## Archivos creados
- `backend/apps/scraping/__init__.py`
- `backend/apps/scraping/apps.py` (ScrapingConfig)
- `backend/apps/scraping/exceptions.py` (`ScrapeError`, `TransientScrapeError`, `RetailerBlockedError`)
- `backend/apps/scraping/base.py` (`BaseRetailerAdapter` ABC, dataclasses `RawProduct`/`RawPrice`)
- `backend/apps/scraping/client.py` (`PoliteClient`, `build_polite_client`)
- `backend/apps/scraping/services.py` (`abrir_corrida`/`cerrar_corrida`, reusan ScrapeRun de F008)
- `backend/apps/scraping/tests/__init__.py`
- `backend/apps/scraping/tests/fakes.py` (`FakeRetailerAdapter` offline)
- `backend/apps/scraping/tests/test_base.py` (interfaz + dataclasses, 4 tests)
- `backend/apps/scraping/tests/test_client.py` (rate-limit, retries, stop-if-blocked, UA honesto, 12 tests)
- `backend/apps/scraping/tests/test_services.py` (helper ScrapeRun, 5 tests)

## Archivos modificados
- `backend/config/settings.py` (app `apps.scraping` en INSTALLED_APPS; settings `SCRAPER_USER_AGENT`, `SCRAPER_MIN_DELAY_SECONDS`, `SCRAPER_TIMEOUT_SECONDS`, `SCRAPER_MAX_CONCURRENCY_PER_DOMAIN`, `SCRAPER_MAX_RETRIES` leídos de env con defaults honestos/conservadores).
- `backend/pyproject.toml` + `backend/uv.lock` (`uv add httpx tenacity`).

## ¿Cambió el contrato OpenAPI?
**NO.** No se añadió ningún endpoint ni schema. Verificado regenerando a temp y `diff -q` contra `backend/openapi.json` → "CONTRATO SIN CAMBIOS". No requiere `pnpm gen:api`.

## Anti-evasión (verificado)
`grep -rinE "fingerprint|captcha|stealth|rotate" apps/scraping/` solo encuentra:
texto de docstrings que describen el guardrail (stop-if-blocked) y los marcadores
de **detección** de challenge para DETENERSE. Cero lógica de resolver captcha,
rotar UA/identidad, stealth o fingerprint falso. El UA default contiene
"ConstruScan" y los tests verifican que no contiene mozilla/chrome/safari/firefox/applewebkit.

## Output REAL de las verificaciones

### uv run ruff check .
```
All checks passed!
```

### uv run python manage.py makemigrations --check --dry-run
```
No changes detected
```

### uv run pytest apps/scraping -q
```
.....................                                                    [100%]
21 passed in 0.47s
```

### uv run pytest -q (suite completa, sin regresiones)
```
........................................................................ [ 73%]
..........................                                               [100%]
98 passed in 1.95s
```

### uv run lint-imports (contrato de capas)
```
Routers (api) no importan models directamente; delegan en services KEPT
Contracts: 1 kept, 0 broken.
```

## Deuda / seguimientos
- Cliente sync: si M5 (Celery beat) necesita scraping concurrente cross-dominio
  real, evaluar variante async (`httpx.AsyncClient` + `asyncio.Semaphore`). La
  interfaz de `BaseRetailerAdapter` no cambiaría.
- La heurística `_is_challenge_response` es conservadora y mínima (Cloudflare /
  marcadores de captcha en HTML). Los adapters concretos (F025/F026) pueden
  necesitar afinarla por retailer con golden fixtures; ningún ajuste debe
  introducir evasión.
- Falta el cableado adapter→ingestión (RawPrice → PriceObservation): llega con
  los adapters concretos F025/F026, fuera del alcance de F024.
```
