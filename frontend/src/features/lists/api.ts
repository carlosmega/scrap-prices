/**
 * Llamadas del dominio "lists" (cotización) usando el cliente tipado.
 *
 * Todos los tipos de cuerpo y de respuesta se infieren de `schema.d.ts` (contrato
 * OpenAPI `/api/lists*`, de F017): aquí no se declara a mano ninguna forma de la
 * API. El único punto de `fetch` sigue siendo `lib/api/client.ts`.
 *
 * Identidad anónima: cada función recibe la `sessionKey` (de `getSessionKey()`) y
 * la pasa a los helpers, que la traducen al header `X-Session-Key`. El backend
 * scope-a las listas por esa clave (404 ante listas/ítems de otra sesión).
 */
import {
  apiDeletePath,
  apiGet,
  apiGetPath,
  apiPatchPath,
  apiPost,
  apiPostPath,
} from "@/lib/api/client";

/** Lista las listas de la sesión (resumen). */
export function fetchLists(sessionKey: string) {
  return apiGet("/api/lists", { sessionKey });
}

/** Trae el detalle de una lista (ítems + subtotal/total). */
export function fetchListDetail(listId: string, sessionKey: string) {
  return apiGetPath("/api/lists/{list_id}", { list_id: listId }, undefined, {
    sessionKey,
  });
}

/**
 * Crea una lista para la sesión. `zoneId` opcional: cuando se provee, el snapshot
 * de cada ítem que se agregue se tomará de la última observación en esa zona.
 */
export function createList(
  sessionKey: string,
  name: string,
  zoneId: string | null
) {
  return apiPost("/api/lists", { name, zone_id: zoneId }, { sessionKey });
}

/** Agrega un SKU (`retailer_product_id`) con cantidad a la lista. */
export function addItem(
  listId: string,
  sessionKey: string,
  retailerProductId: string,
  quantity: number
) {
  return apiPostPath(
    "/api/lists/{list_id}/items",
    { list_id: listId },
    { retailer_product_id: retailerProductId, quantity },
    { sessionKey }
  );
}

/** Cambia la cantidad de un ítem (el snapshot no se toca). */
export function updateItemQuantity(
  listId: string,
  itemId: string,
  sessionKey: string,
  quantity: number
) {
  return apiPatchPath(
    "/api/lists/{list_id}/items/{item_id}",
    { list_id: listId, item_id: itemId },
    { quantity },
    { sessionKey }
  );
}

/** Quita un ítem de la lista. */
export function removeItem(listId: string, itemId: string, sessionKey: string) {
  return apiDeletePath(
    "/api/lists/{list_id}/items/{item_id}",
    { list_id: listId, item_id: itemId },
    { sessionKey }
  );
}
