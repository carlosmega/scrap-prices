# Review F035 — Resultados crudos por término scrapeado

**Veredicto: APROBADO**

Feature backend-only (sin cambio de contrato ni UI). Todas las verificaciones
re-ejecutadas por el reviewer (no se aceptó output pegado). `./init.sh --quick`
VERDE, 0 fallos. El fix se probó anti-teatro: la reproducción del bug DEPENDE
del fix.

Revisor: reviewer. Fecha de la corrida: 2026-07-08.

---

## 1. Criterios de aceptación de la spec (uno por uno)

| # | Criterio (spec F035) | Estado | Evidencia (comando/archivo) |
|---|----------------------|--------|-----------------------------|
| 1 | **Modelo/migración:** `PriceObservation.scrape_run` FK nullable a ScrapeRun, `SET_NULL`; `makemigrations --check` limpio | **CUMPLE** | `backend/apps/prices/migrations/0003_priceobservation_scrape_run.py`: `AddField ... ForeignKey(blank=True, null=True, on_delete=SET_NULL, related_name='observations', to='prices.scraperun')`. `uv run python manage.py makemigrations --check --dry-run` → `No changes detected` (exit 0) |
| 2 | **Ingestión (vivo + comando)** liga `scrape_run` | **CUMPLE** | Vivo: `services.py:437-445` pasa `search_term=termino, triggered_by=SEARCH`; núcleo `_run_ingestion` (`services.py:216`) crea la obs con `scrape_run=run`. Comando: `scrape.py:207` `ingest(..., search_term=category)`. Tests: `test_observaciones_del_vivo_se_ligan_a_su_scrape_run` (4 obs ligadas) y `test_corrida_liga_observaciones_a_scrape_run_con_search_term` (4 obs + `search_term="impermeabilizante"`), ambos PASS |
| 3 | **Búsqueda (el fix):** producto bajo `search_term="impermiabilizante"` con nombre "Impermeabilizante" aparece en `buscar("impermiabilizante")` (>0). Test offline que reproduce el bug (nombre ≠ término) | **CUMPLE** | `catalog/services.py:188-218` `_rp_ids_por_termino_scrapeado` + UNIÓN en `_buscar_crudos:234-243`. Test `test_bug_typo_muestra_crudos_por_termino_scrapeado` PASS. **Anti-teatro probado** (§3) |
| 4 | **Sin regresión + dedup:** `buscar("impermeabilizante")` sigue trayendo crudos por nombre; solape (a)∩(b) no duplica | **CUMPLE** | Dedup por construcción (se itera cada RP candidato UNA vez, `services.py:241`). Tests `test_sin_regresion_busqueda_por_nombre_sigue_funcionando`, `test_dedup_cuando_termino_y_nombre_se_solapan` (`.count("IMP-003")==1`), `test_termino_ajeno_no_arrastra_crudos_sin_relacion`, todos PASS |
| 5 | **Normalización del término** acento/case/espacio-insensible (mismo helper que el nombre) | **CUMPLE** | Reusa `_normalizar(... .strip())` en ambos lados (`services.py:207` y `:136`). Test `test_match_de_termino_es_acento_case_y_espacio_insensible` (`"  Impermeabilizànte  "` matchea `impermeabilizante`) PASS |
| 6 | **Backend limpio + tests OFFLINE** (candado de red intacto) | **CUMPLE** | `ruff` OK, `makemigrations --check` limpio, `pytest` 207 passed, `lint-imports` 1 kept/0 broken (§2). Candado `conftest.py` intacto (`build_live_adapter` explota si un test dispara el vivo real). Test nuevo usa `live="never"` |
| 7 | **Contrato sin drift** (`openapi.json`/`schema.d.ts`) | **CUMPLE** | `git status --porcelain backend/openapi.json frontend/src/lib/api/schema.d.ts` → VACÍO. `init.sh` Fase 5: "tipos TS sincronizados con backend/openapi.json" |
| 8 | **Global:** `./init.sh` verde | **CUMPLE** | `./init.sh --quick` → VERDE, 32 ok / 0 fallos / 3 pendientes (§6) |

**Sub-checks explícitos del encargo:**
- "Un producto scrapeado bajo OTRO término no se arrastra por la vía (a)": CUMPLE
  — `test_termino_ajeno_no_arrastra_crudos_sin_relacion` (CLA-001 bajo "clavo" NO
  sale al buscar "impermeabilizante").
- "El comando estampa `search_term=--category`": CUMPLE — `test_construrama.py`
  ahora asevera `run.search_term == "varilla"` (antes `is None`, deuda F033 pagada).

---

## 2. Backend — verificaciones re-ejecutadas por el reviewer

```
$ cd backend && uv run ruff check .
All checks passed!

$ uv run python manage.py makemigrations --check --dry-run
No changes detected            (exit 0)

$ uv run pytest
207 passed in 1.49s

$ uv run lint-imports
Analyzed 102 files, 158 dependencies.
Routers (api) no importan models directamente; delegan en services  KEPT
Contracts: 1 kept, 0 broken.
```

Los 5 tests nuevos del fix, aislados:
```
$ uv run pytest apps/catalog/tests/test_crudos_por_termino.py -v
apps/catalog/tests/test_crudos_por_termino.py .....   [100%]
5 passed in 0.16s
```

---

## 3. Anti-teatro: el fix es real (el test fallaría sin él)

Regla del "git stash mental": ¿el test de reproducción fallaría revirtiendo la
unión a solo-nombre? Se probó SIN editar el repo, con un test throwaway en el
scratchpad que fuerza el puente por término (`_rp_ids_por_termino_scrapeado`) a
devolver `set()` — simulación quirúrgica de revertir el fix (`_buscar_crudos`
queda con la condición pre-F035, solo `coincide_nombre`):

```
$ uv run pytest -c pyproject.toml --rootdir . <scratchpad>/test_prueba_antiteatro.py -v
test_reproduccion_depende_del_fix  PASSED   (1 passed in 0.15s)
```

El test asevera: (1) CON el fix, `IMP-001` está en `raw_results`; (2) con el
puente por término neutralizado, `IMP-001` DESAPARECE (0 crudos — el bug
reaparece). Razonamiento confirmado: el nombre "Impermeabilizante Comex 19L"
normalizado NO contiene la query typo "impermiabilizante" (i-a vs e-a), así que
la única vía de inclusión es (a) por término scrapeado. Sin (a), 0 crudos.

---

## 4. Arquitectura limpia (greps deterministas)

```
$ grep -rnE "\.objects|\.save\(|\.filter\(|\.create\(|\.delete\(" backend/apps/*/api.py
apps/lists/api.py:92:  @router.delete("/lists/{list_id}", response={204: None})
apps/lists/api.py:149: @router.delete("/lists/{list_id}/items/{item_id}", response={204: None})
```
Ambos son decoradores HTTP de Ninja `@router.delete(...)`, NO llamadas al ORM
(preexistentes; F035 no toca `api.py`). El grep refinado de `init.sh`
(`\.delete\(\s*\)` + filtro de decoradores) confirma limpio: Fase 3 →
"routers (api.py) sin llamadas al ORM". La lógica del fix vive en `services.py`.

Frontend: no aplica (backend-only, cero archivos de `frontend/` tocados).

---

## 5. Higiene de capa y estado

- **Archivos tocados** (todos dentro de la capa permitida `backend/` + el
  informe en `progress/`; NINGUNO fuera):
  ```
  M backend/apps/catalog/services.py
  M backend/apps/catalog/tests/test_live_search.py
  M backend/apps/prices/models.py
  M backend/apps/scraping/management/commands/scrape.py
  M backend/apps/scraping/services.py
  M backend/apps/scraping/tests/test_command_scrape.py
  M backend/apps/scraping/tests/test_construrama.py
  ?? backend/apps/catalog/tests/test_crudos_por_termino.py
  ?? backend/apps/prices/migrations/0003_priceobservation_scrape_run.py
  ?? progress/impl_F035_backend.md
  ```
- **`feature_list.json`:** JSON válido, 34 features, exactamente 1 `in_progress`
  = **F035** (`capas: ["backend"]`). Ninguna otra feature cambió de estado.
- **git repo** inicializado (Fase 0 `init.sh` OK).

---

## 6. `./init.sh` — corrida REAL del reviewer

### Modo usado: `--quick` (protección del dev server del humano)

**Verificado con `--quick` para no corromper el dev server del humano; el build
de frontend no cambió desde el último `init.sh` completo verde** (F034 lo dejó
verde y F035 no toca `frontend/`). El humano tiene `./dev.sh` corriendo AHORA
—`next dev` en `:3300` (PID 34798) y Django en `127.0.0.1:8800` (PID 36377)—; el
`pnpm build` de Fase 4 comparte `.next/` con ese `next dev` y se lo rompería
(hallazgo F033). `--quick` SALTA ese build y cubre todo lo relevante para un
backend-only sin cambio de contrato: ruff, makemigrations --check, pytest,
arquitectura backend, tsc/lint/vitest de frontend y el contrato (Fase 5). NO se
tocó/mató ningún proceso del humano; NO se corrió `--e2e`.

```
── Fase 0 · Herramientas ──  (git, node, jq, uv, docker, pnpm ✔; repo git ✔)
── Fase 1 · Invariantes del arnés ──  (todo ✔; in_progress: 1; 32 done con review APROBADO)
── Fase 2 · Infraestructura ──  ◌ Docker no usado en MVP (SQLite)
── Fase 3 · Backend ──
  ✔ uv sync   ✔ ruff check   ✔ makemigrations --check   ✔ pytest
  ✔ arquitectura: routers (api.py) sin llamadas al ORM
── Fase 4 · Frontend ──
  ✔ pnpm install  ✔ tsc --noEmit  ✔ lint  ✔ vitest  ◌ build saltado en modo --quick
  ✔ arquitectura: fetch solo en src/lib/api/client.ts
── Fase 5 · Contrato OpenAPI → tipos TS ──
  ✔ tipos TS sincronizados con backend/openapi.json
── Fase 6 · E2E ──  ◌ saltada (usa ./init.sh --e2e)

════════ Resumen ════════
  ✔ 32 ok   ✘ 0 fallos   ◌ 3 pendientes
  VERDE — el arnés está en estado consistente.
```

### Nota de transparencia

Antes de recibir la corrección del líder, el reviewer YA había corrido
`./init.sh` COMPLETO una vez (también VERDE: 33 ok / 0 fallos / 2 pendientes,
`build de producción` ✔). Eso pudo romperle el `.next/` al humano (él lo
relanza); NO afecta el veredicto. De aquí en adelante, para backend-only con el
dev server del humano vivo, se usa `--quick`.

---

## 7. Observaciones NO bloqueantes (para el líder/backlog, no afectan el veredicto)

1. **Truncado asimétrico de `search_term`:** el vivo trunca el término a 200
   (`_TERMINO_MAX_CORRIDA`), el comando pasa `--category` crudo sin truncar
   (`scrape.py:207`). `search_term` es `max_length=200`; en SQLite no se
   fuerza y las categorías del comando son slugs cortos, así que es inocuo en
   MVP. En Postgres/M5 convendría truncar también en el comando por simetría.
2. **`_hay_datos_frescos` sigue matcheando solo por nombre** (fuera de alcance,
   ya anotado por el implementer): re-buscar el typo dentro del TTL re-dispara
   el vivo hasta que aplique el cooldown — pero ya NO vuelve a 0 crudos (la FK
   persiste el hallazgo), que era el objetivo de F035.
3. **Observaciones pre-F035 y del seed** quedan con `scrape_run=null` (sin
   backfill, por spec): se hallan por el filtro (b) por nombre o al re-scrapear.

Ninguna de estas afecta un criterio de aceptación; el veredicto es **APROBADO**.
