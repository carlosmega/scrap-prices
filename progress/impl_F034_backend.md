# impl F034 backend — Fix URL de ficha de Home Depot (usar `seo.href`, no `/p/{sku}`)

## Spec aplicada y decisiones (máx. 5 líneas)

- Nuevo helper puro `homedepot_href(content)` en `parsers.py`: extrae `content["seo"]["href"]`, lo strip-ea y exige que empiece con `/`; si falta/mal formado → `""`.
- `parse_homedepot` puebla `RawProduct.url` con ese href relativo (nuevo campo `url` en el dataclass `RawProduct`, default `""`).
- Ingestión HD (`_homedepot_product_url`): `RetailerProduct.url = HOMEDEPOT_BASE_URL + seo.href`; si no hay href, fallback `HOMEDEPOT_BASE_URL + "/search?q={sku}"`. Nunca `/p/{sku}`. Además la re-ingestión **refresca** la url de filas ya existentes (get_or_create solo aplica defaults al crear → añadí `save(update_fields=["url","updated_at"])` cuando difiere).
- Seed HD (`core/services.py`, `_seed_pdp_url`): los RP demo de HD usan `/search?q={sku}` (no `/p/{sku}`); Construrama intacto (su `/...p/{code}` es real, fuera de alcance).
- Fixture `homedepot_varilla_482588.json` ampliado con `seo.href` real (anidado); `homedepot_varilla_batch.json` queda SIN `seo` para ejercer el fallback. Todo offline (MockTransport/fixtures); no toqué el candado de `conftest.py`.

## Archivos creados/modificados

Modificados (todos dentro de `backend/`):
- `backend/apps/scraping/base.py` — `RawProduct` gana el campo `url: str = ""` (href relativo del PDP).
- `backend/apps/scraping/parsers.py` — nuevo `homedepot_href(content)`; `parse_homedepot` puebla `RawProduct.url`.
- `backend/apps/scraping/services.py` — import de `homedepot_href`; nuevo `_homedepot_product_url(raw_price)`; `_get_or_create_retailer_product` usa la url real + fallback y **refresca** la url en re-ingestión; docstring de `ingest_homedepot` actualizado.
- `backend/apps/core/services.py` — nuevo `_seed_pdp_url(slug, base_url, external_sku)`; el loop del seed lo usa (HD → `/search?q={sku}`).
- `backend/apps/scraping/tests/fixtures/homedepot_varilla_482588.json` — añadido `"seo": {"href": "/p/varilla-corrugada-recta-r-42-1-12-metros-1-tonelada-482588"}`.
- `backend/apps/scraping/tests/test_parsers_homedepot.py` — tests: `parse_homedepot` extrae `seo.href` a `url`; sin `seo` deja `url==""`; parametrizado de `homedepot_href` (strip, sin seo, seo no-dict, href sin `/`, absoluto → "").
- `backend/apps/scraping/tests/test_homedepot.py` — tests de ingestión: url absoluta desde `seo.href` (con slug, no `/p/{sku}`); fallback a `/search?q={sku}` sin `seo`; **refresh** de url vieja `/p/{sku}` en re-ingestión (fila preexistente) + no duplica.
- `backend/apps/core/tests/test_seed.py` — test: HD no genera urls `/p/{sku}`; usa `/search?q={sku}`.

## ¿Cambió el contrato OpenAPI?

**No.** El cambio es de datos/ingestión (valor de `RetailerProduct.url`), no de schemas ni rutas Ninja. Verificado: `backend/openapi.json` NO aparece en `git status --porcelain` tras los cambios. No corrí `export_openapi_schema` (no aplica) y no hace falta `pnpm gen:api`.

## Output REAL de las verificaciones

Corridas desde `backend/`.

### `uv run ruff check .`
```
All checks passed!
```

### `uv run python manage.py makemigrations --check --dry-run`
```
No changes detected
```
(exit code 0)

### `uv run pytest -q`
```
........................................................................ [ 36%]
........................................................................ [ 72%]
........................................................                 [100%]
200 passed in 1.32s
```

### `uv run lint-imports`
```
Analyzed 100 files, 154 dependencies.
-------------------------------------

Routers (api) no importan models directamente; delegan en services KEPT

Contracts: 1 kept, 0 broken.
```

## Criterios de aceptación (uno por uno)

- [x] `parse_homedepot` pone `seo.href` (relativo) en `RawProduct.url` — test `test_parse_homedepot_extrae_seo_href_a_url`.
- [x] Ingestión HD guarda url absoluta = host + `seo.href` (slug real, no `/p/{sku}`) — `test_ingest_homedepot_url_absoluta_desde_seo_href`.
- [x] Sin `seo.href` → fallback `/search?q={sku}`, nunca `/p/{sku}` — `test_ingest_homedepot_fallback_a_search_sin_seo` + `test_parse_homedepot_sin_seo_deja_url_vacia`.
- [x] Re-ingestar un SKU existente ACTUALIZA su url (fila con `/p/{sku}` → la buena) — `test_ingest_homedepot_refresca_url_vieja_en_reingestion`.
- [x] Seed no genera urls `/p/{sku}` para HD — `test_seed_hd_no_genera_urls_p_sku`.
- [x] `pytest`, `ruff`, `makemigrations --check`, `lint-imports` limpios; tests offline (MockTransport/fixtures), ninguno pega a la red.

## Deuda / seguimientos

- El refresh de url en re-ingestión sobrescribe SIEMPRE con la url computada de esa corrida: si un run futuro trajera un content SIN `seo` para un SKU que antes sí lo tuvo, degradaría de slug real → `/search?q={sku}` (ambos responden 200; sin regresión funcional). Aceptado por la spec (fallback verificado 200).
- El fixture `homedepot_varilla_482588.json` incluye `seo` solo con `href` (única clave que consumimos); la respuesta real de HD trae más claves bajo `seo` (no relevantes para F034).
- Migración retroactiva de la BD del humano: fuera de alcance por decisión de la spec — las filas viejas se corrigen solas al re-scrapear/buscar en vivo (por el refresh) o al re-seed.
- No hice commits git (según lo pedido): archivos quedan listos en el working tree.
