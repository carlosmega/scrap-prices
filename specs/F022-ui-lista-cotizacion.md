# F022 — UI: lista de cotización (con snapshots, subtotal y total)

> Milestone M4 (cierra el MVP navegable). PRD Épica C + §12 (`/api/lists*`).

## Contexto y objetivo
El usuario arma su cotización ("carrito propio"): agrega productos con cantidad,
ve el **snapshot** de precio (no cambia si el precio cambia después), edita
cantidades, quita ítems y ve subtotal/total. Sin login: identidad por sesión.

## Alcance
**Incluye (frontend):**
- **Clave de sesión**: util `getSessionKey()` que genera y persiste un UUID en
  `localStorage` y se envía como header `X-Session-Key` en cada llamada a `/api/lists*`
  (vía los helpers de `client.ts`: apiGet/apiPost/apiPatch/apiDelete con headers).
- **Agregar a lista**: botón "Agregar a mi cotización" en los resultados de búsqueda
  (F020) y/o en el detalle (F021), por retailer-product + cantidad. Si no existe una
  lista para la sesión, crear una (lista por defecto) en el primer agregado.
- **Página de lista** `app/lists/page.tsx` (o `/cotizacion`): muestra los ítems con
  retailer, nombre, cantidad, `captured_price` (snapshot) + `captured_at`, `line_total`,
  y el **subtotal/total**. Permite **editar cantidad** y **quitar ítem**.
- Indicador de cantidad de ítems (badge) accesible desde el shell.
- Estados cargando/error/vacío ("tu cotización está vacía")/datos.

**Incluye (e2e):**
- `e2e/tests/quote.spec.ts`: zona MTY → buscar "varilla" → **agregar** un producto a la
  cotización → abrir la lista y ver el ítem con su snapshot y el total → **editar cantidad**
  (el total cambia) → **quitar** el ítem (lista vacía). 

**No incluye:** múltiples listas con gestión avanzada (una lista por defecto basta);
export CSV/Excel (backlog C2); login.

## Criterios de aceptación
- [ ] **Frontend:** agregar un producto desde búsqueda/detalle crea/usa la lista de la
      sesión y guarda el **snapshot** de precio; la página de lista muestra ítems con
      cantidad, snapshot, `line_total` y subtotal/total correctos.
- [ ] **Frontend:** editar cantidad recalcula totales; quitar ítem lo elimina; lista
      vacía muestra su estado. La identidad usa `X-Session-Key` (persistente); recargar
      conserva la cotización.
- [ ] **Frontend:** datos de `schema.d.ts` (cero `any`); `fetch` solo en `client.ts`;
      estados cargando/error/vacío/datos. Test unit de `getSessionKey` (persistencia/形ato UUID)
      y/o del cálculo de totales en cliente si aplica.
- [ ] **E2E:** `e2e/tests/quote.spec.ts` pasa (agregar → ver snapshot+total → editar → quitar);
      `./init.sh --e2e` Fase 6 verde.
- [ ] `tsc`/`lint`/`build`/`test:unit` limpios; `./init.sh` y `./init.sh --e2e` verdes.

## Plan de verificación
```bash
cd frontend && pnpm exec tsc --noEmit && pnpm lint && pnpm build && pnpm test:unit
cd .. && ./init.sh --e2e
```

## Notas y decisiones abiertas
- El snapshot lo fija el backend (F017) al agregar; la UI solo lo muestra. El total
  proviene del backend (`UserListDetailOut.total`); la UI no recalcula precios.
- `getSessionKey()` usa `crypto.randomUUID()` (disponible en el navegador).
- Cuando exista login (fase posterior), la lista por sesión podrá migrarse a la cuenta.
