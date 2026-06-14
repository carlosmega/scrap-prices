"use client";

/**
 * Hook client-side del detalle de producto (F021). Carga
 * `GET /api/products/{id}?zone_id=` al montar y cuando cambian `id`/`zoneId`, y
 * expone los estados que exige la convención: cargando / error / datos, más un
 * caso explícito "no encontrado" (404 del backend: producto o zona inexistente).
 *
 * - Sin zona seleccionada NO carga (la UI invita a elegirla).
 * - El `fetch` real vive en `lib/api/client.ts` vía `fetchProductDetail`.
 * - Un flag `active` evita actualizar el estado tras desmontar / cambio de id.
 */
import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { fetchProductDetail } from "../api";
import type { ProductDetail } from "../types";

/** Estado del detalle tal como lo consume la UI. */
export type ProductDetailState =
  | { status: "no-zone" }
  | { status: "loading" }
  | { status: "ready"; detail: ProductDetail }
  | { status: "not-found" }
  | { status: "error"; message: string };

export function useProductDetail(
  id: string,
  zoneId: string | null
): ProductDetailState {
  const [state, setState] = useState<ProductDetailState>(
    zoneId === null ? { status: "no-zone" } : { status: "loading" }
  );

  useEffect(() => {
    if (zoneId === null) {
      setState({ status: "no-zone" });
      return;
    }

    let active = true;
    setState({ status: "loading" });

    fetchProductDetail(id, zoneId)
      .then((detail) => {
        if (active) {
          setState({ status: "ready", detail });
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        if (error instanceof ApiError && error.status === 404) {
          setState({ status: "not-found" });
          return;
        }
        setState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "No se pudo cargar el producto.",
        });
      });

    return () => {
      active = false;
    };
  }, [id, zoneId]);

  return state;
}
