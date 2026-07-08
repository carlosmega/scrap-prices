# Veredicto: APROBADO

> Review de F033 (búsqueda en vivo bajo demanda) contra `specs/F033-busqueda-en-vivo.md`
> y `CHECKPOINTS.md`. Reviewer re-ejecutó TODAS las verificaciones (2026-07-07/08).
>
> Historia del veredicto: la primera pasada quedó **RECHAZADA únicamente** por la
> Fase 6 (suite Playwright 8/8 failed) causada por un **bloqueo de entorno** ajeno
> a la feature (dev server Next de `./dev.sh` del humano en :3300 zombie tras los
> builds de producción de la verificación — diagnóstico completo en el anexo,
> conservado). El líder saneó el entorno (procesos 21982/21983 terminados;
> verifiqué ambos puertos LIBRES con `lsof` antes de re-correr) y la
> re-verificación completa quedó **VERDE**. Ningún defecto de código fue
> encontrado en ninguna pasada; el código NO cambió entre ambas corridas.

## Re-verificación final: `./init.sh --e2e` (output real, entorno saneado)

```
── Fase 1 · Invariantes del arnés ──          14 ✔ (in_progress: 1; 30 done con review APROBADO)
── Fase 2 · Infraestructura ──                ◌ (SQLite MVP, por diseño)
── Fase 3 · Backend ──                        ✔ uv sync ✔ ruff ✔ makemigrations --check ✔ pytest ✔ api.py sin ORM
── Fase 4 · Frontend ──                       ✔ install ✔ tsc ✔ lint ✔ vitest ✔ build ✔ fetch solo en client.ts
── Fase 5 · Contrato ──                       ✔ tipos TS sincronizados con backend/openapi.json
── Fase 6 · E2E ──                            ✔ pnpm install ✔ suite Playwright
════════ Resumen ════════
  ✔ 35 ok   ✘ 0 fallos   ◌ 1 pendientes
  VERDE — el arnés está en estado consistente.
```

Suite E2E corrida además en directo para constancia por test (servers frescos
levantados por Playwright — puertos verificados libres antes; `webServer` hizo
migrate+seed y el env fija `SEARCH_LIVE_TTL_HOURS=876000`, corrida offline):

```
[1/8] detail.spec.ts:13   › desde la búsqueda al detalle: precios por retailer e historial
[2/8] search.spec.ts:28   › buscar varilla en Monterrey Metro: ambos retailers y orden por precio
[3/8] smoke.spec.ts:9     › la home carga y el indicador de salud muestra ok
[4/8] hydration.spec.ts:24 › cargar / con una zona ya guardada no produce hydration mismatch
[5/8] normalization.spec.ts:23 › varilla 1/2 en Monterrey Metro: HD mejor $/kg y nativo $/ton visible
[6/8] quote.spec.ts:23    › cotización: agregar → ver snapshot+total → editar cantidad → quitar
[7/8] zone.spec.ts:11     › elegir zona y que persista tras recargar
[8/8] search.spec.ts:96   › F033: buscar varilla muestra la sección cruda (amarrador Truper) y cotiza desde ahí
  8 passed (6.4s)
```

## Criterios de aceptación de la spec, uno por uno

| Criterio | Estado | Evidencia (re-ejecutada por el reviewer) |
| --- | --- | --- |
| B1: término sin datos dispara vivo de AMBOS (MockTransport), ingesta (RP+PO+ScrapeRun con `search_term`, `triggered_by="search"`) y responde `raw_results` + `live.triggered=true` | CUMPLE | `test_termino_sin_datos_dispara_vivo_de_ambos_e_ingesta` (asserta ScrapeRun×2 `triggered_by=search`, RP unmatched, PO en zona, crudo en respuesta, 1 request por retailer). `uv run pytest` → **186 passed** (exit 0) |
| B2: NO dispara con datos frescos / `live=never` / `len(q)<3` / cooldown (aún con 0 items) | CUMPLE | 4 tests dedicados en `test_live_search.py` + `test_cooldown_es_por_retailer`. **Spot-check anti-teatro:** con `SEARCH_LIVE_COOLDOWN_MINUTES=0` el test del cooldown **FALLA** (1 failed) y con `SEARCH_LIVE_TTL_HOURS=0` el de frescura **FALLA** — los tests ejercitan la implementación real, no pasan solos |
| B3: retailer bloqueado (429) o caído no impide al otro | CUMPLE | `test_retailer_bloqueado_no_impide_al_otro`: HD `blocked` con "429" sin `Traceback`, 1 sola petición (stop-if-blocked), CR `ok` con 7 items ingestados |
| B4: Construrama sin key → `skipped` con motivo y HD sigue; tests OFFLINE | CUMPLE | `test_construrama_sin_key_queda_skipped_y_hd_sigue` (motivo nombra `CONSTRURAMA_ALGOLIA_SEARCH_KEY`, skip sin ScrapeRun). Candado anti-red leído en `backend/conftest.py`: autouse parchea `build_live_adapter` a AssertionError; adapters de test sobre `httpx.MockTransport` + golden fixtures |
| Contrato: `openapi.json` regenerado + `gen:api` sin drift | CUMPLE | Regeneré el schema a scratchpad y `diff` contra `backend/openapi.json` → idéntico. `openapi-typescript` a scratchpad y `diff` contra `frontend/src/lib/api/schema.d.ts` → idéntico. Fase 5 de init.sh ✔ |
| F1: spinner progresivo; sección cruda por retailer (raw_name, precio nativo + `sale_unit`, disponibilidad, frescura "hace X", link); vacío/error; cero `any`; tipos solo generados | CUMPLE | `search-progress.tsx` (1.5 s → mensaje en vivo; testeado con fake timers), `raw-results-section.tsx` (todo lo pedido, link `_blank`+`noopener`, agrupado por retailer), `use-search.ts`/`search-panel.tsx` (estados idle/loading/error/empty/ready; `live` también en vacío). Greps: `fetch(` fuera de client.ts → VACÍO; `: any\|as any` → VACÍO. `types.ts`: todo derivado de `fetchSearch()` → `schema.d.ts`. `tsc`/`lint`/`test:unit` (57 passed)/`build` → verdes |
| F2: badge de vivo por retailer cuando `live.triggered`; agregar-a-cotización desde crudo | CUMPLE | `live-run-badge.tsx` (badge por retailer con status/detail, variantes) + `AddToQuoteButton` con `retailer_product_id` en la sección cruda. Etiquetas unit-testeadas (`live.test.ts`) |
| E2E: seed con ≥1 RP sin matchear; "varilla" muestra canónicos Y sección cruda; cotizar desde ahí; suite completa pasa | CUMPLE | `search.spec.ts:96` **passed** en mi corrida (arriba): canónicos + sección cruda, grupo Construrama, "$125.00"+"pieza", "actualizado hace"+"disponible", link `_blank`/`noopener` a construrama.com, **`live-run-badge` count 0** (= el vivo NO se disparó con datos frescos → corrida offline probada), add-to-quote desde el crudo (data-state added + quote-badge "1"). Suite completa 8/8 |
| Global: `./init.sh --e2e` verde | CUMPLE | Re-verificación final: **35 ✔ / 0 ✘ → VERDE** (output arriba) |

## CHECKPOINTS.md, sección por sección

| Checkpoint | Estado | Evidencia |
| --- | --- | --- |
| Global: init.sh verde punta a punta | CUMPLE | 35 ✔ / 0 ✘ (corrida final) |
| Global: solo F033 cambió de estado | CUMPLE | `feature_list.json`: 32 features, `in_progress: 1 -> F033`, 0 status inválidos (node) |
| Global: impl_<id>_<capa>.md por capa con output real | CUMPLE | `progress/impl_F033_backend.md` y `progress/impl_F033_frontend.md` (outputs consistentes con mis re-corridas) |
| Backend: pytest pasa con tests nuevos que fallarían sin la implementación | CUMPLE | 186 passed (171 base + 15 F033). Spot-checks de cooldown/TTL por env → FALLAN sin la funcionalidad (demostrado) |
| Backend: makemigrations --check limpio | CUMPLE | "No changes detected". Migración `prices/0002_scraperun_search_term_scraperun_triggered_by.py` presente en el árbol (untracked, working tree sin commitear como el resto de F033 — el commit lo hace el líder al cerrar) |
| Backend: ruff limpio | CUMPLE | "All checks passed!" |
| Backend: lógica en services, no en routers | CUMPLE | `catalog/api.py` solo delega (leído); gatillo en `catalog/services.py`, ejecución en `scraping/services.py` |
| Backend: api.py sin ORM; import-linter pasa | CUMPLE | Grep exacto de Fase 3 → VACÍO (los 2 hits de un grep ingenuo son decoradores `@router.delete(`, no ORM). `uv run lint-imports`: "Contracts: 1 kept, 0 broken" |
| Backend: CORS desde env | CUMPLE | `settings.py:24,161` (`CORS_ALLOWED_ORIGINS` env, default localhost:3300); verificado vivo con header `access-control-allow-origin` |
| Backend: openapi.json regenerado y en el árbol | CUMPLE | Diff contra regeneración desde el código → idéntico |
| Contrato: schema.d.ts sin drift; sin tipos de API a mano | CUMPLE | Diff contra regeneración → idéntico; `types.ts` 100 % derivado; cero `any` (grep) |
| Frontend: tsc/lint/build; shadcn por CLI; estados carga/error; fetch solo en client.ts | CUMPLE | Todos verdes (corridas explícitas + Fase 4). Sin componentes shadcn nuevos (Badge/Card/Button existentes). `client.ts` sin timeout impuesto (grep `timeout|AbortSignal` vacío — spec: no <30 s) |
| E2E: smoke + test propio del flujo feliz | CUMPLE | Smoke ✔ y `F033: buscar varilla muestra la sección cruda…` ✔ en la corrida final (8/8) |
| Higiene: feature_list válido ≤1 in_progress; current.md fiel; done con review; repo git | CUMPLE | Fase 1: 14 ✔. `progress/current.md` refleja F033/plan/estado. `git status`: 39 archivos tocados, TODOS de F033 (backend/frontend-search/schema.d.ts/e2e/progress); nada staged; nada fuera de capa |

## Seguridad / secretos

- `backend/.env` existe (64 bytes), **gitignored** (`git check-ignore -v` → regla `.gitignore:20:.env`), NO aparece en `git status` ni staged (`git diff --cached` → 0 archivos).
- Contiene únicamente `CONSTRURAMA_ALGOLIA_SEARCH_KEY=` (solo verifiqué el nombre de la var, no imprimí el valor).
- Grep de patrones hex de 32 chars sobre los 39 archivos tocados (har/ excluido por gitignore) → **0 hits**. Los tests usan `KEY_DE_PRUEBA = "test-search-key"` (no real, transporte mockeado).

## Anexo: diagnóstico del rojo E2E de la primera pasada (superado; conservado como registro)

Primera corrida de `./init.sh --e2e`: 34 ✔ / 1 ✘ — SOLO Fase 6, con 8/8 tests
fallidos incluido el smoke pre-F033 (señal de entorno, no de feature). Segunda
corrida de la suite sola: 8/8 failed de nuevo. Diagnóstico con navegador
instrumentado (Playwright + captura de consola/red) contra el :3300 reusado:

```
[response>=400] 404 /_next/static/css/app/layout.css
[response>=400] 404 /_next/static/chunks/app/page.js
[response>=400] 404 /_next/static/chunks/main-app.js
[response>=400] 404 /_next/static/chunks/app-pages-internals.js
--- roles status: ["Cargando zonas…","Primero selecciona una zona…","Verificando el estado del backend…"]
```

El HTML SSR llegaba (200) pero los chunks de hidratación daban 404 → React no
hidrataba → ningún fetch client-side → timeouts en los 8 tests. Causa: el
`next dev` de `./dev.sh` del humano (PID 21983, arrancado 22:25:48) quedó
incoherente después de que los `pnpm build` de producción de la verificación
reescribieran `.next/` compartido (quedó `BUILD_ID` + chunks hasheados de
producción mientras el dev server servía HTML que referenciaba chunks dev sin
hash). El backend :8800 estaba sano (probe: `/api/search?q=varilla` respondía
`results: 3 | raw: 1 | live: null` — F033 vivo, sin disparo por frescura) y
CORS correcto. Resolución: el líder terminó ambos procesos; verifiqué puertos
libres (`lsof` vacío) y re-corrí todo → VERDE. El hallazgo estructural
(`next dev`/`next build` compartiendo `.next/` + `reuseExistingServer`) quedó
registrado por el líder como follow-up fuera de F033.

## Comandos ejecutados (reproducibles)

```bash
cd backend && uv run ruff check .                                   # All checks passed!
cd backend && uv run python manage.py makemigrations --check --dry-run  # No changes detected
cd backend && uv run pytest                                          # 186 passed (exit 0)
cd backend && uv run lint-imports                                    # 1 kept, 0 broken
# Spot-checks (tests nuevos fallan sin la funcionalidad):
SEARCH_LIVE_COOLDOWN_MINUTES=0 uv run pytest apps/catalog/tests/test_live_search.py::test_dentro_del_cooldown_no_dispara_aunque_hallara_cero  # 1 failed ✔(esperado)
SEARCH_LIVE_TTL_HOURS=0 uv run pytest apps/catalog/tests/test_live_search.py::test_con_datos_frescos_no_dispara_y_expone_crudos_sembrados     # 1 failed ✔(esperado)
# Contrato:
uv run python manage.py export_openapi_schema --api config.api.api --indent 2 --output <scratch>/openapi.check.json && diff <scratch>/openapi.check.json openapi.json   # idéntico
cd frontend && pnpm exec openapi-typescript ../backend/openapi.json -o <scratch>/schema.check.d.ts && diff <scratch>/schema.check.d.ts src/lib/api/schema.d.ts          # idéntico
cd frontend && pnpm exec tsc --noEmit && pnpm lint && pnpm test:unit && pnpm build   # verdes (57 unit tests)
# Arquitectura:
grep -rn "fetch(" frontend/src --include='*.ts' --include='*.tsx' | grep -v client.ts   # vacío
grep -rn ": any\b\|as any" frontend/src --include='*.ts' --include='*.tsx'              # vacío
# (grep ORM de Fase 3, con exclusión de decoradores HTTP)                               # vacío
git check-ignore -v backend/.env   # .gitignore:20:.env
# Re-verificación final (entorno saneado; lsof :8800/:3300 vacío antes):
./init.sh --e2e                    # 35 ✔ / 0 ✘ → VERDE
cd e2e && pnpm test:e2e            # 8 passed (6.4s), incluido search.spec.ts:96 (F033)
```
