# F024 — Infraestructura de scraping (adapters, rate-limit, retries, politeness)

> Milestone M2. PRD §9.3 (interfaz de adapters), §2.3 (guardrails), RNF4/RNF5.
> Base común sobre la que se montan los adapters por retailer (F025 HD, F026 Construrama).

## Contexto y objetivo
Crear la base del subsistema de scraping con los **guardrails cableados en código**
(no como buena voluntad): cliente HTTP respetuoso, rate-limit por dominio, reintentos
con backoff, y **detención ante bloqueo** (nunca evadir defensas). Todo testeable
**offline** (sin red real); los adapters concretos llegan en F025/F026.

## Alcance
**Incluye (app `apps/scraping/`):**
- **`BaseRetailerAdapter`** (Protocol/ABC) con la interfaz del PRD §9.3:
  `list_products(category, location)`, `get_price(product, location)`,
  `set_zone(location)`. Dataclasses normalizadas `RawProduct` / `RawPrice`
  (sku, raw_name, price Decimal, currency, is_available, source, captured_at, raw_payload).
- **Cliente HTTP respetuoso** (`httpx`): 
  - **User-Agent honesto** configurable (`SCRAPER_USER_AGENT`, default que identifica
    a ConstruScan + contacto), NUNCA un UA que finja ser otra cosa para engañar.
  - **Rate-limit por dominio**: delay mínimo configurable (`SCRAPER_MIN_DELAY_SECONDS`,
    default conservador ≥ crawl-delay) + semáforo de concurrencia por dominio.
  - **Reintentos** con `tenacity` (backoff exponencial) SOLO para errores transitorios
    (timeouts, 5xx, errores de red).
  - **`stop-if-blocked` (NO evasión):** si la respuesta es `403`/`429` o un challenge/
    captcha → lanza `RetailerBlockedError` y se DETIENE. No reintenta para “forzar”, no
    rota identidad, no resuelve captcha, no falsea fingerprint. El llamador marca el
    retailer `non_viable` (guardrail §2.3.1/2.3.7).
- Helper de `ScrapeRun` (abrir/cerrar corrida con status ok/partial/failed, items, errors).
- Config desde settings/env (UA, delay, timeout, concurrencia).

**No incluye:** adapters concretos (F025/F026); ingestión real a la DB desde red;
Celery beat scheduling (M5); cualquier técnica de evasión/disimulo (explícitamente fuera).

## Criterios de aceptación
- [ ] **Backend:** `BaseRetailerAdapter` + dataclasses + cliente respetuoso en `apps/scraping/`.
- [ ] **Backend:** el rate-limiter **espera** el delay mínimo entre peticiones al mismo
      dominio (test con reloj/mocked sleep lo demuestra).
- [ ] **Backend:** `tenacity` reintenta un 5xx/timeout transitorio y luego tiene éxito (test).
- [ ] **Backend:** ante `403`/`429`/challenge el cliente lanza `RetailerBlockedError` y
      **NO reintenta indefinidamente ni intenta evadir** (test lo verifica).
- [ ] **Backend:** UA honesto por defecto; configurable por env. Cero código de
      disimulo/fingerprint/captcha (grep lo confirma).
- [ ] **Backend:** todo testeado **sin red real** (httpx mockeado / transport fake);
      `uv run pytest` y `ruff` verdes; `makemigrations --check` limpio (sin modelos nuevos,
      salvo que el helper de ScrapeRun requiera algo — reusar el modelo de F008).
- [ ] No cambia el contrato OpenAPI (sin endpoints).

## Plan de verificación
```bash
cd backend && uv run ruff check . && uv run pytest apps/scraping -q
uv run python manage.py makemigrations --check --dry-run
./init.sh   # verde
```

## Notas y decisiones abiertas
- **Ética cableada:** este módulo es donde los guardrails del PRD §2.3 dejan de ser
  prosa y se vuelven código (UA honesto, rate-limit, stop-if-blocked). Los adapters
  (F025/F026) heredan eso; ninguno implementa evasión.
- La **corrida en vivo** (red real) se ejecuta en el entorno del humano, no en CI/arnés;
  los tests aquí son 100% offline.
- `source` (`xhr`/`html`/`playwright`) lo fija cada adapter; para HD/Construrama (Algolia)
  será `xhr`.
