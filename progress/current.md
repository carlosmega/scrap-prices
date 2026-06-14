# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F022** — UI lista de cotización (snapshots, subtotal, total)
**Spec:** `specs/F022-ui-lista-cotizacion.md`

## Plan F022 (frontend + e2e → implementer-frontend) — última del MVP
- `getSessionKey()` (UUID en localStorage) → header `X-Session-Key` en /api/lists*.
- Botón "Agregar a mi cotización" en búsqueda/detalle (crea lista por defecto si no hay).
- Página de lista: ítems con snapshot + cantidad + line_total + subtotal/total; editar cantidad; quitar.
- E2E `quote.spec.ts`: agregar → ver snapshot+total → editar cantidad → quitar.

Cierre: `./init.sh --e2e` verde + tsc/lint/build/test:unit + review APROBADO. → **MVP M4 completo.**

**Estado:** F022 `in_progress`. M4: F019 ✅ F020 ✅ F021 ✅ → **F022** (última).
