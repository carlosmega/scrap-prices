# impl F022 — UI lista de cotización (frontend + e2e)

Spec aplicada: `specs/F022-ui-lista-cotizacion.md`.

## Estado: BLOCKED (por CORS del backend)

El frontend está **completo y verde** en tsc/lint/build/test:unit. El E2E de la
cotización **falla por una causa de backend**: el header `X-Session-Key` no está
permitido por CORS, así que el navegador bloquea TODAS las llamadas a
`/api/lists*`. Sin ese cambio (que es de la capa backend, prohibida para mí) la
feature no puede funcionar end-to-end. Ver "Bloqueo" abajo.

## Decisiones de UI/UX

- Identidad anónima: `getSessionKey()` genera un UUID v4 con `crypto.randomUUID()`,
  lo persiste en `localStorage` (`construscan.sessionKey`) y se manda como
  `X-Session-Key` vía el soporte de `sessionKey` de los helpers de `client.ts`.
- Estado de cotización compartido (store a nivel de módulo + suscriptores in-tab,
  igual que `use-selected-zone`): el badge del shell, el botón "Agregar" y la
  página `/cotizacion` ven el mismo estado y se actualizan al instante.
- Lista por defecto perezosa ("Mi cotización"): se crea en el primer "Agregar"
  (POST /api/lists con la zona activa, para que el snapshot salga de esa zona),
  cacheando su id en `localStorage`; si el backend ya no la conoce, se recrea.
- Totales y `line_total` SIEMPRE del backend; la UI nunca recalcula precios.
- "Agregar" solo se muestra en filas con precio (sin precio → 422 en backend).
- Estados cargando/error/vacío/datos en la página; feedback transitorio
  (agregando/agregado/reintentar) en el botón.

## Archivos creados

- `frontend/src/features/lists/session.ts` — `getSessionKey()` + `isUuidV4()`.
- `frontend/src/features/lists/session.test.ts` — 6 tests (persistencia + formato UUID).
- `frontend/src/features/lists/api.ts` — llamadas del dominio (tipadas del contrato).
- `frontend/src/features/lists/types.ts` — tipos derivados de `schema.d.ts`.
- `frontend/src/features/lists/hooks/use-quote.ts` — store compartido de la cotización.
- `frontend/src/features/lists/components/add-to-quote-button.tsx`
- `frontend/src/features/lists/components/quote-badge.tsx`
- `frontend/src/features/lists/components/quote-item-row.tsx`
- `frontend/src/features/lists/components/quote-list.tsx`
- `frontend/src/app/cotizacion/page.tsx` — ruta de la cotización.
- `e2e/tests/quote.spec.ts` — E2E agregar → snapshot+total → editar → quitar.

## Archivos modificados

- `frontend/src/lib/api/client.ts` — añadidos `apiPostPath`/`apiPatchPath`/
  `apiDeletePath` (los helpers POST/PATCH/DELETE existentes NO sustituían
  `{list_id}`/`{item_id}`; solo `apiGetPath` lo hacía). Tipados del contrato, sin
  `any`, mismo patrón que `apiGetPath`. `fetch` sigue solo en este archivo.
- `frontend/src/features/search/components/result-card.tsx` — botón "Agregar" por
  retailer con precio; recibe `zoneId`.
- `frontend/src/features/search/components/search-panel.tsx` — pasa `zoneId` a `ResultCard`.
- `frontend/src/features/products/components/product-prices.tsx` — botón "Agregar"
  por retailer con precio; recibe `zoneId`.
- `frontend/src/features/products/components/product-detail.tsx` — pasa `zoneId` a `ProductPrices`.
- `frontend/src/app/page.tsx` — badge de cotización en barra superior.
- `frontend/src/app/products/[id]/page.tsx` — badge de cotización en barra superior.

## Componentes shadcn añadidos

- `badge` (`pnpm dlx shadcn@latest add badge` → `src/components/ui/badge.tsx`).

## Output REAL de verificaciones

### `pnpm exec tsc --noEmit`
```
(sin salida — exit 0)
```

### `pnpm lint`
```
$ eslint
(sin salida — exit 0)
```

### `pnpm build`
```
$ next build
   ▲ Next.js 15.5.19
   - Environments: .env.local

   Creating an optimized production build ...
 ✓ Compiled successfully in 6.1s
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/6) ...
 ✓ Generating static pages (6/6)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    32.2 kB         151 kB
├ ○ /_not-found                            990 B         103 kB
├ ○ /cotizacion                          1.93 kB         121 kB
└ ƒ /products/[id]                       4.06 kB         123 kB
+ First Load JS shared by all             102 kB
```

### `pnpm test:unit`
```
$ vitest run
 RUN  v3.2.6 C:/scrap-prices/frontend

 ✓ src/features/lists/session.test.ts (6 tests) 8ms
 ✓ src/features/search/relative-time.test.ts (9 tests) 7ms
 ✓ src/features/zones/hooks/use-selected-zone.test.ts (5 tests) 39ms
 ✓ src/app/page.test.tsx (3 tests) 94ms

 Test Files  4 passed (4)
      Tests  23 passed (23)
```

### `pnpm test:e2e` (desde `e2e/`)
```
  1) [chromium] › tests\quote.spec.ts:23:5 › cotización: agregar → ver snapshot+total → editar cantidad → quitar
     Error: expect(locator).toHaveAttribute(expected) failed
     Locator:  getByTestId('add-to-quote').first()
     Expected: "added"
     Received: "idle"   (el botón quedó en data-state="error")

  1 failed
    [chromium] › tests\quote.spec.ts ...
  4 passed (37.9s)     ← smoke + zone + search + detail SIGUEN VERDES
```

## Bloqueo (causa raíz, capa backend)

El navegador hace preflight de cada `/api/lists*` (llevan el header
`X-Session-Key`). La respuesta del backend (verificada con curl contra el
servidor real) es:

```
$ curl -i -X OPTIONS http://127.0.0.1:8000/api/lists \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: x-session-key,content-type"
HTTP/1.1 200 OK
access-control-allow-origin: http://localhost:3000
access-control-allow-headers: accept, authorization, content-type, user-agent, x-csrftoken, x-requested-with
access-control-allow-methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
```

`access-control-allow-headers` es el default de `django-cors-headers` y **NO
incluye `x-session-key`** → el navegador bloquea la petición real → `ApiError` →
el botón queda en `error`. No hay `CORS_ALLOW_HEADERS` configurado en
`backend/config/settings.py` (grep sin coincidencias).

El backend EN SÍ funciona perfecto (probado con curl, sin navegador, con mis
mismas formas de request): crear lista → agregar ítem (snapshot `68.50`) →
detalle con total → PATCH qty=2 (`line_total` `137.00`) → DELETE `204`. El
problema es exclusivamente CORS.

### Fix requerido (implementer-backend)

En `backend/config/settings.py`, permitir el header. Mínimo:

```python
from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = (*default_headers, "x-session-key")
```

Tras ese cambio, `e2e/tests/quote.spec.ts` debería pasar tal cual está escrito
(no necesita ajustes de selectores). No tocué `backend/` por la regla de capas.

## Deuda / seguimientos

- Una sola lista por defecto (la spec lo permite). Gestión multi-lista, export
  CSV y login quedan fuera (backlog C2 / fase posterior).
- `formatPrice` asume MXN para los snapshots de la cotización (el contrato del
  ítem no trae `currency`; el catálogo es MXN en el MVP).
