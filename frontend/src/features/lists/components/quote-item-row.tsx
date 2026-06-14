"use client";

/**
 * Fila de un ítem de la cotización (F022).
 *
 * Muestra el snapshot inmutable: retailer, nombre, `captured_price` + cuándo se
 * capturó (`captured_at`) y el `line_total` (todo del backend; la UI no recalcula
 * precios). Permite editar la cantidad (PATCH) y quitar el ítem (DELETE), con un
 * estado `busy` mientras la operación está en vuelo.
 *
 * `"use client"`: tiene controles interactivos (cantidad, quitar).
 */
import { useCallback, useState } from "react";
import { Minus, Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";

import { formatPrice } from "@/features/search/format";
import { freshnessLabel } from "@/features/search/relative-time";

import type { ListItem } from "../types";

export function QuoteItemRow({
  item,
  onSetQuantity,
  onRemove,
}: {
  item: ListItem;
  onSetQuantity: (itemId: string, quantity: number) => Promise<void>;
  onRemove: (itemId: string) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);

  const changeQuantity = useCallback(
    async (next: number) => {
      if (next < 1 || busy) {
        return;
      }
      setBusy(true);
      try {
        await onSetQuantity(item.id, next);
      } finally {
        setBusy(false);
      }
    },
    [busy, item.id, onSetQuantity]
  );

  const remove = useCallback(async () => {
    if (busy) {
      return;
    }
    setBusy(true);
    try {
      await onRemove(item.id);
    } finally {
      setBusy(false);
    }
  }, [busy, item.id, onRemove]);

  return (
    <li
      className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between"
      data-testid="quote-item"
      data-item-id={item.id}
    >
      <div className="flex flex-col gap-0.5">
        <span
          className="font-medium text-foreground"
          data-testid="quote-item-name"
        >
          {item.product_name}
        </span>
        <span className="text-xs text-muted-foreground">
          {item.retailer.name} ·{" "}
          <span data-testid="quote-item-snapshot">
            {formatPrice(item.captured_price, "MXN")}
          </span>{" "}
          · {freshnessLabel(item.captured_at)}
        </span>
      </div>

      <div className="flex items-center gap-4">
        <div
          className="flex items-center gap-1"
          data-testid="quote-item-quantity"
        >
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="size-8"
            onClick={() => changeQuantity(item.quantity - 1)}
            disabled={busy || item.quantity <= 1}
            aria-label="Disminuir cantidad"
            data-testid="quote-item-decrement"
          >
            <Minus aria-hidden className="size-4" />
          </Button>
          <span
            className="w-8 text-center text-sm tabular-nums"
            data-testid="quote-item-quantity-value"
          >
            {item.quantity}
          </span>
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="size-8"
            onClick={() => changeQuantity(item.quantity + 1)}
            disabled={busy}
            aria-label="Aumentar cantidad"
            data-testid="quote-item-increment"
          >
            <Plus aria-hidden className="size-4" />
          </Button>
        </div>

        <span
          className="w-28 text-right text-base font-semibold tabular-nums text-foreground"
          data-testid="quote-item-line-total"
        >
          {formatPrice(item.line_total, "MXN")}
        </span>

        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-8 text-muted-foreground hover:text-destructive"
          onClick={remove}
          disabled={busy}
          aria-label="Quitar ítem"
          data-testid="quote-item-remove"
        >
          <Trash2 aria-hidden className="size-4" />
        </Button>
      </div>
    </li>
  );
}
