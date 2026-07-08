# F034 — Fix: URL de ficha de Home Depot (usar `seo.href`, no `/p/{sku}`)

> SDD: la spec es el contrato. Si no está aquí, no existe.

## Contexto y objetivo

**Bug reportado por el humano (2026-07-08, uso real):** al abrir la ficha de un
producto de Home Depot desde la búsqueda, la app manda a
`https://www.homedepot.com.mx/p/{sku}` (p.ej. `/p/109754`) y HD devuelve **404**.

Causa raíz (diagnosticada con probe en vivo, HD ToS aprobado):
- La ingestión HD **adivina** la URL: `apps/scraping/services.py:124` →
  `f"{HOMEDEPOT_BASE_URL}/p/{raw_price.sku}"`. Ese patrón NO existe en HD.
- El XHR de HD **sí trae el slug real** en `content["seo"]["href"]`
  (p.ej. `/p/uniblock-cemento-gris-uniblock-15kg-34758-109754`) — lo estábamos
  ignorando (el parser no lo lee; los golden fixtures venían recortados sin él).
- Verificado en vivo: `https://www.homedepot.com.mx{seo.href}` → **HTTP 200**;
  `/p/{sku}` → **404**. Además `GET /search?q={sku}` → **200** y el buscador de HD
  encuentra el producto por su SKU (fallback válido).

Afecta tanto la sección de resultados crudos (F033) como los enlaces a la ficha
del retailer en el detalle de producto (F016/F021). Solo Home Depot; Construrama
ya usa su `url_es_mx_string` real (correcto).

## Alcance

**Incluye (solo `backend/`):**
- `parse_homedepot` extrae `content["seo"]["href"]` (relativo) y lo expone en
  `RawProduct.url`.
- Ingestión HD usa esa URL (absoluta `HOMEDEPOT_BASE_URL + href`) en vez de
  `/p/{sku}`. **Fallback** si falta `seo.href`: `HOMEDEPOT_BASE_URL + "/search?q=" + sku`
  (verificado 200), nunca el `/p/{sku}` roto.
- La ingestión **refresca** `RetailerProduct.url` en productos ya existentes (no
  solo al crear), para que una nueva búsqueda/scrape corrija las filas viejas con
  URL mala que hoy tiene la BD del humano.
- Golden fixtures HD actualizados con un `seo.href` realista (para cubrir la
  extracción); +fixture/caso sin `seo` (ejerce el fallback a `/search`).
- Seed (`apps/core/services.py`): los `RetailerProduct` demo de HD dejan de usar
  `/p/{sku}`; usan un slug realista o el fallback `/search?q={sku}` (URL que abre).
- Tests: parser extrae `seo.href`; ingestión arma la URL absoluta correcta; el
  fallback a `/search` cuando falta `seo`; refresh de URL en re-ingestión.

**No incluye:**
- Cambios de frontend (la UI ya renderiza `RetailerProduct.url`; con la URL
  correcta funciona sin tocar nada).
- Construrama (su URL ya es real).
- Migración de datos retroactiva: las filas viejas se corrigen al re-scrapear/
  re-seed; no se escribe un data-migration one-off (el refresh en ingestión basta).

## Criterios de aceptación

- [ ] **Backend:** `parse_homedepot` pone en `RawProduct.url` el `seo.href` del
      contenido (relativo); test con fixture que lo incluye.
- [ ] **Backend:** la ingestión HD guarda `RetailerProduct.url` =
      `https://www.homedepot.com.mx` + `seo.href` (absoluta). Test lo asevera con
      el slug real (no `/p/{sku}`).
- [ ] **Backend:** sin `seo.href`, la URL cae al fallback
      `https://www.homedepot.com.mx/search?q={sku}` (test dedicado). Nunca `/p/{sku}`.
- [ ] **Backend:** re-ingestar un SKU ya existente **actualiza** su `url`
      (test: fila con URL vieja `/p/{sku}` → tras re-ingestión queda la buena).
- [ ] **Backend:** seed no genera URLs `/p/{sku}` para HD (grep en test o aserción).
- [ ] **Backend:** `uv run pytest`, `ruff`, `makemigrations --check`,
      `lint-imports` limpios. Tests offline (MockTransport); ninguno pega a la red.
- [ ] **Global:** `./init.sh` verde.

## Plan de verificación

```bash
cd backend && uv run ruff check . && uv run python manage.py makemigrations --check --dry-run && uv run pytest -q && uv run lint-imports
# demostración de la corrección de datos viejos (BD del humano):
uv run python manage.py seed   # o un scrape real: las URLs HD dejan de ser /p/{sku}
uv run python manage.py shell -c "from apps.catalog.models import RetailerProduct as R; print([r.url for r in R.objects.filter(retailer__slug='home-depot')[:5]])"
```
Prueba de humo del humano: buscar en la app un producto HD y abrir su ficha →
debe abrir la página real (200), no 404.

## Notas y decisiones abiertas

- `seo.href` ya viene relativo (`/p/...`); no anteponer doble slash. Sanitizar
  (strip) y validar que empiece con `/`; si no, fallback.
- El fixture nuevo debe reflejar la forma REAL: `content["seo"]["href"]`
  (anidado), no un campo plano.
- La BD local del humano (`db.sqlite3`) tiene URLs malas ya guardadas; se
  corrigen solas cuando vuelva a buscar ese término (el vivo re-ingesta con
  refresh) o al re-seed. No requiere acción manual del humano.
