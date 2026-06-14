"use client";

/**
 * Detalle de producto (Client Component) — corazón de F021.
 *
 * Recibe el `id` de la ruta (`/products/[id]`) y toma la zona de
 * `useSelectedZone()` (F019). Con ambos, carga `GET /api/products/{id}?zone_id=`
 * vía `useProductDetail` y renderiza los estados que exige la convención:
 * sin-zona / cargando / error / no-encontrado / datos.
 *
 * `"use client"` vive aquí (lo más abajo posible): la ruta `page.tsx` sigue
 * siendo Server Component y solo compone este organismo.
 */
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

import { useSelectedZone } from "@/features/zones/hooks/use-selected-zone";
import { useProductDetail } from "../hooks/use-product-detail";
import { ProductHistory } from "./product-history";
import { ProductPrices } from "./product-prices";
import { ProductSpecs } from "./product-specs";

/** Enlace de vuelta a la búsqueda, presente en todos los estados. */
function BackToSearch() {
  return (
    <Button asChild variant="ghost" size="sm" className="self-start">
      <Link href="/" data-testid="product-back">
        <ArrowLeft aria-hidden className="size-4" />
        Volver a la búsqueda
      </Link>
    </Button>
  );
}

export function ProductDetail({ id }: { id: string }) {
  const { selectedZone } = useSelectedZone();
  const zoneId = selectedZone?.id ?? null;
  const state = useProductDetail(id, zoneId);

  return (
    <div className="flex w-full max-w-2xl flex-col gap-4">
      <BackToSearch />

      {state.status === "no-zone" && (
        <Card className="w-full" data-testid="product-needs-zone">
          <CardHeader>
            <CardTitle>Elige tu zona</CardTitle>
            <CardDescription>
              Los precios y el historial dependen de tu zona.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p
              className="text-sm text-muted-foreground"
              role="status"
              aria-live="polite"
            >
              Vuelve a la búsqueda y selecciona una zona para ver el detalle de
              este producto.
            </p>
          </CardContent>
        </Card>
      )}

      {state.status === "loading" && (
        <Card className="w-full" data-testid="product-loading">
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
              Cargando producto…
            </p>
          </CardContent>
        </Card>
      )}

      {state.status === "not-found" && (
        <Card className="w-full" data-testid="product-not-found">
          <CardHeader>
            <CardTitle>Producto no encontrado</CardTitle>
            <CardDescription>
              No pudimos encontrar este producto en tu zona.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p
              className="text-sm text-muted-foreground"
              role="status"
              aria-live="polite"
            >
              Es posible que el producto ya no esté disponible. Prueba buscar de
              nuevo desde el inicio.
            </p>
          </CardContent>
        </Card>
      )}

      {state.status === "error" && (
        <Card className="w-full" data-testid="product-error">
          <CardContent className="pt-(--card-spacing)">
            <p
              className="flex items-center gap-2 text-sm text-destructive"
              role="status"
              aria-live="polite"
            >
              <span aria-hidden className="size-2 rounded-full bg-destructive" />
              No se pudo cargar el producto. Revisa tu conexión e inténtalo de
              nuevo.
            </p>
          </CardContent>
        </Card>
      )}

      {state.status === "ready" && (
        <article
          className="flex flex-col gap-4"
          data-testid="product-detail"
        >
          <Card className="w-full">
            <CardHeader>
              <CardTitle className="text-lg">
                {state.detail.canonical_product.name}
              </CardTitle>
              <CardDescription>
                {state.detail.canonical_product.category} · por{" "}
                {state.detail.canonical_product.unit}
                {selectedZone ? (
                  <>
                    {" · "}
                    <span className="font-medium text-foreground">
                      {selectedZone.name}
                    </span>
                  </>
                ) : null}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ProductSpecs specs={state.detail.canonical_product.specs} />
            </CardContent>
          </Card>

          <Card className="w-full">
            <CardHeader>
              <CardTitle className="text-base">Precios por retailer</CardTitle>
              <CardDescription>
                Precio más reciente de cada retailer en tu zona.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ProductPrices prices={state.detail.prices} zoneId={zoneId} />
            </CardContent>
          </Card>

          <Card className="w-full">
            <CardHeader>
              <CardTitle className="text-base">Historial de precio</CardTitle>
              <CardDescription>
                Lecturas anteriores, de la más reciente a la más antigua.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ProductHistory history={state.detail.history} />
            </CardContent>
          </Card>
        </article>
      )}
    </div>
  );
}
