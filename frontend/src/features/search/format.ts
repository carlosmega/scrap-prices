/**
 * Helpers de formato PUROS para la UI de búsqueda.
 *
 * Los precios llegan del contrato como strings de Decimal
 * (`PriceByRetailerOut.price`, `.price_per_piece`, `.price_per_kg`) para no
 * perder exactitud monetaria (PRD §8). Aquí solo formateamos para mostrar;
 * jamás usamos el número para cálculos monetarios.
 *
 * F031 — Normalización de unidad: el `price` es el valor NATIVO del retailer
 * (transparencia: "listado a $20,085.00 / ton"); la base de comparación
 * cross-retailer es `price_per_kg`. El orden y el "mejor precio" usan
 * `price_per_kg`; cuando falta (retailer no normalizable), la fila va al final.
 */
import type { RetailerPrice } from "./types";

/** Una fila de precio que se puede formatear/comparar (search o detalle). */
type PriceLike = Pick<
  RetailerPrice,
  "price" | "price_per_piece" | "price_per_kg" | "sale_unit"
> & { currency: string; retailer: { name: string } };

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
 * Mapea la `sale_unit` estructurada del contrato a su etiqueta corta de display
 * (tonelada→"ton", kg→"kg", pieza→"pieza"). Para unidades sin abreviatura propia
 * (`m`, `saco`, "" desconocida) devuelve el valor tal cual (transparencia).
 */
export function saleUnitLabel(saleUnit: string): string {
  switch (saleUnit) {
    case "tonelada":
      return "ton";
    case "kg":
      return "kg";
    case "pieza":
      return "pieza";
    default:
      return saleUnit;
  }
}

/**
 * Titular por fila de retailer: precio NORMALIZADO por pieza → "$236.65 / pieza".
 * Null cuando no hay `price_per_piece` (no normalizable): la UI cae al nativo.
 */
export function formatPricePerPiece(
  pricePerPiece: string | null | undefined,
  currency: string,
): string | null {
  if (pricePerPiece === null || pricePerPiece === undefined) return null;
  return `${formatPrice(pricePerPiece, currency)} / pieza`;
}

/**
 * Base de comparación: precio NORMALIZADO por kg → "$20.09 / kg".
 * Null cuando no hay `price_per_kg` (no normalizable).
 */
export function formatPricePerKg(
  pricePerKg: string | null | undefined,
  currency: string,
): string | null {
  if (pricePerKg === null || pricePerKg === undefined) return null;
  return `${formatPrice(pricePerKg, currency)} / kg`;
}

/**
 * Línea NATIVA del retailer (transparencia F031): el `price` crudo en su unidad
 * de venta → "listado a $20,085.00 / ton". Null cuando no hay precio en la zona.
 */
export function formatNativePrice(
  price: string | null | undefined,
  saleUnit: string,
  currency: string,
): string | null {
  if (price === null || price === undefined) return null;
  const unit = saleUnitLabel(saleUnit);
  const amount = formatPrice(price, currency);
  return unit ? `listado a ${amount} / ${unit}` : `listado a ${amount}`;
}

/**
 * Ordena los precios por retailer para la comparación cross-retailer (F031):
 * la base es `price_per_kg` ASCENDENTE (la unidad común y justa), NO el `price`
 * nativo crudo (que mezcla ton/kg/pieza y no es comparable). Los que no tienen
 * `price_per_kg` (no normalizable o sin precio en la zona) van al final.
 * No muta el arreglo de entrada.
 */
export function sortPricesAsc<T extends Pick<PriceLike, "price_per_kg" | "retailer">>(
  prices: T[],
): T[] {
  return [...prices].sort((a, b) => {
    const aHas = a.price_per_kg !== null && a.price_per_kg !== undefined;
    const bHas = b.price_per_kg !== null && b.price_per_kg !== undefined;
    if (aHas && bHas) {
      return Number(a.price_per_kg) - Number(b.price_per_kg);
    }
    // Sin base comparable va al final; entre dos sin base, alfabético por retailer.
    if (aHas) return -1;
    if (bHas) return 1;
    return a.retailer.name.localeCompare(b.retailer.name, "es-MX");
  });
}

/**
 * Índice (en el arreglo de entrada original) de la fila con MENOR `price_per_kg`,
 * i.e. el "mejor precio" cross-retailer (F031). -1 si ninguna fila es
 * normalizable. Empate: gana la primera encontrada (orden estable).
 */
export function bestPriceIndex(
  prices: ReadonlyArray<Pick<PriceLike, "price_per_kg">>,
): number {
  let best = -1;
  let bestValue = Number.POSITIVE_INFINITY;
  prices.forEach((p, i) => {
    if (p.price_per_kg === null || p.price_per_kg === undefined) return;
    const value = Number(p.price_per_kg);
    if (Number.isNaN(value)) return;
    if (value < bestValue) {
      bestValue = value;
      best = i;
    }
  });
  return best;
}
