/**
 * Llamadas del dominio "health" usando el cliente tipado.
 *
 * El tipo del resultado se infiere de `apiGet("/api/health")`, que a su vez
 * deriva de `schema.d.ts` (contrato OpenAPI). No se declara a mano ningún tipo
 * de respuesta de la API: el contrato manda.
 */
import { apiGet } from "@/lib/api/client";

/** Consulta el estado del backend. Devuelve `{ status: string }` (HealthOut). */
export function fetchHealth() {
  return apiGet("/api/health");
}
