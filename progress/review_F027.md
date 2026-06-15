# Review F027 — comando `manage.py scrape`

**Veredicto: APROBADO**

Capa única backend (no toca contrato OpenAPI). Re-ejecuté yo mismo `./init.sh`
(modo full), los tests de `apps/scraping`, `ruff`, `makemigrations --check` y
`scrape --help`; leí `scrape.py`, `services.ingest_homedepot`, el adapter HD y
el `PoliteClient`. No me fié del output pegado por el implementer: todo el
output de abajo es de mi propia corrida.

## Criterios de aceptación (specs/F027) → estado → evidencia

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | `--dry-run` (HTTP mockeado + golden fixture) **imprime** productos y **NO** crea `PriceObservation`/`RetailerProduct`/`ScrapeRun` | **CUMPLE** | `test_dry_run_imprime_y_no_escribe` (verde): captura `obs_antes/rp_antes/runs_antes`, asevera `count() == antes` para las 3 tablas y `"Productos que se traerían: 4"` + SKU `462843`. Confirmado en código: `_ejecutar_dry_run` llama `adapter.fetch_products_with_prices` (solo GET + parseo puro, sin ORM), **nunca** `ingest_homedepot`. Es estructuralmente imposible que escriba. |
| 2 | Sin `--dry-run` ingiere (crea `PriceObservation` + `ScrapeRun` ok) | **CUMPLE** | `test_corrida_real_crea_observations_y_run_ok` (verde): 4 `PriceObservation`, 4 `RetailerProduct`, `ScrapeRun.status == OK`, `items_found == 4`. `handle` delega en `INGEST_REGISTRY["home-depot"] = services.ingest_homedepot`. |
| 3 | retailer/zona inexistente o sin `RetailerLocation` → `CommandError` claro | **CUMPLE** | `test_retailer_inexistente_command_error` (match `"No existe un Retailer"`), `test_zona_inexistente_command_error` (`"No existe una Zone"`), `test_sin_location_primaria_command_error` (`"RetailerLocation primaria"`). Los 3 resolvers (`_resolver_retailer/_resolver_zone/_resolver_primary_location`) levantan `CommandError` con mensaje accionable, sin stacktrace. |
| 4 | slug `construrama` (sin adapter) → "no disponible aún", sin reventar | **CUMPLE** | `test_slug_sin_adapter_avisa_sin_reventar` (verde): `call_command` no levanta excepción, imprime `"no disponible aún"`, `ScrapeRun.count() == 0`. En código: `INGEST_REGISTRY.get(slug) is None` → `style.WARNING` + `return` (no `CommandError`, no stacktrace). |
| 5 | MockTransport **429** → reporta bloqueo y sale con error, **sin reintentar para evadir** | **CUMPLE** | `test_429_reporta_bloqueo_y_sale_con_error_sin_evadir` y `test_429_en_dry_run_tambien_reporta_bloqueo` (verdes): ambos esperan `CommandError` match `"stop-if-blocked"` y aseveran `calls["n"] == 1` (una sola petición). Confirmado en `client.py`: `BLOCKED_STATUS_CODES = {403, 429}` y `RetailerBlockedError` **no** está en `retry_if_exception_type` → propaga al primer intento. El dry-run variante también deja 0 escrituras. |
| 6 | `ruff`/`pytest` verdes; `makemigrations --check` limpio; contrato sin cambios | **CUMPLE** | Ver output abajo: `All checks passed!`, `No changes detected`, suite scraping y backend completa verdes. `backend/openapi.json` NO aparece en `git status` (no se tocó). |

## CHECKPOINTS.md punto por punto

**Global**
- `./init.sh` verde de punta a punta: **CUMPLE** (31 ok, 0 fallos, 4 pendientes esperados — jq/docker ausentes en MVP, Fase 2 Postgres diferida, Fase 6 E2E saltada en modo full).
- Exactamente F027 `in_progress`, ninguna otra cambió: **CUMPLE** (`feature_list.json`: F027 `in_progress`, resto `done`/`pending`; Fase 1 reporta `in_progress: 1`).
- `progress/impl_F027_backend.md` con output real por capa: **CUMPLE** (existe; sus números coinciden con mi re-ejecución).
- Cumple la spec criterio por criterio: **CUMPLE** (tabla de arriba).

**Backend**
- `uv run pytest` pasa, con tests nuevos que fallarían sin la implementación: **CUMPLE**. Los 8 tests nuevos aseveran comportamiento observable (conteos de filas, `CommandError`, `calls["n"]==1`); no son humo. El test (1) compara conteos antes/después: si el dry-run llamara a `ingest_homedepot`, fallaría.
- `makemigrations --check --dry-run` limpio: **CUMPLE** (`No changes detected`; el comando no toca modelos).
- `ruff check .` limpio: **CUMPLE** (`All checks passed!`).
- Lógica de negocio en `services.py`, no en routers: **CUMPLE**. El comando es delgado: resuelve entidades, elige adapter, reporta; la ingestión vive en `services.ingest_homedepot` y la cortesía/stop-if-blocked en `client.py`. Un management command no es un router de Ninja.
- `api.py` sin llamadas al ORM: **CUMPLE**. El grep solo arroja `@router.delete(...)` (decoradores de ruta HTTP en `lists/api.py`, líneas 92 y 149), que es exactamente el falso positivo que `init.sh` filtra; cero ORM real. F027 no toca ningún `api.py`.
- `corsheaders`/contrato: **N/A** (F027 no toca CORS ni contrato).

**Contrato:** N/A — la API no cambió. `backend/openapi.json` intacto; no procede `pnpm gen:api`.

**Frontend / E2E:** N/A — F027 es capa única backend.

**Higiene del arnés**
- `feature_list.json` JSON válido con ≤1 `in_progress`: **CUMPLE**.
- Repo git inicializado: **CUMPLE** (`git rev-parse --is-inside-work-tree` → `true`; Fase 0 verde).

## Diff / alcance (git)

`git status --porcelain` + `git ls-files --others`:

```
?? backend/apps/scraping/management/
?? backend/apps/scraping/tests/test_command_scrape.py
?? progress/impl_F027_backend.md
```

Archivos nuevos:
- `backend/apps/scraping/management/__init__.py`
- `backend/apps/scraping/management/commands/__init__.py`
- `backend/apps/scraping/management/commands/scrape.py`
- `backend/apps/scraping/tests/test_command_scrape.py`
- `progress/impl_F027_backend.md`

Todo dentro de la capa permitida (`backend/apps/scraping/management` + tests + `progress/`).
`git diff --name-only HEAD` vacío (no se modificaron archivos ya rastreados).
**`backend/openapi.json` NO cambió.** Cero evasión: el código no rota UA, no
reintenta bloqueos, no resuelve captchas (verificado en `client.py` y en el flujo
del comando, que solo propaga `RetailerBlockedError` como `CommandError`).

## "Git stash mental" (¿el test prueba algo?)

- Test (1) dry-run: si el comando llamara a `ingest_homedepot` en dry-run, los
  conteos cambiarían y la aserción `count() == antes` fallaría. Prueba real.
- Test (5) 429: si el cliente reintentara el bloqueo, `calls["n"]` sería > 1 y
  fallaría. Prueba el guardrail, no solo el happy path.
- Ningún test pega a URL real: todos construyen el adapter sobre
  `httpx.MockTransport` y parchean `build_adapter`; los tests de `CommandError`
  ni siquiera alcanzan el adapter (fallan en la resolución de entidades).

## Output REAL de mi corrida

### `./init.sh` (modo full)
```
── Fase 0 · Herramientas ──
  ✔ git disponible
  ✔ node disponible
  ◌ jq no encontrado (opcional / al bootstrapear su capa)
  ✔ uv disponible
  ◌ docker no encontrado (opcional / al bootstrapear su capa)
  ✔ pnpm disponible
  ✔ repositorio git inicializado

── Fase 1 · Invariantes del arnés ──
  ✔ existe CLAUDE.md
  ✔ existe AGENTS.md
  ✔ existe CHECKPOINTS.md
  ✔ existe feature_list.json
  ✔ existe specs/TEMPLATE.md
  ✔ existe progress/current.md
  ✔ existe progress/history.md
  ✔ existe docs/architecture.md
  ✔ existe docs/verification.md
  ✔ feature_list.json es JSON válido (array)
  ✔ features in_progress: 1 (máximo 1)
  ✔ todos los status son válidos
  ✔ hook guard-feature.sh ejecutable
  ✔ las 23 feature(s) 'done' tienen review APROBADO

── Fase 2 · Infraestructura (Postgres + Redis — opcional, migración futura) ──
  ◌ Docker no usado en MVP (backend corre con SQLite); infra Postgres/Redis diferida

── Fase 3 · Backend (Django + Ninja) ──
  ✔ uv sync (dependencias)
  ✔ ruff check
  ✔ migraciones al día (makemigrations --check)
  ✔ pytest
  ✔ arquitectura: routers (api.py) sin llamadas al ORM

── Fase 4 · Frontend (Next.js + Tailwind + shadcn) ──
  ✔ pnpm install
  ✔ tsc --noEmit
  ✔ lint
  ✔ tests unitarios (vitest)
  ✔ build de producción
  ✔ arquitectura: fetch solo en src/lib/api/client.ts

── Fase 5 · Contrato OpenAPI → tipos TS ──
  ✔ tipos TS sincronizados con backend/openapi.json

── Fase 6 · E2E (Playwright) ──
  ◌ saltada (usa ./init.sh --e2e para correrla)

════════ Resumen ════════
  ✔ 31 ok   ✘ 0 fallos   ◌ 4 pendientes
  VERDE — el arnés está en estado consistente.
```

### `uv run pytest apps/scraping/tests/test_command_scrape.py -v`
```
collected 8 items
apps\scraping\tests\test_command_scrape.py ........                      [100%]
8 passed in 0.81s
```

### `uv run pytest apps/scraping -q`
```
.........................................                                [100%]
```

### `uv run pytest -q` (suite backend completa)
```
........................................................................ [ 61%]
..............................................                           [100%]
(118 passed)
```

### `uv run ruff check .`
```
All checks passed!
```

### `uv run python manage.py makemigrations --check --dry-run`
```
No changes detected
```

### `uv run python manage.py scrape --help` (args confirmados)
```
options:
  --retailer RETAILER   Slug del retailer a scrapear (p.ej. home-depot).      [requerido]
  --zone ZONE           Slug de la zona interna a scrapear (p.ej. monterrey-metro). [requerido]
  --category CATEGORY   Término/categoría a buscar (default: varilla).
  --dry-run             Fetch real e imprime lo que traería, SIN escribir en la BD.
```
(El mojibake de acentos en consola es solo el encoding cp1252 de Windows; el
fuente es UTF-8 correcto. No es defecto.)

## Conclusión

Los 6 criterios de la spec CUMPLEN, todos los puntos aplicables de CHECKPOINTS
(Global + Backend + Higiene) CUMPLEN, el diff está dentro de la capa permitida,
el contrato no cambió y no hay rastro de evasión. El punto clave (dry-run = 0
escrituras) está garantizado tanto por el test como por la estructura del código
(usa el método de solo lectura del adapter, nunca la función de ingestión).

**Veredicto: APROBADO**
