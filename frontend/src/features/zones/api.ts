/**
 * Llamadas del dominio "zones" usando el cliente tipado.
 *
 * El tipo del resultado se infiere de `apiGet("/api/zones")`, que a su vez
 * deriva de `schema.d.ts` (contrato OpenAPI). No se declara a mano ningún tipo
 * de respuesta de la API: el contrato manda.
 *
 * Nota (F014): solo se expone el GET de listado. El endpoint POST
 * `/api/zones/resolve` se consumirá desde la UI de selección de zona (F019),
 * que añadirá el helper POST correspondiente al cliente.
 */
import { apiGet } from "@/lib/api/client";

/** Lista las zonas activas ordenadas por nombre. Devuelve `ZoneOut[]`. */
export function fetchZones() {
  return apiGet("/api/zones");
}
