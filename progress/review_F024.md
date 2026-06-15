# review_F024 — Infraestructura de scraping (adapters, rate-limit, retries, politeness)

**Veredicto: APROBADO**

Spec: `specs/F024-scraping-infra.md` · CHECKPOINTS: Global + Backend + Higiene.
Feature de **capa única backend** (no toca contrato). Toda la verificación que
sigue la re-ejecuté yo; no acepté el output del implementer como evidencia.

---

## Criterios de aceptación (spec) → estado → evidencia

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | `BaseRetailerAdapter` (ABC §9.3) + dataclasses `RawProduct`/`RawPrice` | CUMPLE | `apps/scraping/base.py`: `BaseRetailerAdapter(ABC)` con `set_zone`/`list_products`/`get_price` (@abstractmethod); `RawProduct` y `RawPrice` (frozen, slots), `price: Decimal`. `test_base.py` (4 tests): ABC no instanciable + `price` Decimal. |
| 2 | Rate-limit: espera el delay mínimo entre peticiones al mismo dominio (reloj inyectado) | CUMPLE | `client.py::_wait_for_domain` usa `_monotonic`/`_sleep` inyectables. `test_rate_limit_espera_el_delay_entre_peticiones_mismo_dominio`: 1ª petición `clock.sleeps == []`, 2ª `clock.sleeps == [7.0]`. `test_rate_limit_no_mezcla_dominios_distintos`: dominios distintos no comparten delay. |
| 3 | `tenacity` reintenta un transitorio (timeout/5xx) y luego tiene éxito | CUMPLE | `_retrying()`: `retry_if_exception_type(TransientScrapeError)`. `test_reintenta_5xx_y_luego_tiene_exito` (calls 1→503, 2→200) y `test_reintenta_timeout_y_luego_tiene_exito` (ConnectTimeout→200). `test_5xx_persistente_agota_reintentos_y_lanza_transient`: `calls == 3` (no infinito). |
| 4 | **stop-if-blocked (CRÍTICO):** 403/429/challenge → `RetailerBlockedError`, NO reintenta indefinidamente; `RetailerBlockedError` NO está en la política de retry | CUMPLE | `exceptions.py`: `RetailerBlockedError(ScrapeError)` — NO hereda de `TransientScrapeError`. `client.py::_retrying()` solo reintenta `TransientScrapeError`; `_raise_for_block_or_transient` evalúa el bloqueo PRIMERO. Tests: `test_403_429_lanza_blocked_y_no_reintenta` (param 403/429, `calls == 1`), `test_challenge_captcha_lanza_blocked_y_no_reintenta` (`calls == 1`), `test_blocked_no_se_reintenta_aunque_max_retries_sea_alto` (max_retries=10, `calls == 1`). |
| 5 | UA honesto por defecto (identifica a ConstruScan, no finge navegador); configurable por env | CUMPLE | `settings.py`: `SCRAPER_USER_AGENT` default `"ConstruScan/0.1 (+https://construscan.example/contacto)"` leído de env. `test_user_agent_por_defecto_es_honesto`: contiene "ConstruScan" y NO contiene mozilla/chrome/safari/firefox/applewebkit. `test_user_agent_se_envia_en_la_peticion`: el header viaja en la petición. |
| 6 | Cero evasión (grep) — solo docstrings/detección-para-detenerse | CUMPLE | Grep abajo: todas las coincidencias son docstrings, marcadores de **detección** (`_is_challenge_response` solo RECONOCE para lanzar `RetailerBlockedError`), o asserts de test. Cero solving de captcha, cero rotación de identidad/UA, cero stealth, cero fingerprint falso. `BLOCKED_STATUS_CODES = {403,429}` se usa para detenerse, no para evadir. |
| 7 | Tests offline (MockTransport/fakes, ninguna URL real); `pytest apps/scraping` verde | CUMPLE | `test_client.py` usa `httpx.MockTransport` + `FakeClock` (sleep/monotonic falsos). `fakes.py::FakeRetailerAdapter` en memoria, sin httpx ni red. URLs son `*.example` servidas por el mock. `uv run pytest apps/scraping -v` → **21 passed**. |
| 8 | `ruff` limpio; `makemigrations --check` limpio (reusa ScrapeRun de F008, sin modelos nuevos) | CUMPLE | `uv run ruff check .` → "All checks passed!". `makemigrations --check --dry-run` → "No changes detected". `services.py` usa `apps.prices.models.ScrapeRun` (F008); `test_helper_no_crea_modelo_nuevo` asserta `_meta.app_label == "prices"`. No hay `models.py` ni migraciones en `apps/scraping/`. |
| 9 | No cambia el contrato OpenAPI (sin endpoints) | CUMPLE | `git status --short backend/openapi.json` → vacío (sin cambios). No existe `apps/scraping/api.py`. `init.sh` Fase 5 (contrato) VERDE sin cambios. |

## CHECKPOINTS

| Sección | Punto | Estado | Evidencia |
|---------|-------|--------|-----------|
| Global | `./init.sh` verde de punta a punta | CUMPLE | Output abajo: 31 ok / 0 fallos / 4 pendientes → VERDE. |
| Global | Solo la feature actual (F024) `in_progress`; ninguna otra cambió | CUMPLE | `feature_list.json`: F024 `in_progress`; `init.sh` Fase 1: "features in_progress: 1 (máximo 1)". |
| Global | Existe `progress/impl_F024_backend.md` con output real | CUMPLE | Presente; outputs coinciden con mi re-ejecución. |
| Backend | `uv run pytest` pasa; tests fallarían sin la implementación | CUMPLE | Full suite exit 0 (98 dots); regla "git stash mental": el test de bloqueo asserta `calls == 1` — si `RetailerBlockedError` entrara al backoff sería 3/10; el de rate-limit asserta `sleeps == [7.0]` — sin `_wait_for_domain` sería `[]`. |
| Backend | `makemigrations --check` limpio | CUMPLE | "No changes detected". |
| Backend | `ruff check` limpio | CUMPLE | "All checks passed!". |
| Backend | Lógica en `services.py`, no en routers | CUMPLE | Orquestación de corrida en `services.py`; no hay `api.py`. |
| Backend | `api.py` sin ORM (Fase 3 grep) | CUMPLE | No existe `apps/scraping/api.py`. Grep `*/api.py` solo halla `@router.delete(...)` en `lists/api.py` (decoradores de ruta, no ORM; archivo no tocado por F024). Fase 3 de `init.sh`: "routers (api.py) sin llamadas al ORM". |
| Backend | Si cambió el contrato: openapi.json regenerado | N/A | No cambió el contrato. |
| Higiene | `feature_list.json` JSON válido, ≤1 `in_progress` | CUMPLE | Fase 1 de `init.sh` lo valida (verde). |
| Higiene | Repo git inicializado (diff ejecutable) | CUMPLE | `git rev-parse` ok; Fase 0: "repositorio git inicializado". |

## Diff / capa (sin desbordes)

`git status --short`:
```
 M backend/config/settings.py
 M backend/pyproject.toml
 M backend/uv.lock
?? backend/apps/scraping/
?? progress/impl_F024_backend.md
```
Todo dentro de la capa permitida (backend: apps/scraping, config/settings.py,
pyproject/uv.lock) + `progress/`. `backend/openapi.json` NO cambió. Ningún
archivo de `frontend/` ni `e2e/` tocado.

## Grep anti-evasión (resultado explícito)

`grep -rinE "fingerprint|captcha|stealth|rotate|undetected|puppeteer-extra" backend/apps/scraping`:
```
client.py:13   docstring stop-if-blocked (NO evasión)
client.py:15   docstring "NO se rote identidad/UA, NO se resuelva captcha"
client.py:16   docstring "falsee fingerprint. Reintentar o disimular sería violar..."
client.py:50   docstring "_is_challenge_response: detectar para detenerse"
client.py:54   docstring "ante la duda, mejor detenerse"
client.py:64   markers = ("captcha", "are you a robot", ...)  → DETECCIÓN para lanzar RetailerBlockedError
client.py:188  docstring "no resuelve captcha, no evade"
exceptions.py:9,12,30,34  docstrings del guardrail
test_client.py:195,196,205,212  test de que un captcha → bloqueo (calls == 1)
(+ binarios .pyc del cache)
```
**Veredicto del grep: limpio.** Todas las coincidencias son (a) docstrings que
describen el guardrail, (b) marcadores de **detección para detenerse**
(`_is_challenge_response` solo lanza `RetailerBlockedError`, nunca resuelve), o
(c) asserts de test. NINGUNA lógica de resolver captcha, rotar identidad/UA,
stealth ni fingerprint falso. Confirmado leyendo `client.py`.

Grep ORM en `*/api.py`: sin `api.py` en scraping; sin ORM en routers.
Grep frontend `fetch(` fuera del cliente: VACÍO (F024 no toca frontend).

## Output REAL de mi corrida de `./init.sh`

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
  ✔ las 21 feature(s) 'done' tienen review APROBADO

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
EXIT: 0

Las 4 pendientes son esperadas para esta feature (jq/docker opcionales, infra
Postgres/Redis diferida en MVP-SQLite, E2E saltada en modo full). Cero fallos.

## Verificaciones directas re-ejecutadas

- `uv run ruff check .` → All checks passed! (exit 0)
- `uv run python manage.py makemigrations --check --dry-run` → No changes detected (exit 0)
- `uv run pytest apps/scraping -v` → 21 passed (exit 0)
- `uv run pytest -q` (full) → exit 0, sin regresiones (98 tests)
- `git status` / `git diff` → solo backend + progress; openapi.json intacto

---

**Conclusión:** Los nueve criterios de la spec CUMPLEN, los CHECKPOINTS aplicables
CUMPLEN, el grep anti-evasión está limpio, el diff no se sale de la capa backend,
el contrato no cambió, y `./init.sh` termina VERDE. **APROBADO.**
