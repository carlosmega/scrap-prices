# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F020** — UI búsqueda + resultados comparados por retailer
**Spec:** `specs/F020-ui-busqueda-resultados.md`

## Plan F020 (frontend + e2e → implementer-frontend)
- `src/features/search/`: input + resultados (Client Component) usando `useSelectedZone()` (F019)
  como zone_id; GET /api/search tipado. Cada resultado: precios por retailer + unidad + disponibilidad
  + frescura "actualizado hace X"; retailer sin precio indicado; orden por precio. Estados completos.
- Helper puro "hace X" testeable. E2E `search.spec.ts`: varilla en MTY, ambos retailers, orden por precio.

Cierre: `./init.sh --e2e` verde + tsc/lint/build/test:unit + review APROBADO.

**Estado:** F020 `in_progress`. M4: F019 ✅ → **F020** → F021 → F022.
