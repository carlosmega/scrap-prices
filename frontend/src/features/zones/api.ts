/**
 * Llamadas del dominio "zones" usando el cliente tipado.
 *
 * El tipo del resultado se infiere de `apiGet`/`apiPost`, que a su vez derivan
 * de `schema.d.ts` (contrato OpenAPI). No se declara a mano ningún tipo de
 * respuesta de la API: el contrato manda.
 *
 * Nota (F019): además del GET de listado (F014) se añade el helper del POST
 * `/api/zones/resolve`, que consume la UI de "usar mi ubicación".
 */
import { apiGet, apiPost } from "@/lib/api/client";

/** Lista las zonas activas ordenadas por nombre. Devuelve `ZoneOut[]`. */
export function fetchZones() {
  return apiGet("/api/zones");
}

/**
 * Resuelve la zona activa más cercana a unas coordenadas. Devuelve `ZoneOut`.
 * El backend responde 404 (sin cobertura) → el cliente lanza `ApiError` con
 * `status === 404`, que la UI traduce a un mensaje amable.
 */
export function resolveZone(coords: { lat: number; lng: number }) {
  return apiPost("/api/zones/resolve", coords);
}
