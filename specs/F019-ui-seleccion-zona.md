# F019 — UI: selección de zona (persistente en sesión)

> Milestone M4. PRD Épica A (A1) + §12. Primera feature de UI: establece el shell
> de la app y el estado de "zona seleccionada" que consumen búsqueda (F020) y listas.

## Contexto y objetivo
El usuario elige su zona; los precios mostrados después corresponden a esa zona. La
selección **persiste durante la sesión** (A1·CA3). Consume `GET /api/zones` (y,
opcional, `POST /api/zones/resolve` por geolocalización). Limpia el placeholder
viejo de la home (deuda de F003).

## Alcance
**Incluye (frontend):**
- Shell de la home (`app/page.tsx`) renovado: encabezado ConstruScan + selector de zona
  visible. (Reemplaza el texto placeholder de F003.)
- `src/features/zones/` : componente selector (Client Component) que lista zonas activas
  con `fetchZones()` (tipado, ya existe) y permite elegir una; estados carga/error/datos.
- Estado de zona seleccionada **persistente en `localStorage`** vía un hook
  `useSelectedZone()` (id + nombre); sobrevive a recargas (A1·CA3).
- (Opcional) botón "usar mi ubicación": `navigator.geolocation` → `POST /api/zones/resolve`;
  si 404 → mensaje amable "aún sin cobertura en tu zona" (A1·CA4).
- El `HealthIndicator` puede quedarse (footer discreto) o moverse; no es el foco.

**Incluye (e2e):**
- Asegurar **datos sembrados** para E2E: actualizar el `webServer` de backend en
  `e2e/playwright.config.ts` para correr `migrate` + `seed` antes de `runserver`.
- Test E2E del flujo feliz: abrir `/`, elegir "Monterrey Metro", verificar que queda
  seleccionada y que **persiste tras recargar** la página.

**No incluye:** búsqueda (F020), detalle (F021), lista (F022); geocoding por dirección
(solo lat/lng); multi-zona simultánea.

## Criterios de aceptación
- [ ] **Frontend:** la home muestra el selector de zona; al elegir "Monterrey Metro"
      queda seleccionada y se muestra el nombre; recargar mantiene la selección.
- [ ] **Frontend:** el selector maneja sus tres estados (cargando/error/datos); los
      datos de zona salen de `schema.d.ts` (cero tipos a mano, cero `any`, `fetch`
      solo en `client.ts`).
- [ ] **Frontend:** ya no queda el texto placeholder de F003 en la home.
- [ ] **E2E:** `pnpm test:e2e` (con backend seedeado vía webServer) pasa el test de
      selección + persistencia; `./init.sh --e2e` Fase 6 verde.
- [ ] `pnpm exec tsc --noEmit`, `pnpm lint`, `pnpm build`, `pnpm test:unit` limpios;
      `./init.sh` verde (full) y `./init.sh --e2e` verde.

## Plan de verificación
```bash
cd frontend && pnpm exec tsc --noEmit && pnpm lint && pnpm build && pnpm test:unit
cd .. && ./init.sh --e2e   # Fase 6 (Playwright) verde con backend seedeado
```

## Notas y decisiones abiertas
- Persistencia: `localStorage` (cliente). La clave de sesión para listas
  (`X-Session-Key`) se introduce en F022; F019 solo persiste la zona.
- Mantener `"use client"` lo más abajo posible (solo el selector y su estado).
- Sin librería de estado global nueva (hook + localStorage basta para MVP).
