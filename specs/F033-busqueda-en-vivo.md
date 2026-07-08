# F033 — Búsqueda en vivo bajo demanda (live-on-miss, cache-through)

> SDD: la spec es el contrato. Si no está aquí, no existe. Si es ambiguo,
> se pregunta al humano ANTES de implementar, no después.

## Contexto y objetivo

**Pivote de producto decidido por el dueño (Carlos) el 2026-07-07**, que reemplaza
el "principio no negociable" del PRD §1 (scraping solo programado): *"el objetivo
es que genere un scraper que me traiga los precios del producto que estoy buscando
en esas tiendas (Home Depot y Construrama); entiendo que los buscará en vivo y que
puede tardar"*. Decisiones cerradas con el humano (AskUserQuestion 2026-07-07):

1. **Cuándo en vivo:** AUTO si faltan datos — la búsqueda consulta primero la BD
   (instantáneo); si no hay resultados frescos para ese término+zona, consulta
   ambos retailers EN VIVO (~2–25 s), ingesta lo hallado (histórico + frescura) y
   lo muestra. Repetir la búsqueda sirve de la BD.
2. **Resultados nuevos:** CRUDOS POR TIENDA — además de los canónicos comparados
   ($/kg, F031), la búsqueda muestra una sección por retailer con los productos
   hallados aún sin matchear (nombre tal cual, precio nativo, disponibilidad,
   frescura, link a la ficha). La comparación cross-retailer se habilita al
   curarlos en Admin (matching manual, PRD D1).

Los guardrails NO cambian: UA honesto, rate-limit por dominio, tenacity solo
transitorios, **stop-if-blocked sin evasión**, `raw_payload` auditado, ToS de
ambos retailers aprobado por el humano.

## Alcance

**Incluye:**
- **Backend:** orquestador de búsqueda en vivo (ambos retailers concurrentes,
  fallo de uno no tumba al otro), gatillo por cobertura/frescura con cooldown,
  ingestión reutilizando `_run_ingestion`, contrato de `/api/search` extendido
  (resultados canónicos + crudos + info de la corrida en vivo), campos nuevos en
  `ScrapeRun` (+migración), settings con TTL/cooldown/timeout.
- **Frontend:** estados de carga para búsqueda larga, sección "resultados de las
  tiendas (sin comparar)" agrupada por retailer, badge de corrida en vivo,
  agregar-a-cotización desde resultados crudos.
- **E2E:** flujo con datos sembrados (SIN red a retailers).

**No incluye (explícitamente fuera):**
- Auto-match (rapidfuzz) — sigue siendo M5; el matching continúa manual en Admin.
- Celery/broker (la corrida en vivo es síncrona dentro del request; el humano
  aceptó la latencia).
- Deduplicación de búsquedas concurrentes multi-usuario (MVP single-user; el
  cooldown mitiga; anotar como límite conocido).
- Playwright plan-B para Construrama (si Imperva bloquea Algolia en vivo, el
  retailer se reporta `blocked` y se sigue: feature aparte).

## Contrato API

`GET /api/search?q=&zone_id=&sort={price|name}&live={auto|never}` (default `live=auto`)

**BREAKING (respuesta pasa de lista a objeto):**

| Schema | Campos |
| --- | --- |
| `SearchOut` | `results: list[SearchResultOut]` (canónicos, igual que hoy) · `raw_results: list[RawRetailerResultOut]` · `live: LiveSearchInfoOut \| null` (`null` si no se disparó) |
| `RawRetailerResultOut` | `retailer_slug`, `retailer_name`, `retailer_product_id (UUID)`, `external_sku`, `raw_name`, `url \| null`, `brand \| null`, `sale_unit \| null`, `price (float)`, `currency`, `is_available (bool)`, `captured_at (datetime)` |
| `LiveSearchInfoOut` | `triggered (bool)`, `duration_ms (int)`, `retailers: list[LiveRetailerStatusOut]` |
| `LiveRetailerStatusOut` | `retailer_slug`, `status: "ok"\|"failed"\|"blocked"\|"skipped"`, `items_found (int)`, `detail \| null` (motivo breve; sin stacktraces) |

Reglas de `raw_results`: solo `RetailerProduct` **sin** canónico asignado
(`canonical_product` null), cuyo `raw_name` matchee `q` acento-insensible
(reusar el helper de la búsqueda actual), con su observación más fresca en la
zona; orden por retailer y luego precio asc; tope 50. Los matcheados ya salen
en `results` — no duplicar.

**Gatillo del vivo (servicio, no en el router):**
- `live=never` → nunca. `q` normalizado (strip/lower); si `len(q) < 3` → nunca.
- Se dispara si para `q`+zona no hay NINGUNA observación (canónica o cruda) más
  fresca que `SEARCH_LIVE_TTL_HOURS` (default 24, env-overridable), **y** no hay
  un `ScrapeRun` de ese `search_term`+zona+retailer más reciente que
  `SEARCH_LIVE_COOLDOWN_MINUTES` (default 15) — el cooldown evita martillar
  términos sin resultados ("asdfgh") y aplica aunque la corrida haya hallado 0.
- Presupuesto total `SEARCH_LIVE_TIMEOUT_SECONDS` (default 25); al vencer, se
  responde con lo que haya (retailer lento → `failed: timeout`).
- Retailers `scraper_status != active` o sin credencial (Construrama sin
  `CONSTRURAMA_ALGOLIA_SEARCH_KEY`) → `skipped` con motivo, sin romper el resto.
- Cada corrida en vivo crea su `ScrapeRun` por retailer con `search_term=q` y
  `triggered_by="search"` (comando existente → `triggered_by="command"`).

**Modelo:** `ScrapeRun` + `search_term (CharField null/blank)` +
`triggered_by (CharField, default "command")` — una migración.

## Criterios de aceptación

- [ ] **Backend:** buscar un término sin datos (p.ej. "cemento") con adapters
      mockeados (MockTransport) dispara la corrida en vivo de AMBOS retailers,
      ingesta (RetailerProduct+PriceObservation+ScrapeRun con `search_term` y
      `triggered_by="search"`) y responde `raw_results` poblado + `live.triggered=true`.
- [ ] **Backend:** con datos frescos (seed) NO dispara vivo (`live=null`); con
      `live=never` tampoco; con `len(q)<3` tampoco; dentro del cooldown tampoco
      (aunque la corrida previa hallara 0).
- [ ] **Backend:** un retailer bloqueado (429→`RetailerBlockedError`) o caído no
      impide ingerir/responder el otro (`status="blocked"/"failed"` + el otro `"ok"`).
- [ ] **Backend:** Construrama sin search key → `skipped` con motivo claro y HD
      sigue. Todos los tests OFFLINE (MockTransport); ningún test pega a la red.
- [ ] **Contrato:** `openapi.json` regenerado + `pnpm gen:api` sin drift (Fase 5).
- [ ] **Frontend:** spinner con mensaje progresivo ("Buscando…" → tras ~1.5 s
      "Consultando Home Depot y Construrama en vivo, puede tardar unos segundos…").
      Sección "Resultados de las tiendas (sin comparar)" agrupada por retailer con
      nombre crudo, precio nativo + `sale_unit`, disponibilidad, frescura "hace X"
      y link a la ficha; estados vacío/error manejados; cero `any`; tipos SOLO
      generados.
- [ ] **Frontend:** badge de corrida en vivo cuando `live.triggered` (por retailer:
      ok N · bloqueado · omitido). "Agregar a cotización" funciona desde un
      resultado crudo (mismo POST de items con `retailer_product_id`).
- [ ] **E2E (sin red):** el seed añade ≥1 `RetailerProduct` SIN matchear con
      observación (p.ej. el "amarrador" real del fixture de Construrama) → buscar
      "varilla" muestra los canónicos comparados Y la sección cruda con ese ítem;
      agregarlo a la cotización desde ahí funciona. La suite E2E completa pasa.
- [ ] **Global:** `./init.sh --e2e` verde.

## Plan de verificación

```bash
cd backend && uv run ruff check . && uv run python manage.py makemigrations --check --dry-run && uv run pytest -q && uv run lint-imports
cd frontend && pnpm exec tsc --noEmit && pnpm lint && pnpm test:unit && pnpm gen:api && git diff --exit-code src/lib/api/schema.d.ts
./init.sh --e2e
# humo manual (opcional, red real, respetuoso): levantar dev y buscar "cemento"
```

## Notas y decisiones abiertas

- **PRD:** este pivote deja obsoleto el §1 "no negociable" y matiza RNF2 (<500 ms
  solo aplica a búsquedas servidas de BD). El líder lo anota aquí y en history;
  la edición del PRD queda a decisión del humano.
- La vista puede ser sync con `asyncio.run(gather(...))` interno (patrón del
  comando `scrape`) — no exige migrar el API a async.
- Extraer `_resolver_primary_location` del comando a `services` para reusarlo
  (comando y búsqueda comparten resolución de tienda primaria por retailer).
- El cliente HTTP del frontend no debe imponer timeout < 30 s al fetch de búsqueda.
