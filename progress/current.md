# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F021** — UI detalle de producto + historial
**Spec:** `specs/F021-ui-detalle-producto.md`

## Plan F021 (frontend + e2e → implementer-frontend)
- Ruta `app/products/[id]/page.tsx`: lee id + zona (useSelectedZone) → GET /api/products/{id}.
  Render: specs del canónico, precios por retailer (frescura + enlace ficha), historial ordenado.
  Enlazar resultados de F020 al detalle. Estados + 404 + sin-zona. Reusa helper "hace X" (F020).
- E2E `detail.spec.ts`: búsqueda → detalle → precios por retailer + historial.

Cierre: `./init.sh --e2e` verde + tsc/lint/build/test:unit + review APROBADO.

**Estado:** F021 `in_progress`. M4: F019 ✅ F020 ✅ → **F021** → F022 (última del MVP).
