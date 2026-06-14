# F021 — UI: detalle de producto + historial de precio

> Milestone M4. PRD Épica B2 + §12 (`/api/products/{id}`).

## Contexto y objetivo
Desde un resultado de búsqueda, el usuario abre el detalle de un producto canónico:
ve sus `specs` (calibre/diámetro/longitud), los precios actuales por retailer en su
zona, el historial de precio y el enlace a la ficha original del retailer.

## Alcance
**Incluye (frontend):**
- Ruta de detalle (App Router): `app/products/[id]/page.tsx` (o vista equivalente).
  Lee el `id` de la ruta y la zona de `useSelectedZone()`; llama
  `GET /api/products/{id}?zone_id=` con el client tipado.
- Render: nombre + `specs` del canónico; precios actuales por retailer (precio,
  disponibilidad, frescura "hace X", enlace a `url` del retailer); **historial** de
  precio (lista de lecturas con retailer, precio y fecha, orden reciente→antiguo).
- Enlazar los resultados de F020 al detalle (cada resultado lleva a `/products/{id}`).
- Estados cargando/error/datos; si no hay zona → invitar a elegirla. 404 → "producto no encontrado".

**Incluye (e2e):**
- `e2e/tests/detail.spec.ts`: desde la búsqueda (zona MTY, "varilla"), entrar al
  detalle de un producto y verificar que se ven precios por retailer y el historial.

**No incluye:** gráfica de historial (lista basta para MVP); lista de cotización (F022);
agregar al carrito desde aquí (lo cablea F022).

## Criterios de aceptación
- [ ] **Frontend:** el detalle muestra `specs`, precios actuales por retailer (con
      frescura y enlace a la ficha) e historial de precio (varias lecturas ordenadas).
- [ ] **Frontend:** se navega a `/products/{id}` desde un resultado de búsqueda (F020).
- [ ] **Frontend:** estados cargando/error/datos; 404 producto → mensaje amable; sin
      zona → invita a elegir. Datos de `schema.d.ts` (cero `any`); `fetch` solo en client.ts.
- [ ] **E2E:** `e2e/tests/detail.spec.ts` pasa (búsqueda → detalle → precios + historial);
      `./init.sh --e2e` Fase 6 verde.
- [ ] `tsc`/`lint`/`build`/`test:unit` limpios; `./init.sh` y `./init.sh --e2e` verdes.

## Plan de verificación
```bash
cd frontend && pnpm exec tsc --noEmit && pnpm lint && pnpm build && pnpm test:unit
cd .. && ./init.sh --e2e
```

## Notas y decisiones abiertas
- La ruta dinámica de Next con datos de zona en cliente: el detalle puede ser Client
  Component (lee `useSelectedZone`) o pasar `zone` por query. Elegir lo más simple y limpio.
- Reutiliza el helper de frescura ("hace X") de F020.
