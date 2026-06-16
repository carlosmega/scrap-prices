/**
 * Tarjeta de un resultado de búsqueda: el canónico (nombre + unidad) y una fila
 * por retailer con precio, disponibilidad y frescura ("actualizado hace X").
 *
 * No es Client Component: es presentación pura sobre datos ya cargados, así que
 * vive sin `"use client"` (el estado/interactividad están en `SearchPanel`).
 *
 * F031 — Normalización de unidad: cada retailer lista en su propia unidad
 * (HD por tonelada, CR por kg). El titular muestra el NORMALIZADO por pieza
 * ("$236.65 / pieza"), el secundario el NATIVO ("listado a $20,085.00 / ton") y
 * el $/kg (base de comparación). Las filas se ordenan por $/kg ascendente y la
 * de menor $/kg se marca como "mejor precio" (B1·CA4). Cuando un retailer no es
 * normalizable se cae al nativo con nota "sin normalizar"; un retailer sin
 * precio en la zona se indica explícitamente (B1·CA5).
 */
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { AddToQuoteButton } from "@/features/lists/components/add-to-quote-button";

import {
  bestPriceIndex,
  formatNativePrice,
  formatPrice,
  formatPricePerKg,
  formatPricePerPiece,
  sortPricesAsc,
} from "../format";
import { freshnessLabel } from "../relative-time";
import type { SearchResult } from "../types";

export function ResultCard({
  result,
  zoneId,
}: {
  result: SearchResult;
  /** Zona activa; se propaga al botón "Agregar a mi cotización". */
  zoneId: string | null;
}) {
  const { canonical_product: product, prices } = result;
  const orderedPrices = sortPricesAsc(prices);
  const bestIndex = bestPriceIndex(orderedPrices);

  return (
    <Card className="w-full" data-testid="search-result">
      <CardHeader>
        <CardTitle>
          <Link
            href={`/products/${product.id}`}
            className="underline-offset-4 hover:underline"
            data-testid="search-result-link"
          >
            {product.name}
          </Link>
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          {product.category} · por {product.unit}
        </p>
      </CardHeader>
      <CardContent>
        <ul className="flex flex-col divide-y divide-foreground/10">
          {orderedPrices.map((entry, index) => {
            const hasPrice =
              entry.price !== null && entry.price !== undefined;
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
            // "Sin normalizar": hay precio nativo pero no se pudo normalizar.
            const isUnnormalized = hasPrice && headline === null && perKg === null;

            return (
              <li
                key={entry.retailer.slug}
                className="flex items-center justify-between gap-4 py-2"
                data-testid="retailer-row"
                data-retailer={entry.retailer.slug}
              >
                <div className="flex flex-col">
                  <span className="flex items-center gap-2 font-medium text-foreground">
                    {entry.retailer.name}
                    {isBest ? (
                      <Badge data-testid="best-price-badge">mejor precio</Badge>
                    ) : null}
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
                  <div className="flex items-center gap-3">
                    <div className="flex flex-col items-end">
                      <span
                        className="text-base font-semibold tabular-nums text-foreground"
                        data-testid="retailer-price"
                      >
                        {headline ??
                          formatPrice(entry.price as string, entry.currency)}
                      </span>
                      {native ? (
                        <span
                          className="text-xs text-muted-foreground tabular-nums"
                          data-testid="retailer-native-price"
                        >
                          {native}
                        </span>
                      ) : null}
                      {perKg ? (
                        <span
                          className="text-xs text-muted-foreground tabular-nums"
                          data-testid="retailer-price-per-kg"
                        >
                          {perKg}
                        </span>
                      ) : null}
                      {isUnnormalized ? (
                        <span
                          className="text-xs text-muted-foreground"
                          data-testid="retailer-unnormalized"
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
