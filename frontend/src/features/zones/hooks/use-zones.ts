"use client";

/**
 * Hook client-side que lista las zonas activas (`GET /api/zones`) al montar.
 *
 * Expone los tres estados que exige la convención: cargando / error / datos. El
 * fetch ocurre en el navegador (no en build/prerender), igual que `useHealth`.
 */
import { useEffect, useState } from "react";

import { fetchZones } from "../api";
import type { Zone } from "../types";

/** Estado de la lista de zonas tal como la ve la UI. */
export type ZonesState =
  | { status: "loading" }
  | { status: "ready"; zones: Zone[] }
  | { status: "error"; message: string };

export function useZones(): ZonesState {
  const [state, setState] = useState<ZonesState>({ status: "loading" });

  useEffect(() => {
    let active = true;

    fetchZones()
      .then((zones) => {
        if (active) {
          setState({ status: "ready", zones });
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setState({
            status: "error",
            message:
              error instanceof Error
                ? error.message
                : "No se pudieron cargar las zonas.",
          });
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return state;
}
