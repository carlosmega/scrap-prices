/**
 * Tarjeta de un resultado de búsqueda: el canónico (nombre + unidad) y una fila
 * por retailer con precio, disponibilidad y frescura ("actualizado hace X").
 *
 * No es Client Component: es presentación pura sobre datos ya cargados, así que
 * vive sin `"use client"` (el estado/interactividad están en `SearchPanel`).
 * Las filas se ordenan con el menor precio primero (B1·CA4) y un retailer sin
 * precio en la zona se indica explícitamente (B1·CA5).
 */
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { formatPrice, sortPricesAsc } from "../format";
import { freshnessLabel } from "../relative-time";
import type { SearchResult } from "../types";

export function ResultCard({ result }: { result: SearchResult }) {
  const { canonical_product: product, prices } = result;
  const orderedPrices = sortPricesAsc(prices);

  return (
    <Card className="w-full" data-testid="search-result">
      <CardHeader>
        <CardTitle>{product.name}</CardTitle>
        <p className="text-sm text-muted-foreground">
          {product.category} · por {product.unit}
        </p>
      </CardHeader>
      <CardContent>
        <ul className="flex flex-col divide-y divide-foreground/10">
          {orderedPrices.map((entry) => {
            const hasPrice =
              entry.price !== null && entry.price !== undefined;
            return (
              <li
                key={entry.retailer.slug}
                className="flex items-center justify-between gap-4 py-2"
                data-testid="retailer-row"
                data-retailer={entry.retailer.slug}
              >
                <div className="flex flex-col">
                  <span className="font-medium text-foreground">
                    {entry.retailer.name}
                  </span>
                  {hasPrice ? (
                    <span
                      className="text-xs text-muted-foreground"
                      data-testid="retailer-freshness"
                    >
                      {freshnessLabel(entry.captured_at)} ·{" "}
                      {entry.is_available ? "disponible" : "sin disponibilidad"}
                    </span>
                  ) : null}
                </div>

                {hasPrice ? (
                  <span
                    className="text-base font-semibold tabular-nums text-foreground"
                    data-testid="retailer-price"
                  >
                    {formatPrice(entry.price as string, entry.currency)}
                  </span>
                ) : (
                  <span
                    className="text-sm text-muted-foreground"
                    data-testid="retailer-no-price"
                  >
                    sin precio en tu zona
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      </CardContent>
    </Card>
  );
}
