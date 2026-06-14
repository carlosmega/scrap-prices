/**
 * Llamadas del dominio "search" usando el cliente tipado.
 *
 * El tipo del resultado se infiere de `apiGetQuery`, que deriva de `schema.d.ts`
 * (contrato OpenAPI `GET /api/search`). No se declara a mano ningún tipo de
 * respuesta ni de query: el contrato manda. El único punto de `fetch` sigue
 * siendo `lib/api/client.ts`.
 */
import { apiGetQuery } from "@/lib/api/client";

/** Criterios de orden soportados por `GET /api/search` (PRD §12). */
export type SearchSort = "price" | "name";

/**
 * Busca canónicos por texto en una zona y devuelve `SearchResultOut[]`.
 *
 * @param q      término de búsqueda (p.ej. "varilla").
 * @param zoneId id de la zona seleccionada (F019).
 * @param sort   orden de los resultados ("price": menor primero; "name": A-Z).
 */
export function fetchSearch(q: string, zoneId: string, sort: SearchSort) {
  return apiGetQuery("/api/search", { q, zone_id: zoneId, sort });
}
