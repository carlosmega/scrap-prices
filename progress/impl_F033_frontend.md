# impl F033 — frontend + e2e (búsqueda en vivo: UI de crudos, badge y espera progresiva)

## Spec aplicada y decisiones

Spec: `specs/F033-busqueda-en-vivo.md`, criterios Frontend y E2E. Decisiones:
(1) el breakage de tipos colgaba TODO de `features/search/types.ts` (derivaba
`[number]` de la respuesta-lista): rederivar de `SearchOut` arregló en cascada
`result-card` y `product-prices` sin tocarlos — canónicos $/kg (F031) intactos;
(2) "vacío" ahora es "ni canónicos NI crudos", y `live` se conserva también en
vacío/sin-canónicos para explicar qué pasó con cada tienda; (3) el mensaje
progresivo vive en un componente con timer propio (`SearchProgress`, umbral
exportado y testeado con fake timers); (4) helpers nuevos PUROS y unit-testeados
(agrupado por retailer robusto a intercalado, precio nativo float + sale_unit,
etiquetas del vivo); (5) el cliente HTTP no impone timeout (verificado: `fetch`
sin `AbortSignal.timeout`) — no hizo falta tocarlo.

## Archivos creados

- `frontend/src/features/search/raw-results.ts` — `groupRawResultsByRetailer`
  (genérico estilo `sortPricesAsc`; preserva orden backend retailer→precio asc).
- `frontend/src/features/search/live.ts` — `liveStatusLabel` ("ok · N" /
  "bloqueado" / "omitido" / "falló") y `retailerNameFromSlug`.
- `frontend/src/features/search/components/raw-results-section.tsx` — sección
  "Resultados de las tiendas (sin comparar)" agrupada por retailer: raw_name,
  brand, precio nativo + `sale_unit`, disponibilidad, frescura "hace X"
  (reusa `relative-time`), link a la ficha (`_blank` + `noopener`) y
  `AddToQuoteButton` con `retailer_product_id`. Sin crudos no se renderiza.
- `frontend/src/features/search/components/live-run-badge.tsx` — badge cuando
  `live.triggered`: un Badge por retailer (variante por status, `detail` breve
  si viene; testids `live-run-badge`/`live-retailer-status` + data-status).
- `frontend/src/features/search/components/search-progress.tsx` — "Buscando…"
  → tras 1.5 s "Consultando Home Depot y Construrama en vivo, puede tardar
  unos segundos…" (`LIVE_HINT_DELAY_MS = 1500`).
- Tests: `raw-results.test.ts` (5), `live.test.ts` (5),
  `components/search-progress.test.tsx` (3, fake timers).

## Archivos modificados

- `frontend/src/features/search/types.ts` — **la adaptación al BREAKING**:
  `SearchResponse` (SearchOut) y de ahí `SearchResult`, `RetailerPrice`,
  `RawResult`, `LiveInfo`, `LiveRetailerStatus`. Todo inferido de
  `fetchSearch()` → `schema.d.ts`; cero tipos a mano.
- `frontend/src/features/search/hooks/use-search.ts` — estado `ready` ahora
  lleva `results + rawResults + live`; `empty` lleva `live`; carrera por
  generación intacta.
- `frontend/src/features/search/components/search-panel.tsx` — compone badge
  de vivo, canónicos (o nota `search-no-canonical` si solo hay crudos) y la
  sección cruda; loading delega en `SearchProgress`.
- `frontend/src/features/search/format.ts` (+`format.test.ts`, +3 casos) —
  `formatRawPrice` (price float del contrato + sale_unit null-able).
- `frontend/src/features/search/api.ts` — solo docstring (SearchOut, default
  `live=auto` del contrato, latencia esperada). No se manda `live` desde la UI.
- `frontend/src/lib/api/schema.d.ts` — ya venía regenerado por backend (sin
  cambios míos).
- `e2e/tests/search.spec.ts` — test nuevo "F033: buscar varilla muestra la
  sección cruda (amarrador Truper) y cotiza desde ahí": canónicos Y sección
  cruda juntos, grupo Construrama, precio "$125.00 / pieza", frescura
  "actualizado hace" + "disponible", link `_blank`/`noopener` a construrama.com,
  **asserta live-run-badge count 0** (datos frescos ⇒ corrida en vivo NO
  disparada ⇒ prueba de que el run fue offline) y agrega a cotización desde el
  crudo (data-state added + quote-badge-count "1").
- `e2e/playwright.config.ts` — `SEARCH_LIVE_TTL_HOURS=876000` en el env del
  webServer backend (blindaje sugerido por backend: un server relanzado por
  Playwright jamás dispara vivo por seed viejo; comentado que NO protege
  términos sin ninguna observación — ningún E2E debe buscar fuera del seed).

Componentes shadcn añadidos: ninguno (Badge/Card/Button existentes cubren todo).

## Output real de verificación

```
$ pnpm exec tsc --noEmit
(sin errores)

$ pnpm lint
$ eslint
(sin errores)

$ pnpm test:unit
 ✓ src/features/search/live.test.ts (5 tests) 1ms
 ✓ src/features/search/relative-time.test.ts (9 tests) 2ms
 ✓ src/features/lists/session.test.ts (6 tests) 2ms
 ✓ src/features/search/raw-results.test.ts (5 tests) 2ms
 ✓ src/features/search/format.test.ts (21 tests) 12ms
 ✓ src/features/zones/hooks/use-selected-zone.test.ts (5 tests) 11ms
 ✓ src/features/search/components/search-progress.test.tsx (3 tests) 15ms
 ✓ src/app/page.test.tsx (3 tests) 34ms
 Test Files  8 passed (8)
      Tests  57 passed (57)

$ pnpm build
 ✓ Generating static pages (6/6)
Route (app)                                 Size  First Load JS
┌ ○ /                                    33.4 kB         153 kB
├ ○ /_not-found                            988 B         103 kB
├ ○ /cotizacion                          1.93 kB         121 kB
└ ƒ /products/[id]                       4.31 kB         124 kB

$ cd e2e && pnpm test:e2e
Running 8 tests using 8 workers
[1/8] [chromium] › tests/normalization.spec.ts:23:5 › varilla 1/2 en Monterrey Metro: Home Depot es mejor precio por $/kg y su nativo $/ton es visible
[2/8] [chromium] › tests/search.spec.ts:28:5 › buscar varilla en Monterrey Metro: ambos retailers y orden por precio
[3/8] [chromium] › tests/detail.spec.ts:13:5 › desde la búsqueda al detalle: precios por retailer e historial
[4/8] [chromium] › tests/quote.spec.ts:23:5 › cotización: agregar → ver snapshot+total → editar cantidad → quitar
[5/8] [chromium] › tests/search.spec.ts:96:5 › F033: buscar varilla muestra la sección cruda (amarrador Truper) y cotiza desde ahí
[6/8] [chromium] › tests/smoke.spec.ts:9:5 › la home carga y el indicador de salud muestra ok
[7/8] [chromium] › tests/hydration.spec.ts:24:5 › cargar / con una zona ya guardada no produce hydration mismatch
[8/8] [chromium] › tests/zone.spec.ts:11:5 › elegir zona y que persista tras recargar
  8 passed (2.8s)
```

Nota de la corrida E2E: había servidores previos en 8800/3300 (huérfanos de una
sesión anterior); los reinicié y un `./dev.sh` del humano los relevantó al
instante con migrate+seed F033 recién corridos — `reuseExistingServer` los
aprovechó, que es exactamente su caso de uso. La suite pasó 8/8 en 2.8 s
(servida de BD; el test F033 asserta que el vivo NO se disparó).

## Deuda / seguimientos

- El camino `live.triggered` del badge (y `blocked`/`skipped`/`failed`) no es
  ejercitable en E2E offline por diseño (el vivo requiere red real); queda
  cubierto por unit tests de las etiquetas y por los 10 tests offline del
  backend. Humo manual opcional con red real: buscar "cemento" en dev.
- Si el usuario re-somete mientras ya está cargando, `SearchProgress` no
  re-monta y el hint de 1.5 s no se resetea (caso menor, sin key natural para
  forzar remount; anotado en el docstring del componente).
- `retailerNameFromSlug` capitaliza el slug porque `LiveRetailerStatusOut` solo
  trae slug; si algún día el contrato añade `retailer_name` ahí, usarlo.
- Recordatorio permanente para futuros E2E: no buscar términos fuera del seed
  (el TTL del webServer no protege términos con CERO observaciones).
