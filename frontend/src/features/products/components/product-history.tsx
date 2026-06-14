/**
 * Historial de precio: lista de lecturas (retailer, precio, fecha) ordenadas de
 * la más reciente a la más antigua. Presentación pura: sin `"use client"`.
 *
 * El contrato ya entrega `history` con orden `-captured_at`, pero ordenamos aquí
 * de forma defensiva por `captured_at` descendente para no depender del orden de
 * la red. Reutiliza `formatPrice` (string del Decimal) del dominio search y
 * `formatHistoryDate` del dominio products.
 */
import { formatPrice } from "@/features/search/format";
import { formatHistoryDate } from "../format";
import type { ProductHistoryPoint } from "../types";

/** Ordena por fecha descendente (reciente → antiguo) sin mutar la entrada. */
function sortRecentFirst(
  history: ProductHistoryPoint[]
): ProductHistoryPoint[] {
  return [...history].sort(
    (a, b) =>
      new Date(b.captured_at).getTime() - new Date(a.captured_at).getTime()
  );
}

export function ProductHistory({
  history,
}: {
  history: ProductHistoryPoint[];
}) {
  if (history.length === 0) {
    return (
      <p
        className="text-sm text-muted-foreground"
        data-testid="product-history-empty"
      >
        Aún no hay historial de precio para este producto en tu zona.
      </p>
    );
  }

  const ordered = sortRecentFirst(history);

  return (
    <ul
      className="flex flex-col divide-y divide-foreground/10"
      data-testid="product-history"
    >
      {ordered.map((point, index) => (
        <li
          key={`${point.retailer.slug}-${point.captured_at}-${index}`}
          className="flex items-center justify-between gap-4 py-2"
          data-testid="product-history-row"
        >
          <div className="flex flex-col gap-0.5">
            <span className="font-medium text-foreground">
              {point.retailer.name}
            </span>
            <span className="text-xs text-muted-foreground">
              {formatHistoryDate(point.captured_at)}
            </span>
          </div>
          <span className="text-sm font-semibold tabular-nums text-foreground">
            {formatPrice(point.price, point.currency)}
          </span>
        </li>
      ))}
    </ul>
  );
}
