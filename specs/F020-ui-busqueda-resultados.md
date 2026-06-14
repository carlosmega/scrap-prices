# F020 — UI: búsqueda + resultados comparados por retailer

> Milestone M4. PRD Épica B1 + §12 (`/api/search`). La pantalla central de
> ConstruScan: buscar un material y comparar precios por retailer en la zona.

## Contexto y objetivo
Con una zona seleccionada (F019), el usuario busca por texto (p.ej. "varilla") y ve
los productos canónicos con sus precios en Home Depot y Construrama, con frescura y
orden por precio. Consume `GET /api/search` (DB propia, nunca en vivo).

## Alcance
**Incluye (frontend):**
- `src/features/search/`: input de búsqueda + componente de resultados (Client Component).
  Usa la zona de `useSelectedZone()` (F019) como `zone_id`; si no hay zona seleccionada,
  invita a elegirla (no busca sin zona).
- Llama `GET /api/search?q=&zone_id=&sort=` con el client tipado (helper `fetchSearch`).
- Cada resultado: nombre del canónico (+ unidad) y una fila/tarjeta por retailer con
  **precio**, **disponibilidad** y **frescura "actualizado hace X"** (a partir de
  `captured_at`); si un retailer no tiene precio → indicar "sin precio en tu zona"
  (B1·CA5). Control para ordenar por precio (B1·CA4).
- Estados: inicial (sin query), cargando, error, vacío ("sin resultados"), datos.
- Helper de "hace X" (relative time) en `src/features/search/` o `src/lib/` (util pura, testeable).

**Incluye (e2e):**
- `e2e/tests/search.spec.ts`: elegir "Monterrey Metro", buscar "varilla", ver ≥1
  resultado con precios de **ambos** retailers; verificar que el orden por precio
  muestra el menor primero.

**No incluye:** detalle/historial (F021), lista de cotización (F022), paginación,
filtros avanzados.

## Criterios de aceptación
- [ ] **Frontend:** con zona seleccionada, buscar "varilla" muestra resultados; cada
      uno con precios por retailer (HD y Construrama), unidad, disponibilidad y
      frescura ("actualizado hace X"). Ordenable por precio (menor primero).
- [ ] **Frontend:** sin zona seleccionada, la UI invita a elegir zona y no rompe.
      Retailer sin precio en la zona → se indica explícitamente. Estados
      cargando/error/vacío/datos presentes.
- [ ] **Frontend:** datos de `schema.d.ts` (cero `any`, cero tipos a mano); `fetch`
      solo en `client.ts`. Test unit del helper "hace X" (frescura).
- [ ] **E2E:** `e2e/tests/search.spec.ts` pasa (varilla en MTY, ambos retailers,
      orden por precio); `./init.sh --e2e` Fase 6 verde.
- [ ] `tsc`/`lint`/`build`/`test:unit` limpios; `./init.sh` y `./init.sh --e2e` verdes.

## Plan de verificación
```bash
cd frontend && pnpm exec tsc --noEmit && pnpm lint && pnpm build && pnpm test:unit
cd .. && ./init.sh --e2e
```

## Notas y decisiones abiertas
- Frescura: formatear `captured_at` a "hace X" en cliente; el dato nunca se oculta (RNF3).
- Si `fetchSearch` no existe aún, créalo en `src/features/search/api.ts` usando `apiGet`
  con query params tipados de `schema.d.ts`.
- Enlazar cada resultado al detalle (F021) es opcional aquí; F021 lo cablea.
