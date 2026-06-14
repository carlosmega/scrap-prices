/**
 * Precios ACTUALES por retailer en la zona: precio, disponibilidad, frescura
 * ("hace X") y enlace a la ficha original del retailer (target _blank, rel
 * noopener). Presentación pura: sin `"use client"`.
 *
 * Reutiliza los helpers del dominio "search": `formatPrice`/`sortPricesAsc` y
 * `freshnessLabel` (el helper de frescura de F020 que la spec pide reaprovechar).
 * Las filas van con el menor precio primero; un retailer sin precio en la zona se
 * indica explícitamente (paridad con la tarjeta de búsqueda).
 */
import { ExternalLink } from "lucide-react";

import { AddToQuoteButton } from "@/features/lists/components/add-to-quote-button";
import { formatPrice, sortPricesAsc } from "@/features/search/format";
import { freshnessLabel } from "@/features/search/relative-time";
import type { ProductPrice } from "../types";

export function ProductPrices({
  prices,
  zoneId,
}: {
  prices: ProductPrice[];
  /** Zona activa; se propaga al botón "Agregar a mi cotización". */
  zoneId: string | null;
}) {
  const ordered = sortPricesAsc(prices);

  return (
    <ul
      className="flex flex-col divide-y divide-foreground/10"
      data-testid="product-prices"
    >
      {ordered.map((entry) => {
        const hasPrice = entry.price !== null && entry.price !== undefined;
        return (
          <li
            key={entry.retailer.slug}
            className="flex items-center justify-between gap-4 py-3"
            data-testid="product-retailer-row"
            data-retailer={entry.retailer.slug}
          >
            <div className="flex flex-col gap-0.5">
              <a
                href={entry.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 font-medium text-foreground underline-offset-4 hover:underline"
                data-testid="product-retailer-link"
              >
                {entry.retailer.name}
                <ExternalLink aria-hidden className="size-3.5" />
              </a>
              {hasPrice ? (
                <span
                  className="text-xs text-muted-foreground"
                  data-testid="product-retailer-freshness"
                >
                  {freshnessLabel(entry.captured_at)} ·{" "}
                  {entry.is_available ? "disponible" : "sin disponibilidad"}
                </span>
              ) : null}
            </div>

            {hasPrice ? (
              <div className="flex items-center gap-3">
                <span
                  className="text-base font-semibold tabular-nums text-foreground"
                  data-testid="product-retailer-price"
                >
                  {formatPrice(entry.price as string, entry.currency)}
                </span>
                <AddToQuoteButton
                  retailerProductId={entry.retailer_product_id}
                  zoneId={zoneId}
                  label="Agregar"
                />
              </div>
            ) : (
              <span
                className="text-sm text-muted-foreground"
                data-testid="product-retailer-no-price"
              >
                sin precio en tu zona
              </span>
            )}
          </li>
        );
      })}
    </ul>
  );
}
