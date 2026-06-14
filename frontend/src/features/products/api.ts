/**
 * Llamadas del dominio "products" usando el cliente tipado.
 *
 * El tipo del resultado se infiere de `apiGetPath`, que deriva de `schema.d.ts`
 * (contrato OpenAPI `GET /api/products/{id}`). No se declara a mano ningún tipo
 * de respuesta ni de parámetros: el contrato manda. El único punto de `fetch`
 * sigue siendo `lib/api/client.ts`.
 */
import { apiGetPath } from "@/lib/api/client";

/**
 * Trae el detalle de un canónico en una zona: producto + `specs`, precios
 * actuales por retailer e historial. Devuelve `ProductDetailOut`.
 *
 * El backend responde 404 si el producto no existe/está inactivo o si la zona no
 * existe/está inactiva; el cliente lo traduce a `ApiError` con `status === 404`,
 * que la UI muestra como "producto no encontrado".
 *
 * @param id     id del producto canónico (de la ruta `/products/{id}`).
 * @param zoneId id de la zona seleccionada (F019).
 */
export function fetchProductDetail(id: string, zoneId: string) {
  return apiGetPath("/api/products/{id}", { id }, { zone_id: zoneId });
}
