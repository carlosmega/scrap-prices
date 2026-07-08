# impl F033 — backend (búsqueda en vivo bajo demanda, live-on-miss)

## Spec aplicada y decisiones

Spec: `specs/F033-busqueda-en-vivo.md`, criterios backend completos. Decisiones:
(1) gatillo (TTL/cooldown/never/q<3) en `apps.catalog.services`, ejecución en
`apps.scraping.services` — el router solo delega; (2) concurrencia con
`ThreadPoolExecutor` + `futures.wait(timeout=presupuesto)` en vez de
`asyncio.run(gather)`: `asyncio.run` ESPERA a los hilos abandonados al cerrar el
loop, así que el presupuesto de 25 s ("al vencer, responde con lo que haya") no
se cumpliría; el hilo rezagado termina solo y su ingestión queda en DB
(cache-through) — documentado en el docstring de `correr_busqueda_en_vivo`;
(3) cooldown POR retailer (el que corrió hace <15 min queda fuera; si ninguno
queda, `live=null`); los `skipped` (sin key / pausado / sin tienda) no abren
`ScrapeRun` ni gastan red; (4) el seed ahora deja una observación FRESCA por RP
(marker `raw_payload.fresh`, refrescada en sitio → idempotente): con datos
frescos la búsqueda sembrada NO dispara el vivo, que es lo que mantiene los
tests y el E2E 100 % offline (los términos e2e "varilla" y `1/2"` quedan frescos).

## Archivos creados

- `backend/apps/prices/migrations/0002_scraperun_search_term_scraperun_triggered_by.py`
  (migración de `ScrapeRun`: `search_term` null/blank + `triggered_by` default `command`).
- `backend/apps/catalog/tests/test_live_search.py` — 10 tests OFFLINE
  (MockTransport + golden fixtures): dispara-cuando-vacío e ingesta
  (`triggered_by="search"`, `search_term`), NO-dispara (frescos/never/q<3/
  cooldown-con-0-items), cooldown por retailer, 429→blocked+otro ok (1 sola
  petición, sin stacktrace en detail), Construrama sin key→skipped+HD sigue,
  retailer pausado→skipped, presupuesto→failed: timeout.
- `backend/conftest.py` — candado autouse: `build_live_adapter` parcheado a
  "explota"; NINGÚN test puede pegar a la red por el camino del vivo.

## Archivos modificados

- `backend/apps/prices/models.py` — `ScrapeRun.search_term`/`triggered_by`
  (+`TriggeredBy` choices; noqa DJ001 justificado: null = "sin término").
- `backend/apps/prices/admin.py` — columnas/filtro de auditoría del origen.
- `backend/config/settings.py` — `SEARCH_LIVE_TTL_HOURS` (24) /
  `SEARCH_LIVE_COOLDOWN_MINUTES` (15) / `SEARCH_LIVE_TIMEOUT_SECONDS` (25.0)
  env-overridables; DB de TEST SQLite en ARCHIVO (los hilos del vivo abren su
  propia conexión: el `:memory:` compartido da SQLITE_LOCKED entre escritores).
- `backend/apps/scraping/services.py` — `resolver_primary_location` (extraído
  del comando, spec), `abrir_corrida`/`_run_ingestion`/`ingest_*` con
  passthrough `search_term`/`triggered_by`, `build_live_adapter` (seam),
  `LiveRetailerOutcome`/`LiveRunReport`, `_skip_para`, `_correr_retailer`
  (nunca lanza; cierra adapter y conexiones del hilo), `correr_busqueda_en_vivo`.
- `backend/apps/scraping/management/commands/scrape.py` — el resolver delega en
  services (mismo mensaje de `CommandError`).
- `backend/apps/catalog/schemas.py` — `SearchOut`, `RawRetailerResultOut`
  (`retailer_product_id` UUID, `price` float, `status` Literal por spec),
  `LiveSearchInfoOut`, `LiveRetailerStatusOut`.
- `backend/apps/catalog/services.py` — `buscar` → `SearchOut` (BREAKING),
  `_buscar_canonicos` (lógica F015/F031 intacta), `_buscar_crudos` (sin
  canónico + matcheo acento-insensible + obs más fresca en zona + orden
  retailer→precio asc + tope 50), gatillo `_buscar_en_vivo_si_falta` +
  `_hay_datos_frescos` + `_en_cooldown` (término truncado a 200 consistente
  entre persistencia y consulta).
- `backend/apps/catalog/api.py` — `response=SearchOut`, param
  `live: Literal["auto","never"]="auto"`; sin ORM en el router.
- `backend/apps/core/services.py` — seed: captura FRESCA por RP
  (`_sembrar_observacion_fresca`, mismo precio vigente ×1.030) + crudo real
  sin matchear (amarrador Truper `0204000086` del fixture Algolia, brand
  TRUPER, sale_unit pieza, obs histórica + fresca $125.00, disponible).
- Tests actualizados por el BREAKING y la frescura del seed:
  `apps/catalog/tests/test_search.py` (shape `results/raw_results/live`,
  frescura en vez de fecha fija, `live=never` solo en la query sin datos),
  `apps/catalog/tests/test_detalle.py` (historial 8 puntos, fresca primero),
  `apps/core/tests/test_seed.py` (+1 RP sin matchear, fresca, idempotencia
  del marker, test nuevo del crudo), `apps/lists/tests/test_api.py`
  (snapshot toma la fresca), `apps/scraping/tests/test_services.py`
  (+resolver, +defaults/estampado de auditoría),
  `apps/scraping/tests/test_construrama.py` (comando sigue `command`).
- `backend/openapi.json` — regenerado (verificado sin drift contra el código).
- `frontend/src/lib/api/schema.d.ts` — regenerado con `pnpm gen:api`
  (verificado idéntico a re-generación limpia). ÚNICO toque en frontend.

## ¿Cambió el contrato OpenAPI?

**SÍ — BREAKING**: `GET /api/search` pasa de `SearchResultOut[]` a `SearchOut`
(`results` + `raw_results` + `live`) y gana el query param `live={auto|never}`.
`openapi.json` y `schema.d.ts` regenerados y sincronizados (Fase 5 sin drift).
OJO líder: `frontend` queda temporalmente ROTO de tipos (`tsc --noEmit` falla
en componentes que derivaban tipos de la respuesta-lista) — lo resuelve el
implementer-frontend; hay que lanzarlo antes de esperar `./init.sh` verde en
Fase 4.

## Output real de verificación

```
$ uv run ruff check .
All checks passed!

$ uv run python manage.py makemigrations --check --dry-run
No changes detected

$ uv run pytest -q
........................................................................ [ 38%]
........................................................................ [ 77%]
..........................................                               [100%]
186 passed in 1.29s

$ uv run lint-imports
Analyzed 100 files, 154 dependencies.
-------------------------------------
Routers (api) no importan models directamente; delegan en services KEPT
Contracts: 1 kept, 0 broken.
```

(186 = 171 baseline + 15 nuevos; la línea `186 passed in 1.29s` es de
`uv run pytest` sin `-q` de la misma sesión.)

## Deuda / seguimientos

- Deduplicación de búsquedas concurrentes multi-usuario: fuera de alcance
  (spec); el cooldown mitiga. Límite conocido.
- El hilo que excede el presupuesto sigue corriendo hasta terminar (escritura
  cache-through); en un proceso de larga vida es inocuo, pero si algún día se
  migra a workers efímeros conviene revisarlo.
- `ScrapeRun` con 0 items queda `failed` (regla F024) aunque el vivo lo reporte
  `ok` con `items_found=0`: mismatch semántico documentado en código; si
  molesta en Admin, considerar un status `empty` en una feature futura.
- La corrida del comando `scrape` no registra `search_term` (null): si se
  quisiera que el comando también alimente el cooldown del vivo, pasar el
  término ahí (decisión de producto, no tomada).
- E2E: los términos sembrados quedan frescos → offline garantizado; si la capa
  e2e añade búsquedas de términos SIN datos, debe usarse `live=never` en la UI
  o fijar `SEARCH_LIVE_TTL_HOURS` enorme en el env del webServer.
