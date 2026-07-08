/**
 * Sección "Resultados de las tiendas (sin comparar)" (F033).
 *
 * Hallazgos CRUDOS por retailer aún sin matchear a un canónico: nombre tal
 * cual lo lista la tienda, precio NATIVO en su unidad (`sale_unit`),
 * disponibilidad, frescura "hace X" y link a la ficha (nueva pestaña). NO se
 * comparan cross-retailer (eso llega al curarlos en Admin, PRD D1); por eso se
 * agrupan por tienda en vez de mezclarse con los canónicos comparados.
 *
 * "Agregar a cotización" reutiliza el mecanismo existente (`AddToQuoteButton`
 * con `retailer_product_id`): un hallazgo crudo ES un RetailerProduct.
 *
 * Presentación pura sobre datos ya cargados: vive sin `"use client"` (el
 * estado está en `SearchPanel`; el botón de cotización trae el suyo).
 */
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { AddToQuoteButton } from "@/features/lists/components/add-to-quote-button";

import { formatRawPrice } from "../format";
import { groupRawResultsByRetailer } from "../raw-results";
import { freshnessLabel } from "../relative-time";
import type { RawResult } from "../types";

export function RawResultsSection({
  rawResults,
  zoneId,
}: {
  rawResults: RawResult[];
  /** Zona activa; se propaga al botón "Agregar a mi cotización". */
  zoneId: string | null;
}) {
  // Sin hallazgos crudos no hay sección (estado vacío de esta capa: la
  // búsqueda sigue mostrando sus canónicos o su "sin resultados" global).
  if (rawResults.length === 0) {
    return null;
  }

  const groups = groupRawResultsByRetailer(rawResults);

  return (
    <section
      className="flex flex-col gap-3"
      data-testid="raw-results-section"
      aria-label="Resultados de las tiendas (sin comparar)"
    >
      <div className="flex flex-col gap-1">
        <h2 className="text-base font-semibold text-foreground">
          Resultados de las tiendas (sin comparar)
        </h2>
        <p className="text-xs text-muted-foreground">
          Hallados tal cual en cada tienda; su precio es el nativo del retailer
          y aún no se compara entre tiendas.
        </p>
      </div>

      {groups.map((group) => (
        <Card
          key={group.slug}
          className="w-full"
          data-testid="raw-retailer-group"
          data-retailer={group.slug}
        >
          <CardHeader>
            <CardTitle>{group.name}</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col divide-y divide-foreground/10">
              {group.items.map((item) => (
                <li
                  key={item.retailer_product_id}
                  className="flex items-center justify-between gap-4 py-2"
                  data-testid="raw-result"
                  data-sku={item.external_sku}
                >
                  <div className="flex flex-col">
                    <span
                      className="font-medium text-foreground"
                      data-testid="raw-result-name"
                    >
                      {item.url ? (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="underline-offset-4 hover:underline"
                          data-testid="raw-result-link"
                        >
                          {item.raw_name}
                        </a>
                      ) : (
                        item.raw_name
                      )}
                    </span>
                    {item.brand ? (
                      <span
                        className="text-xs text-muted-foreground"
                        data-testid="raw-result-brand"
                      >
                        {item.brand}
                      </span>
                    ) : null}
                    <span
                      className="text-xs text-muted-foreground"
                      data-testid="raw-result-freshness"
                    >
                      {freshnessLabel(item.captured_at)} ·{" "}
                      {item.is_available ? "disponible" : "sin disponibilidad"}
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <span
                      className="text-base font-semibold tabular-nums text-foreground"
                      data-testid="raw-result-price"
                    >
                      {formatRawPrice(item.price, item.sale_unit, item.currency)}
                    </span>
                    <AddToQuoteButton
                      retailerProductId={item.retailer_product_id}
                      zoneId={zoneId}
                      label="Agregar"
                    />
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ))}
    </section>
  );
}
