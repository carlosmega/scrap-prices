"use client";

/**
 * Hook client-side de la búsqueda (F020 + F033). Orquesta query + orden + zona
 * y expone los estados que exige la convención: inicial / cargando / error /
 * vacío / datos. El `fetch` real vive en `lib/api/client.ts` vía `fetchSearch`.
 *
 * - Sin zona seleccionada NO busca (la UI invita a elegir zona).
 * - La búsqueda se dispara explícitamente (`submit`) y se re-ejecuta al cambiar
 *   el orden si ya hay un término activo, sin perder los resultados.
 * - Una "generación" monótona evita condiciones de carrera: solo la respuesta de
 *   la última petición disparada actualiza el estado.
 *
 * F033: la respuesta es el objeto `SearchOut` — además de los canónicos
 * comparados (`results`) trae los hallazgos crudos por tienda (`rawResults`) y
 * la info de la corrida en vivo (`live`, null si no se disparó). "Vacío" es
 * ahora "ni canónicos NI crudos"; `live` se conserva también en vacío para que
 * la UI pueda explicar qué pasó con cada tienda (p.ej. bloqueada).
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { fetchSearch, type SearchSort } from "../api";
import type { LiveInfo, RawResult, SearchResult } from "../types";

/** Estado de la búsqueda tal como lo consume la UI. */
export type SearchState =
  | { status: "idle" }
  | { status: "loading" }
  | {
      status: "ready";
      results: SearchResult[];
      rawResults: RawResult[];
      live: LiveInfo | null;
    }
  | { status: "empty"; live: LiveInfo | null }
  | { status: "error"; message: string };

export interface UseSearch {
  /** Texto actual del input (controlado). */
  query: string;
  /** Actualiza el texto del input. */
  setQuery: (value: string) => void;
  /** Orden activo (price/name). */
  sort: SearchSort;
  /** Cambia el orden; re-busca si hay un término activo. */
  setSort: (value: SearchSort) => void;
  /** Dispara la búsqueda con el término actual (Enter o botón). */
  submit: () => void;
  /** Estado de la búsqueda (idle/loading/ready/empty/error). */
  state: SearchState;
}

export function useSearch(zoneId: string | null): UseSearch {
  const [query, setQuery] = useState("");
  const [sort, setSortState] = useState<SearchSort>("price");
  const [state, setState] = useState<SearchState>({ status: "idle" });

  // Término efectivamente buscado (no el del input, que el usuario puede seguir
  // tecleando). Permite re-ordenar sin re-teclear y evita buscar en cada pulsación.
  const [activeQuery, setActiveQuery] = useState<string | null>(null);

  // Generación monótona: descarta respuestas de peticiones obsoletas.
  const generation = useRef(0);

  const run = useCallback(
    (term: string, order: SearchSort) => {
      const trimmed = term.trim();
      if (zoneId === null || trimmed === "") {
        return;
      }
      setActiveQuery(trimmed);
      generation.current += 1;
      const current = generation.current;
      setState({ status: "loading" });

      fetchSearch(trimmed, zoneId, order)
        .then((data) => {
          if (current !== generation.current) {
            return;
          }
          const live = data.live ?? null;
          setState(
            data.results.length === 0 && data.raw_results.length === 0
              ? { status: "empty", live }
              : {
                  status: "ready",
                  results: data.results,
                  rawResults: data.raw_results,
                  live,
                }
          );
        })
        .catch((error: unknown) => {
          if (current !== generation.current) {
            return;
          }
          setState({
            status: "error",
            message:
              error instanceof Error
                ? error.message
                : "No se pudo completar la búsqueda.",
          });
        });
    },
    [zoneId]
  );

  const submit = useCallback(() => {
    run(query, sort);
  }, [run, query, sort]);

  const setSort = useCallback(
    (value: SearchSort) => {
      setSortState(value);
      if (activeQuery !== null) {
        run(activeQuery, value);
      }
    },
    [run, activeQuery]
  );

  // Si se deselecciona la zona (o cambia a null), volvemos a "idle": no tiene
  // sentido mostrar resultados de una zona que ya no está elegida.
  useEffect(() => {
    if (zoneId === null) {
      generation.current += 1;
      setActiveQuery(null);
      setState({ status: "idle" });
    }
  }, [zoneId]);

  return { query, setQuery, sort, setSort, submit, state };
}
