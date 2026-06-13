"use client";

/**
 * Hook client-side que consulta `GET /api/health` al montar.
 *
 * El fetch ocurre en el navegador (no en build/prerender) para que `pnpm build`
 * no dependa de que el backend esté arriba. Expone los tres estados que exige
 * la convención: cargando / error / datos.
 */
import { useEffect, useState } from "react";

import { fetchHealth } from "../api";

/** Estado del backend tal como lo ve la UI. */
export type HealthState =
  | { status: "loading" }
  | { status: "ok"; value: string }
  | { status: "error"; message: string };

export function useHealth(): HealthState {
  const [state, setState] = useState<HealthState>({ status: "loading" });

  useEffect(() => {
    let active = true;

    fetchHealth()
      .then((data) => {
        if (active) {
          setState({ status: "ok", value: data.status });
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setState({
            status: "error",
            message:
              error instanceof Error
                ? error.message
                : "No se pudo verificar el estado del backend.",
          });
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return state;
}
