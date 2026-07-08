# Review F034 — Fix URL de ficha de Home Depot (usar `seo.href`, no `/p/{sku}`)

**Veredicto: APROBADO**

Feature backend-only, sin cambio de contrato. Los 7 criterios de aceptación de
`specs/F034-fix-url-homedepot.md` se cumplen, verificados **re-ejecutando** yo
mismo las verificaciones (no acepté output pegado). `./init.sh` VERDE (33 ok /
0 fallos). Spot-check anti-teatro superado: los tests nuevos delatarían el bug
si se revirtiera la URL a `/p/{sku}`.

---

## 1. Verificaciones re-ejecutadas por el reviewer (output real)

Backend (`cd backend && ...`):

| Comando | Resultado | Exit |
|---|---|---|
| `uv run ruff check .` | `All checks passed!` | 0 |
| `uv run python manage.py makemigrations --check --dry-run` | `No changes detected` | 0 |
| `uv run pytest -q` | `200 passed` (72+72+56 puntos, sin fallos) | 0 |
| `uv run lint-imports` | `Contracts: 1 kept, 0 broken.` | 0 |

`makemigrations` limpio es correcto: `RetailerProduct.url` ya era campo del
modelo (F034 solo cambia el VALOR escrito), y el nuevo `RawProduct.url` es campo
de **dataclass** (`base.py:39` `url: str = ""`), no de modelo → sin migración.

## 2. Criterios de aceptación de la spec (uno por uno)

| # | Criterio | Estado | Evidencia (comando/archivo re-ejecutado) |
|---|---|---|---|
| 1 | `parse_homedepot` pone `seo.href` (relativo) en `RawProduct.url`; test con fixture que lo incluye | **CUMPLE** | `parsers.py:137` `url=homedepot_href(content)`; `homedepot_href` en `parsers.py:185-201` lee `content["seo"]["href"]` anidado, strip, exige `startswith("/")`. Fixture `homedepot_varilla_482588.json:11-13` trae `seo.href` anidado realista. Test `test_parse_homedepot_extrae_seo_href_a_url` PASA. Demo en vivo: `RawProduct.url = /p/varilla-corrugada-recta-r-42-1-12-metros-1-tonelada-482588` |
| 2 | Ingestión HD guarda `RetailerProduct.url = host + seo.href` (absoluta); test con slug real, no `/p/{sku}` | **CUMPLE** | `services.py:112-124` `_homedepot_product_url` → `f"{HOMEDEPOT_BASE_URL}{href}"`. Test `test_ingest_homedepot_url_absoluta_desde_seo_href` PASA (asevera el slug Y `!= /p/482588`). Demo en vivo: `URL absoluta = https://www.homedepot.com.mx/p/varilla-...-482588`; `¿coincide con /p/{sku} roto?: False` |
| 3 | Sin `seo.href` → fallback `/search?q={sku}` (test dedicado); nunca `/p/{sku}` | **CUMPLE** | `services.py:124` fallback `/search?q={sku}`. Tests `test_ingest_homedepot_fallback_a_search_sin_seo` + `test_parse_homedepot_sin_seo_deja_url_vacia` PASAN. Fixture `homedepot_varilla_batch.json` SIN `seo` (grep `"seo"` → 0). Demo en vivo (sin seo): `homedepot_href=''` → `URL = https://www.homedepot.com.mx/search?q=482588` |
| 4 | Re-ingestar un SKU existente ACTUALIZA su url (`/p/{sku}` viejo → la buena) | **CUMPLE** | `services.py:154-157` refresh explícito (`get_or_create` solo aplica defaults al crear; el bloque `if not created and rp.url != url: rp.save(update_fields=["url","updated_at"])` corrige en sitio). Test `test_ingest_homedepot_refresca_url_vieja_en_reingestion` PASA (crea fila con `/p/482588`, re-ingesta, asevera slug y no-duplicación) |
| 5 | Seed no genera URLs `/p/{sku}` para HD (grep/aserción) | **CUMPLE** | `core/services.py:130-140` `_seed_pdp_url` (HD → `/search?q={sku}`; Construrama conserva su `/p/{code}` real). Test `test_seed_hd_no_genera_urls_p_sku` PASA (asevera `f"/p/{sku}" not in url` y `== /search?q={sku}`) |
| 6 | `pytest`/`ruff`/`makemigrations`/`lint-imports` limpios; tests offline (MockTransport), ninguno pega a la red | **CUMPLE** | Ver §1 (todo verde). Candado de red `conftest.py:19-27` (`_explota` sobre `build_live_adapter`) INTACTO (git no lo modificó). Adapters HD sobre `httpx.MockTransport`/golden fixtures |
| 7 | Global: `./init.sh` verde | **CUMPLE** | `./init.sh` → `VERDE — 33 ok / 0 fallos / 2 pendientes`, exit 0 (output completo en §7) |

## 3. CHECKPOINTS.md (sección aplicable)

| Punto | Estado | Evidencia |
|---|---|---|
| `./init.sh` verde punta a punta | CUMPLE | 33 ok / 0 fallos (§7) |
| Exactamente la feature actual `in_progress`; ninguna otra cambió | CUMPLE | `feature_list.json`: `in_progress: ['F034']` (1 sola); init.sh Fase 1 `features in_progress: 1 (máximo 1)` |
| `progress/impl_<id>_<capa>.md` por capa, con output real | CUMPLE | `progress/impl_F034_backend.md` existe con outputs reales |
| Cumple la spec criterio por criterio | CUMPLE | §2 |
| **Backend:** pytest pasa; tests nuevos que fallarían sin la implementación | CUMPLE | 200 passed; anti-teatro §5 |
| **Backend:** `makemigrations --check` limpio | CUMPLE | `No changes detected` |
| **Backend:** `ruff check` limpio | CUMPLE | `All checks passed!` |
| **Backend:** lógica en `services.py`, no en routers | CUMPLE | Cambios en `services.py`/`parsers.py`/`base.py`/`core/services.py`; ningún `api.py` tocado |
| **Backend:** `api.py` sin ORM; regla de capas pasa | CUMPLE | `lint-imports` 1 kept 0 broken; init.sh Fase 3 `routers (api.py) sin llamadas al ORM`. (El grep amplio matchea solo decoradores `@router.delete(...)` de `lists/api.py`, no tocado por F034 — falso positivo del backup heurístico) |
| **Contrato:** si cambió la API, openapi regenerado | N/A / CUMPLE | El contrato NO cambió: `git status` de `backend/openapi.json` y `frontend/src/lib/api/schema.d.ts` VACÍO; init.sh Fase 5 `tipos TS sincronizados` |
| **Higiene:** `feature_list.json` válido ≤1 in_progress | CUMPLE | JSON válido (array), 1 in_progress (F034), 33 features |
| **Higiene:** toda feature `done` con review APROBADO | CUMPLE | init.sh Fase 1 `las 31 feature(s) 'done' tienen review APROBADO` |
| **Higiene:** repo git inicializado | CUMPLE | init.sh Fase 0 `repositorio git inicializado` |

Frontend / E2E: **N/A** — F034 es backend-only (la UI ya renderiza
`RetailerProduct.url`, sin tocar nada). Aun así init.sh Fases 4/5 quedaron verdes
(sin regresión: `tsc`, `lint`, vitest, `build`, contrato).

## 4. Arquitectura limpia (greps deterministas, no dependen de git)

- **ORM en routers** `grep -rnE "\.objects|\.save\(|\.filter\(|\.create\(|\.delete\(" backend/apps/*/api.py`:
  solo 2 hits, ambos `@router.delete("/lists/...")` en `lists/api.py` (rutas HTTP,
  NO ORM; archivo no tocado por F034). Sin ORM real en routers.
- **`/p/{sku}` para HD**: `grep -rn "/p/{" backend/apps` → todos los hits en
  `scraping/services.py`/`parsers.py` son **comentarios/docstrings**; el único
  `/p/{...}` de código productivo alcanzable es `core/services.py:140`
  (rama Construrama de `_seed_pdp_url`, tras el `if slug == "home-depot"` que
  retorna `/search`) y `core/services.py:121` (crudo Truper) — **ambos
  Construrama**, que la spec permite (su `/...p/{code}` es real). Ningún camino
  produce `/p/{sku}` para Home Depot (confirmado en vivo, §5).
- **`fetch(` fuera del cliente**: VACÍO (frontend no tocado; init.sh Fase 4
  `fetch solo en src/lib/api/client.ts`).
- **`: any` / `as any`**: N/A (frontend no tocado).

## 5. Spot-check anti-teatro (¿el test fallaría sin el fix?)

Demostración EN VIVO ejecutando las funciones REALES sobre el golden fixture
(`uv run python manage.py shell`), sin editar código:

```
SKU: 482588
RawProduct.url (relativo desde seo.href): /p/varilla-corrugada-recta-r-42-1-12-metros-1-tonelada-482588
URL ABSOLUTA ingerida (con seo): https://www.homedepot.com.mx/p/varilla-corrugada-recta-r-42-1-12-metros-1-tonelada-482588
¿coincide con el /p/{sku} roto?: False
homedepot_href(sin seo): ''
URL ABSOLUTA ingerida (sin seo, fallback): https://www.homedepot.com.mx/search?q=482588
```

Revirtiendo mentalmente la URL a `/p/{sku}`:
- `test_ingest_homedepot_url_absoluta_desde_seo_href` fija el slug EXACTO
  (`/p/varilla-...-482588`) que solo puede venir de `seo.href`; con `/p/{sku}`
  el `assert rp.url == host+slug` fallaría. **Delata el bug.**
- `test_ingest_homedepot_refresca_url_vieja_en_reingestion`: sin el bloque de
  refresh (`services.py:154-157`), `get_or_create` no toca la url de una fila
  hallada → `refresh_from_db()` devolvería `/p/482588` y el `assert == slug`
  fallaría. **Delata la ausencia del refresh.**
- `test_seed_hd_no_genera_urls_p_sku` asevera `/p/{sku} not in url`; con el seed
  viejo (`/p/{sku}`) fallaría. **Delata la regresión del seed.**

Los 5 tests F034 nombrados PASAN (`5 passed in 0.16s`). Tests 100% offline.

## 6. Higiene / alcance

- Archivos tocados **todos dentro de `backend/`** (la capa que la spec autoriza,
  "solo `backend/`"): `git status` no muestra ningún archivo de código fuera de
  `backend/`; único untracked = `progress/impl_F034_backend.md` (informe).
- Contrato SIN cambios: `openapi.json`/`schema.d.ts` no aparecen en `git status`.
- Puertos 8800/3300 OCUPADOS por dev servers del humano (hallazgo F033) → corrí
  `./init.sh` en modo **normal** (no `--e2e`); Fase 6 E2E saltada. init.sh full
  no liga a esos puertos (Fase 3 backend en `backend/`, Fase 4 `pnpm build` sin
  server), así que la corrida es válida y no interfiere con el dev del humano.

**Observación NO bloqueante (para el líder, no para un implementer):**
`progress/current.md` está desactualizado — dice "Feature en curso: ninguna" y
"31 done, pendiente F012", sin mencionar F034 in_progress ni su corrida `--e2e`
antigua (35 ok). CHECKPOINTS pide que refleje la sesión. No afecta la corrección
de F034 (no es criterio de la spec ni archivo del implementer); conviene que el
líder lo actualice al cerrar F034.

## 7. Output real de `./init.sh` (corrida del reviewer)

```
── Fase 0 · Herramientas ──
  ✔ git disponible
  ✔ node disponible
  ✔ jq disponible
  ✔ uv disponible
  ✔ docker disponible
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
  ✔ las 31 feature(s) 'done' tienen review APROBADO

── Fase 2 · Infraestructura (Postgres + Redis — opcional, migración futura) ──
  ◌ Docker no usado en el MVP (backend corre con SQLite); infra Postgres/Redis diferida a una migración futura

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
  ✔ 33 ok   ✘ 0 fallos   ◌ 2 pendientes
  VERDE — el arnés está en estado consistente.
INIT_EXIT=0
```
