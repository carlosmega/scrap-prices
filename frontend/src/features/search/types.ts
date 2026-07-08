/**
 * Tipos derivados del contrato para el dominio "search".
 *
 * NO se declara a mano ninguna forma de la API: todo se infiere del retorno de
 * `fetchSearch()` (que a su vez deriva de `schema.d.ts`). Si el contrato
 * cambia, estos tipos cambian con él sin tocar nada.
 *
 * F033 (BREAKING): la respuesta de `GET /api/search` pasó de lista a objeto
 * `SearchOut` con tres partes: `results` (canónicos comparados, igual que
 * antes), `raw_results` (hallazgos por tienda aún sin matchear) y `live`
 * (info de la corrida en vivo; null/ausente cuando no se disparó).
 */
import type { fetchSearch } from "./api";

/** La respuesta completa de la búsqueda (`SearchOut`). */
export type SearchResponse = Awaited<ReturnType<typeof fetchSearch>>;

/** Un resultado canónico comparado (elemento de `SearchOut.results`). */
export type SearchResult = SearchResponse["results"][number];

/** El precio de un retailer dentro de un resultado (`PriceByRetailerOut`). */
export type RetailerPrice = SearchResult["prices"][number];

/** Un hallazgo crudo de una tienda, sin matchear (`RawRetailerResultOut`). */
export type RawResult = SearchResponse["raw_results"][number];

/** Info de la corrida en vivo (`LiveSearchInfoOut`). */
export type LiveInfo = NonNullable<SearchResponse["live"]>;

/** Cómo le fue a UN retailer en la corrida (`LiveRetailerStatusOut`). */
export type LiveRetailerStatus = LiveInfo["retailers"][number];
