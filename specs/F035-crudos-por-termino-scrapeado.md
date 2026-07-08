# F035 — Resultados crudos por término scrapeado (no por substring del nombre)

> SDD: la spec es el contrato. Si no está aquí, no existe.

## Contexto y objetivo

**Bug de uso real (2026-07-08):** el usuario busca "impermiabilizante" (con typo),
el vivo scrapea HD (28) y Construrama (9) y los ingesta — pero la app muestra
**0 crudos**. Causa raíz (diagnosticada): `_buscar_crudos` (F033) filtra los
`RetailerProduct` sin matchear por `raw_name` acento-insensible **CONTIENE** `q`.
El buscador de los retailers es tolerante a typos/fuzzy (devuelve productos
llamados "Impermeabilizante" para la query "impermiabilizante"), pero el filtro
local es literal → los nombres guardados no contienen el typo → 0 resultados.

Verificado: `q="impermiabilizante"` → 0 crudos; `q="impermeabilizante"` → 29 crudos
(los mismos 29 productos están en BD, sin canónico). También afecta frases cuyas
palabras no aparecen contiguas en el nombre.

**Objetivo:** que la sección de crudos muestre lo que los retailers realmente
devolvieron para la query — asociando cada producto al **término con que se
scrapeó** (que es exactamente la query del usuario, se la pasamos al adapter),
sin depender de que el nombre contenga el texto tecleado.

## Alcance

**Incluye (solo `backend/`):**
- **Modelo:** `PriceObservation.scrape_run` → FK a `ScrapeRun` (nullable,
  `on_delete=SET_NULL`), para saber bajo qué corrida/término se halló cada
  observación. Una migración.
- **Ingestión:** al crear cada `PriceObservation`, setear su `scrape_run` (tanto
  el camino en vivo como el del comando). El `ScrapeRun` ya trae `search_term`
  (F033); el término se normaliza (strip/casefold/acentos) al comparar.
- **Búsqueda (`_buscar_crudos`):** los crudos (RetailerProduct sin canónico en la
  zona) se seleccionan por **UNIÓN** de:
  (a) productos con una `PriceObservation` cuya `ScrapeRun.search_term`
      normalizado == `q` normalizado (en la zona) — **el fix**; y
  (b) el filtro actual por `raw_name` acento-insensible contiene `q` — se
      conserva para no regresar la relevancia por nombre.
  Dedup por producto, observación más fresca en la zona, orden retailer→precio
  asc, tope 50 (igual que hoy).

**No incluye:**
- Frontend (la UI ya renderiza `raw_results`; con más resultados, funciona igual).
- Full-text/fuzzy propio ni auto-match (rapidfuzz sigue en M5).
- Backfill retroactivo de observaciones viejas sin `scrape_run` (quedan en null;
  se cubren por el filtro (b) por nombre, o al re-scrapear).

## Criterios de aceptación

- [ ] **Modelo/migración:** `PriceObservation.scrape_run` (FK nullable a ScrapeRun,
      SET_NULL); `makemigrations --check` limpio tras generar+commitear.
- [ ] **Ingestión:** las `PriceObservation` creadas por el vivo y por el comando
      quedan con su `scrape_run` seteado (test lo asevera en ambos caminos).
- [ ] **Búsqueda (el fix):** con productos ingestados bajo `ScrapeRun.search_term
      ="impermiabilizante"` cuyos nombres dicen "Impermeabilizante",
      `buscar(q="impermiabilizante")` devuelve esos crudos (>0). Test offline que
      reproduce el escenario del bug (nombre ≠ término).
- [ ] **Sin regresión:** `buscar(q="impermeabilizante")` sigue devolviendo los
      crudos por nombre (filtro (b) intacto); dedup correcto cuando (a) y (b) se
      solapan (un producto no aparece dos veces).
- [ ] **Normalización del término:** el match de `search_term` es
      acento/case/espacio-insensible (mismo helper que la búsqueda por nombre).
- [ ] **Backend:** `pytest`, `ruff`, `makemigrations --check`, `lint-imports`
      limpios; tests OFFLINE (candado de red intacto).
- [ ] **Contrato:** sin cambios de schema (es lógica de selección, no de shape).
      Confirmar `openapi.json`/`schema.d.ts` sin drift.
- [ ] **Global:** `./init.sh` verde.

## Plan de verificación

```bash
cd backend && uv run ruff check . && uv run python manage.py makemigrations --check --dry-run && uv run pytest -q && uv run lint-imports
# reproducción del bug (debe pasar tras el fix): un test que ingesta un producto
# con raw_name "Impermeabilizante X" bajo search_term "impermiabilizante" y asevera
# que buscar("impermiabilizante") lo devuelve en raw_results.
```
Prueba de humo del humano: buscar "impermiabilizante" (o cualquier término con
typo/fuzzy que el retailer resuelva) → la sección de tiendas muestra resultados.

## Notas y decisiones abiertas

- El comando `scrape` sí setea `search_term` (F033 lo dejó en null para el comando;
  para que el filtro (a) funcione también con datos del comando, el comando debe
  pasar su `--category` como `search_term`). Incluirlo en esta feature (barato y
  coherente).
- Alternativa considerada y descartada: devolver, tras un run en vivo, los
  productos que el run ingestó en memoria (sin persistir asociación). Rechazada:
  no cubre el cache-hit (re-buscar el typo dentro del TTL volvería a 0). La FK
  persistente sí lo cubre.
- Observaciones viejas (pre-migración) quedan con `scrape_run=null`: se siguen
  encontrando por el filtro (b) por nombre; no se hace backfill.
