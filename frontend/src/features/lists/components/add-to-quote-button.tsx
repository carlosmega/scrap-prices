"use client";

/**
 * Botón "Agregar a mi cotización" (F022).
 *
 * Reutilizable: aparece por retailer-product (un SKU con precio) tanto en la
 * tarjeta de búsqueda (F020) como en el detalle (F021). Agrega `quantity` (1 por
 * defecto) al SKU; en el primer uso el hook crea la lista por defecto de la
 * sesión. Muestra feedback transitorio (agregando / agregado / error).
 *
 * `"use client"` vive aquí (lo más abajo posible): las tarjetas/listas que lo
 * embeben siguen siendo presentación pura.
 */
import { useCallback, useRef, useState } from "react";
import { Check, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";

import { useQuote } from "../hooks/use-quote";

type AddState = "idle" | "adding" | "added" | "error";

export function AddToQuoteButton({
  retailerProductId,
  zoneId,
  quantity = 1,
  label = "Agregar a mi cotización",
}: {
  /** SKU a agregar (`PriceByRetailerOut.retailer_product_id`). */
  retailerProductId: string;
  /** Zona actual; fija la zona de la lista nueva (para el snapshot). */
  zoneId: string | null;
  /** Cantidad a agregar (>= 1). Por defecto 1. */
  quantity?: number;
  /** Texto del botón (compacto en filas, completo en el detalle). */
  label?: string;
}) {
  const { add } = useQuote();
  const [state, setState] = useState<AddState>("idle");
  const resetTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const onClick = useCallback(async () => {
    if (resetTimer.current !== null) {
      clearTimeout(resetTimer.current);
    }
    setState("adding");
    try {
      await add(retailerProductId, quantity, zoneId);
      setState("added");
    } catch {
      setState("error");
    } finally {
      resetTimer.current = setTimeout(() => setState("idle"), 2500);
    }
  }, [add, retailerProductId, quantity, zoneId]);

  const isAdding = state === "adding";

  return (
    <Button
      type="button"
      size="sm"
      variant={state === "added" ? "secondary" : "outline"}
      onClick={onClick}
      disabled={isAdding}
      data-testid="add-to-quote"
      data-state={state}
      aria-live="polite"
    >
      {state === "added" ? (
        <Check aria-hidden className="size-4" />
      ) : (
        <Plus aria-hidden className="size-4" />
      )}
      {state === "adding"
        ? "Agregando…"
        : state === "added"
          ? "Agregado"
          : state === "error"
            ? "Reintentar"
            : label}
    </Button>
  );
}
