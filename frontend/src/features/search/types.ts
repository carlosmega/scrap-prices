/**
 * Tipos derivados del contrato para el dominio "search".
 *
 * NO se declara a mano ninguna forma de la API: tanto el resultado de búsqueda
 * como su precio por retailer se infieren del retorno de `fetchSearch()` (que a
 * su vez deriva de `schema.d.ts`). Si el contrato cambia, estos tipos cambian
 * con él sin tocar nada.
 */
import type { fetchSearch } from "./api";

/** Un resultado de búsqueda (elemento de `SearchResultOut[]`). */
export type SearchResult = Awaited<ReturnType<typeof fetchSearch>>[number];

/** El precio de un retailer dentro de un resultado (`PriceByRetailerOut`). */
export type RetailerPrice = SearchResult["prices"][number];
