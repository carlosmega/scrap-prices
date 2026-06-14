/**
 * Tipos derivados del contrato para el dominio "products".
 *
 * NO se declara a mano ninguna forma de la API: tanto el detalle como sus partes
 * (canónico, precios por retailer, puntos de historial) se infieren del retorno
 * de `fetchProductDetail()` (que a su vez deriva de `schema.d.ts`). Si el
 * contrato cambia, estos tipos cambian con él sin tocar nada.
 */
import type { fetchProductDetail } from "./api";

/** Detalle completo de un producto (`ProductDetailOut`). */
export type ProductDetail = Awaited<ReturnType<typeof fetchProductDetail>>;

/** El canónico expandido con `specs` (`CanonicalProductDetailOut`). */
export type ProductCanonical = ProductDetail["canonical_product"];

/** El precio actual de un retailer dentro del detalle (`PriceByRetailerOut`). */
export type ProductPrice = ProductDetail["prices"][number];

/** Una lectura histórica de precio (`PriceHistoryPointOut`). */
export type ProductHistoryPoint = ProductDetail["history"][number];
