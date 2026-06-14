"use client";

/**
 * Indicador de la cotización para el shell (F022).
 *
 * Enlace a la página de la lista con un badge que muestra la cantidad de ítems.
 * Comparte el estado con el resto de la cotización vía `useQuote` (store en
 * memoria), así el contador sube al instante al agregar un producto. Carga el
 * detalle al montar para reflejar lo que ya había en la sesión tras una recarga.
 *
 * `"use client"`: lee estado de cliente (sesión/localStorage) y reacciona a los
 * cambios del store.
 */
import { useEffect } from "react";
import Link from "next/link";
import { ShoppingCart } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import { useQuote } from "../hooks/use-quote";

export function QuoteBadge() {
  const { itemCount, load } = useQuote();

  // Al montar, carga lo que ya hubiera en la sesión (sobrevive recarga).
  useEffect(() => {
    load();
  }, [load]);

  return (
    <Button
      asChild
      variant="outline"
      size="sm"
      className="relative"
      data-testid="quote-badge"
    >
      <Link href="/cotizacion" aria-label={`Mi cotización (${itemCount} ítems)`}>
        <ShoppingCart aria-hidden className="size-4" />
        Mi cotización
        {itemCount > 0 ? (
          <Badge
            variant="secondary"
            className="ml-1 tabular-nums"
            data-testid="quote-badge-count"
          >
            {itemCount}
          </Badge>
        ) : null}
      </Link>
    </Button>
  );
}
