/**
 * Llamadas del dominio "retailers" usando el cliente tipado.
 *
 * El tipo del resultado se infiere de `apiGet("/api/retailers")`, que a su vez
 * deriva de `schema.d.ts` (contrato OpenAPI). No se declara a mano ningún tipo
 * de respuesta de la API: el contrato manda.
 *
 * Nota (F018): paso de contrato, sin UI. Este helper es el punto de entrada del
 * dominio para cuando exista la pantalla de diagnóstico de scrapers; expone el
 * GET de listado interno (incluye retailers inactivos), ordenado por nombre.
 */
import { apiGet } from "@/lib/api/client";

/** Lista todos los retailers (incluye inactivos) ordenados por nombre. Devuelve `RetailerOut[]`. */
export function fetchRetailers() {
  return apiGet("/api/retailers");
}
