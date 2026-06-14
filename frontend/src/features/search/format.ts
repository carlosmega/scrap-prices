/**
 * Helpers de formato PUROS para la UI de búsqueda.
 *
 * El precio llega del contrato como string del Decimal (`PriceByRetailerOut.price`)
 * para no perder exactitud monetaria (PRD §8). Aquí solo formateamos para mostrar;
 * jamás usamos el número para cálculos monetarios.
 */
import type { RetailerPrice } from "./types";

/**
 * Formatea un precio (string del Decimal) + moneda a "$1,234.50 MXN".
 * Si el string no es numérico, lo devuelve tal cual con la moneda (transparencia
 * del dato, RNF3).
 */
export function formatPrice(price: string, currency: string): string {
  const value = Number(price);
  if (Number.isNaN(value)) {
    return `${price} ${currency}`;
  }
  const formatted = new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(value);
  return formatted;
}

/**
 * Ordena los precios por retailer para mostrar el menor primero (B1·CA4 a nivel
 * de tarjeta): disponibles con precio ascendente, luego los que no tienen precio
 * en la zona. No muta el arreglo de entrada.
 */
export function sortPricesAsc(prices: RetailerPrice[]): RetailerPrice[] {
  return [...prices].sort((a, b) => {
    const aHas = a.price !== null && a.price !== undefined;
    const bHas = b.price !== null && b.price !== undefined;
    if (aHas && bHas) {
      return Number(a.price) - Number(b.price);
    }
    // Sin precio va al final; entre dos sin precio, alfabético por retailer.
    if (aHas) return -1;
    if (bHas) return 1;
    return a.retailer.name.localeCompare(b.retailer.name, "es-MX");
  });
}
