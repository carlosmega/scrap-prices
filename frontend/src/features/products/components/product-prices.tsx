/**
 * Precios ACTUALES por retailer en la zona: precio, disponibilidad, frescura
 * ("hace X") y enlace a la ficha original del retailer (target _blank, rel
 * noopener). Presentación pura: sin `"use client"`.
 *
 * Reutiliza los helpers del dominio "search": formato/orden de precios y
 * `freshnessLabel` (el helper de frescura de F020 que la spec pide reaprovechar).
 *
 * F031 — Normalización de unidad (paridad con la tarjeta de búsqueda): titular
 * NORMALIZADO por pieza, secundario NATIVO ("listado a $X / ton") y $/kg (base
 * de comparación). Filas ordenadas por $/kg ascendente; la de menor $/kg se
 * marca como "mejor precio". Fallback "sin normalizar" cuando falta el dato; un
 * retailer sin precio en la zona se indica explícitamente.
 */
import { ExternalLink } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { AddToQuoteButton } from "@/features/lists/components/add-to-quote-button";
import {
  bestPriceIndex,
  formatNativePrice,
  formatPrice,
  formatPricePerKg,
  formatPricePerPiece,
  sortPricesAsc,
} from "@/features/search/format";
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
  const bestIndex = bestPriceIndex(ordered);

  return (
    <ul
      className="flex flex-col divide-y divide-foreground/10"
      data-testid="product-prices"
    >
      {ordered.map((entry, index) => {
        const hasPrice = entry.price !== null && entry.price !== undefined;
        const isBest = index === bestIndex;
        const headline = formatPricePerPiece(
          entry.price_per_piece,
          entry.currency,
        );
        const perKg = formatPricePerKg(entry.price_per_kg, entry.currency);
        const native = formatNativePrice(
          entry.price,
          entry.sale_unit,
          entry.currency,
        );
        const isUnnormalized = hasPrice && headline === null && perKg === null;

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
              {isBest ? (
                <Badge
                  className="w-fit"
                  data-testid="product-best-price-badge"
                >
                  mejor precio
                </Badge>
              ) : null}
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
                <div className="flex flex-col items-end">
                  <span
                    className="text-base font-semibold tabular-nums text-foreground"
                    data-testid="product-retailer-price"
                  >
                    {headline ??
                      formatPrice(entry.price as string, entry.currency)}
                  </span>
                  {native ? (
                    <span
                      className="text-xs text-muted-foreground tabular-nums"
                      data-testid="product-retailer-native-price"
                    >
                      {native}
                    </span>
                  ) : null}
                  {perKg ? (
                    <span
                      className="text-xs text-muted-foreground tabular-nums"
                      data-testid="product-retailer-price-per-kg"
                    >
                      {perKg}
                    </span>
                  ) : null}
                  {isUnnormalized ? (
                    <span
                      className="text-xs text-muted-foreground"
                      data-testid="product-retailer-unnormalized"
                    >
                      sin normalizar
                    </span>
                  ) : null}
                </div>
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
