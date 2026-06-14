"use client";

/**
 * Página de la cotización (`/cotizacion`, organismo de F022).
 *
 * Carga el detalle de la lista por defecto de la sesión vía `useQuote` y
 * renderiza los estados que exige la convención: cargando / error / vacío /
 * datos. Con datos, lista los ítems (snapshot + `line_total`) y muestra el
 * subtotal/total que vienen del backend (la UI NO recalcula precios). Editar
 * cantidad y quitar ítem delegan en el hook.
 *
 * `"use client"` vive aquí (lo más abajo posible): la ruta `page.tsx` es Server
 * Component y solo compone este organismo.
 */
import { useEffect } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { formatPrice } from "@/features/search/format";

import { useQuote } from "../hooks/use-quote";
import { QuoteItemRow } from "./quote-item-row";

/** Enlace de vuelta a la búsqueda, presente en todos los estados. */
function BackToSearch() {
  return (
    <Button asChild variant="ghost" size="sm" className="self-start">
      <Link href="/" data-testid="quote-back">
        <ArrowLeft aria-hidden className="size-4" />
        Volver a la búsqueda
      </Link>
    </Button>
  );
}

export function QuoteList() {
  const { state, load, setQuantity, remove } = useQuote();

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="flex w-full max-w-2xl flex-col gap-4">
      <BackToSearch />

      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Mi cotización
        </h1>
        <p className="text-sm text-muted-foreground">
          Precios fijados al momento de agregar cada producto (snapshot).
        </p>
      </header>

      {state.status === "loading" && (
        <Card className="w-full" data-testid="quote-loading">
          <CardContent className="pt-(--card-spacing)">
            <p
              className="flex items-center gap-2 text-sm text-muted-foreground"
              role="status"
              aria-live="polite"
            >
              <span
                aria-hidden
                className="size-2 animate-pulse rounded-full bg-muted-foreground"
              />
              Cargando tu cotización…
            </p>
          </CardContent>
        </Card>
      )}

      {state.status === "error" && (
        <Card className="w-full" data-testid="quote-error">
          <CardContent className="pt-(--card-spacing)">
            <p
              className="flex items-center gap-2 text-sm text-destructive"
              role="status"
              aria-live="polite"
            >
              <span aria-hidden className="size-2 rounded-full bg-destructive" />
              {state.message}
            </p>
          </CardContent>
        </Card>
      )}

      {(state.status === "empty" || state.status === "idle") && (
        <Card className="w-full" data-testid="quote-empty">
          <CardHeader>
            <CardTitle>Tu cotización está vacía</CardTitle>
            <CardDescription>
              Agrega productos desde la búsqueda o el detalle para compararlos
              aquí.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild size="sm">
              <Link href="/">Buscar materiales</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {state.status === "ready" && (
        <Card className="w-full" data-testid="quote-detail">
          <CardHeader>
            <CardTitle className="text-lg">{state.detail.name}</CardTitle>
            <CardDescription>
              {state.detail.items.length}{" "}
              {state.detail.items.length === 1 ? "producto" : "productos"} en tu
              cotización.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <ul className="flex flex-col divide-y divide-foreground/10">
              {state.detail.items.map((item) => (
                <QuoteItemRow
                  key={item.id}
                  item={item}
                  onSetQuantity={setQuantity}
                  onRemove={remove}
                />
              ))}
            </ul>

            <div className="flex items-center justify-between border-t border-foreground/10 pt-4">
              <span className="text-base font-medium text-foreground">
                Total
              </span>
              <span
                className="text-xl font-semibold tabular-nums text-foreground"
                data-testid="quote-total"
              >
                {formatPrice(state.detail.total, "MXN")}
              </span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
