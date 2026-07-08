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
 * Busca por texto en una zona y devuelve el `SearchOut` completo (F033):
 * canónicos comparados (`results`) + hallazgos crudos por tienda
 * (`raw_results`) + info de la corrida en vivo (`live`).
 *
 * No se manda `live`: aplica el default del contrato (`auto`) — si no hay
 * datos frescos para término+zona, el backend consulta las tiendas EN VIVO y
 * la petición puede tardar varios segundos (~2–25 s). Por eso el cliente HTTP
 * no impone timeout y la UI muestra un mensaje progresivo mientras espera.
 *
 * @param q      término de búsqueda (p.ej. "varilla").
 * @param zoneId id de la zona seleccionada (F019).
 * @param sort   orden de los resultados ("price": menor primero; "name": A-Z).
 */
export function fetchSearch(q: string, zoneId: string, sort: SearchSort) {
  return apiGetQuery("/api/search", { q, zone_id: zoneId, sort });
}
