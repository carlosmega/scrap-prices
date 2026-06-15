# F030 — Fix hydration mismatch (hooks de localStorage SSR-safe)

> Bug de runtime reportado en el navegador: "Hydration failed... server rendered
> text didn't match the client" en `SearchPanel`/`CardDescription`. Causa: los
> hooks que leen `localStorage` (zona seleccionada, cotización) lo hacen en el
> render inicial → el HTML del servidor (sin localStorage) difiere del cliente.

## Contexto y objetivo
Eliminar el desajuste de hidratación haciendo que el **primer render del cliente
coincida con el del servidor**, y poblar desde `localStorage` **después de montar**.
Conservar la persistencia y el sync entre pestañas/in-tab existentes.

## Alcance
**Incluye (frontend):**
- **`useSelectedZone`** (F019) y **el hook de cotización/sesión** (`useQuote`/`getSessionKey`,
  F022) y cualquier otro que lea `localStorage`/`window` durante el render:
  - Patrón SSR-safe: el valor inicial (server snapshot) es el **default sin
    localStorage** (p.ej. zona = `null`, cotización vacía); leer `localStorage` en
    `useEffect` tras montar (o `useSyncExternalStore` con `getServerSnapshot` que
    devuelva el default). Así el primer paint del cliente == SSR; luego se hidrata.
  - Conservar persistencia (escritura a localStorage), sync `storage` cross-tab y el
    broadcast in-tab ya implementados.
- Revisar que ningún componente (badge de cotización, SearchPanel, ZoneSelector)
  ramifique su markup con datos de localStorage en el primer render.

**Incluye (e2e) — guardia de regresión:**
- En el flujo E2E (p.ej. `zone.spec.ts` o un test nuevo), **escuchar errores de consola/página**
  y **fallar** si aparece un mensaje de hidratación (`/hydration/i`) al cargar `/` con una zona
  ya seleccionada en `localStorage` (simular: set localStorage antes de navegar, recargar).

**No incluye:** cambios de diseño visual; lógica de negocio; backend.

## Criterios de aceptación
- [ ] **Frontend:** con una zona guardada en `localStorage`, cargar `/` **no produce
      hydration mismatch** (sin el error de consola). El primer render muestra el estado
      SSR-safe y luego refleja la zona guardada.
- [ ] **Frontend:** la persistencia sigue funcionando: elegir zona → recargar → la zona
      persiste (el comportamiento de F019 no se rompe); la cotización (F022) igual.
- [ ] **E2E:** un test falla si hay error de hidratación en `/` con zona pre-seteada en
      localStorage; con el fix, pasa. No se rompen los E2E previos.
- [ ] `pnpm exec tsc --noEmit`, `pnpm lint`, `pnpm build`, `pnpm test:unit` limpios;
      `./init.sh --e2e` verde. Sin `fetch` fuera de client.ts; cero `any`.

## Plan de verificación
```bash
cd frontend && pnpm exec tsc --noEmit && pnpm lint && pnpm build && pnpm test:unit
cd .. && ./init.sh --e2e
```

## Notas
- Aceptable un breve "flash" del estado por-defecto antes de hidratar desde localStorage
  (es el costo correcto de SSR-safety; preferible al mismatch).
- `useSyncExternalStore` (React 18+) con `getServerSnapshot` es la solución canónica para
  estado externo como localStorage; alternativamente el patrón `mounted` + `useEffect`.
