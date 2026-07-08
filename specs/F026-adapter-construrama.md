# F026 — M2 ConstruramaAdapter (Algolia, respetuoso)

> SDD: la spec es el contrato. Si no está aquí, no existe. Si es ambiguo,
> se pregunta al humano ANTES de implementar, no después.

## Contexto y objetivo

Segundo retailer del MVP. Hoy solo Home Depot está en vivo; Construrama habilita
la **comparación cross-retailer real** (el corazón del PRD). El precio de
Construrama se sirve por **Algolia** (índice `construrama_mx`, campo
`OSS7_priceValue_mxn_double`), reconocido en F011 (`docs/recon/construrama.md`).
Este adapter consulta Algolia de forma **respetuosa** (evita el WAF Imperva del
host, §5 del recon), parsea los `hits[]` e ingesta a `PriceObservation`/`ScrapeRun`,
espejando el patrón de F025 (Home Depot).

**Gate legal:** el ToS/robots.txt de Construrama fue **APROBADO por el humano
(Carlos) el 2026-07-07** para acceso automatizado respetuoso. Esto levanta el
`paused` del recon §0. Se mantienen los guardrails: UA honesto, rate-limit por
dominio, sin evasión, `raw_payload` guardado, stop-if-blocked.

## Alcance

**Incluye:**
- `ConstruramaAdapter` implementando `BaseRetailerAdapter` (infra F024), usando el
  `PoliteClient` (httpx + rate-limit + tenacity + stop-if-blocked).
- **Parser puro** de la respuesta Algolia (`results[0].hits[]` → `RawProduct`/`RawPrice`),
  con **golden fixtures** sanitizados de la 2ª captura HAR (patrón F025).
- **Ingestión** a `RetailerProduct` (get_or_create) + `PriceObservation`
  (`source=xhr`) + `ScrapeRun`, reusando los servicios de F008/F025.
- Registro en la tarea Celery y en el comando `manage.py scrape`
  (`--retailer construrama`), incluyendo `--dry-run` (fetch real, 0 escrituras).
- **Seed** del `Retailer` Construrama + `RetailerLocation` de Monterrey con los
  parámetros de zona en `extra` (subpath `nuevo-leon`, city place_id, store-id del
  distribuidor y prefijo `OSS7` — todos de la 2ª captura), y `ZoneLocationMap` a
  la zona Monterrey Metro. Flip de `scraper_status` `paused → active`.

**No incluye (explícitamente fuera):**
- **Plan B Playwright** (§5 recon): solo si Algolia-directo resulta bloqueado por
  Imperva en corrida real → feature separada. Este adapter asume `source=xhr`.
- Fijar la zona en vivo vía `setStoresByCity` (se usan los params ya capturados).
- Auto-match de SKU (curación manual en Admin, MVP).
- Sitios de distribuidores Construrama independientes (fuera de `construrama.com`).

## Contrato (endpoint Algolia — confirmado del lado request en F011)

`POST https://njvy3eu5dw-dsn.algolia.net/1/indexes/*/queries`
Headers: `x-algolia-application-id: njvy3eu5dw`, `x-algolia-api-key: <search-key pública>`
(ambos obtenidos del HAR / `get/algolia`; la key NO se commitea).
Body (multi-query InstantSearch):
```json
{"requests":[{"indexName":"construrama_mx",
  "params":"query=varilla&hitsPerPage=N&page=0&filters=allCategories_string_mv:OSS7Category AND (OSS7_priceValue_mxn_double > 0)&userToken=cma-anonymous-..."}]}
```
Respuesta (Algolia estándar): `{ "results":[ { "hits":[ {...} ], "nbHits", "page", "nbPages" } ] }`.

**Campos de `hits[]` — CONFIRMADOS por probe en vivo (2026-07-07, 7 hits de "varilla" en store OSS7):**
| Dato en `RawProduct`/`RawPrice` | Campo Algolia | Notas |
| --- | --- | --- |
| `price` | `OSS7_priceValue_mxn_double` (Number, MXN) | precio de la zona OSS7. `priceValue_mxn_double` base = 0.0 → **ignorar** |
| `external_sku` | `code_string` (10 díg., ej. `"6000111693"`); `objectID`/`pk` de respaldo | |
| `raw_name` | `name_text_es_mx` (ej. `"Varilla Corrugada Grado 42 De 1/2” 9.15 M, Kilogramos"`) | |
| `url` | `https://www.construrama.com` + `url_es_mx_string` (relativa `/catalogo/.../p/{code}`) | |
| `brand` | `brand_string_mv` (array; **filtrar el token literal `"brands"`** → `"GENÉRICO"`/`"TRUPER"`) | |
| `is_available` | `inStockFlag_boolean` (hoy todos `false`); `stockLevelStatus_string`, `availabilityDescription_OSS7` (`"72 hrs"`) como extra | |
| `unit_raw` / `sale_unit` | **inferir del nombre**: `"Kilogramos"` → kg, `"Pieza"` → pieza (F031) | grado-42 9.15m por kg; lisas 12m por pieza |
| specs matching | del nombre: diámetro (`1/2"`,`3/8"`,`5/8"`,`3/4"`), grado (`42`/R42), largo (`9.15m`/`12m`) | Algolia no trae facets limpios de diámetro → parsear del nombre |

Meta de la respuesta: `results[0].{ hits[], nbHits, page, nbPages, hitsPerPage }`.
Confirmado: `currentStore=OSS7` (de `get/algolia`) es el prefijo de precio de Nuevo León/Monterrey.
**Ojo:** "varilla" también devuelve accesorios (ej. `"amarrador de varillas"`, pieza) → el matching **manual** en Admin decide cuáles mapean a canónicos de varilla.

## Criterios de aceptación

- [ ] **Backend:** `ConstruramaAdapter(BaseRetailerAdapter)` con `retailer_slug`
      y método que consulta Algolia vía `PoliteClient` (UA honesto, delay, tenacity,
      stop-if-blocked → `RetailerBlockedError`, sin evasión).
- [ ] **Backend:** parser **puro** (`hits[]` → `RawProduct`/`RawPrice`, precio Decimal),
      con **golden fixtures** de la 2ª captura; ignora hits sin precio (`> 0`).
- [ ] **Backend:** ingestión crea `RetailerProduct` (get_or_create por external_sku),
      `PriceObservation` (`source=xhr`, `raw_payload` = hit crudo) y `ScrapeRun`
      (`ok`/`partial`/`failed`, `items_found`).
- [ ] **Backend:** `manage.py scrape --retailer construrama --zone monterrey-metro
      --category varilla [--dry-run]` funciona; `--dry-run` hace fetch real e imprime
      con 0 escrituras.
- [ ] **Backend:** seed idempotente del `Retailer`/`RetailerLocation`/`ZoneLocationMap`
      de Construrama Monterrey (`extra` con nuevo-leon/place_id/store-id/OSS7);
      `scraper_status=active`.
- [ ] **Backend:** `uv run pytest` pasa con tests **offline** (MockTransport, patrón
      F025), incluyendo un test 429 → stop-if-blocked. `ruff`, `makemigrations --check`
      y arquitectura (api.py sin ORM) limpios.
- [ ] **Global:** `./init.sh` verde de punta a punta.

## Plan de verificación

```bash
cd backend
uv run ruff check . && uv run python manage.py makemigrations --check --dry-run
uv run pytest -q                    # tests offline del adapter + ingestión
uv run python manage.py seed
uv run python manage.py scrape --retailer construrama --zone monterrey-metro --category varilla --dry-run
# corrida real (red, respetuosa) tras validar el dry-run:
uv run python manage.py scrape --retailer construrama --zone monterrey-metro --category varilla
```
Luego: matchear los SKUs reales de Construrama a los canónicos en Admin y confirmar
`sale_unit`/`mass_kg` (F031) para que la comparación $/kg contra Home Depot sea real.

## Notas y decisiones abiertas

- **ToS: APROBADO 2026-07-07** (humano). Levanta el `paused` del recon §0.
- **Insumo requerido: RESUELTO (2026-07-07).** El HAR no guardó el body de Algolia
  (limitación de Chrome con XHR grandes), así que se hizo **UNA consulta respetuosa
  en vivo** a Algolia con la search key pública de `get/algolia` (App ID `NJVY3EU5DW`,
  índice `construrama_mx`, store `OSS7`, UA honesto, sin evasión). Respuesta cruda
  (7 hits reales) preservada en `docs/recon/har/algolia_varilla_response.json`
  (gitignored) → **fuente de los golden fixtures**.
- **Manejo de la search key:** es pública (search-only) pero **NO se commitea**. El
  adapter la lee de env (`CONSTRURAMA_ALGOLIA_SEARCH_KEY`) o de `get/algolia`; los
  tests son **offline** (MockTransport) y no la requieren. El fixture committeable en
  `backend/` debe ser sanitizado (solo `results[0].hits[]` de catálogo, sin headers/keys).
- **Riesgo técnico (recon §5):** Imperva. Plan A = Algolia directo (evita el host).
  Si en corrida real la search key está restringida por Referer/allowedSources o
  responde bloqueo → **NO forzar**; escalar a Plan B (Playwright) como feature aparte,
  o marcar `non_viable`.
- **Normalización (F031):** Construrama vende varilla por **kilogramo** (Home Depot por
  tonelada/pieza) → clave fijar `sale_unit`/`mass_kg` en Admin para comparar $/kg.
