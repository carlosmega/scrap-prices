"use client";

/**
 * Panel de búsqueda (Client Component) — corazón de F020.
 *
 * Toma la zona de `useSelectedZone()` (F019) como `zone_id`. Si NO hay zona,
 * invita a elegirla y no busca. Con zona, ejerce `GET /api/search` vía
 * `useSearch` y renderiza los cinco estados: inicial / cargando / error / vacío
 * / datos. Incluye el control para ordenar por precio (menor primero, B1·CA4).
 *
 * `"use client"` vive aquí (lo más abajo posible): la home sigue siendo Server
 * Component y solo compone este organismo debajo del selector de zona.
 */
import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";

import { useSelectedZone } from "@/features/zones/hooks/use-selected-zone";
import type { SearchSort } from "../api";
import { useSearch } from "../hooks/use-search";
import { ResultCard } from "./result-card";

const SORT_OPTIONS: ReadonlyArray<{ value: SearchSort; label: string }> = [
  { value: "price", label: "Precio (menor primero)" },
  { value: "name", label: "Nombre (A-Z)" },
];

export function SearchPanel() {
  const { selectedZone } = useSelectedZone();
  const zoneId = selectedZone?.id ?? null;
  const { query, setQuery, sort, setSort, submit, state } = useSearch(zoneId);

  // Sin zona: invitamos a elegirla y no buscamos (B1, A1·CA dependencia).
  if (zoneId === null) {
    return (
      <Card className="w-full max-w-md" data-testid="search-panel">
        <CardHeader>
          <CardTitle>Buscar materiales</CardTitle>
          <CardDescription>
            Elige tu zona arriba para comparar precios por retailer.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p
            className="text-sm text-muted-foreground"
            role="status"
            aria-live="polite"
            data-testid="search-needs-zone"
          >
            Primero selecciona una zona para poder buscar.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-2xl" data-testid="search-panel">
      <CardHeader>
        <CardTitle>Buscar materiales</CardTitle>
        <CardDescription>
          Precios para{" "}
          <span className="font-medium text-foreground">
            {selectedZone?.name}
          </span>
          .
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form
          className="flex items-center gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            submit();
          }}
        >
          <Input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Busca un material, p.ej. varilla"
            aria-label="Buscar materiales"
            data-testid="search-input"
          />
          <Button type="submit" data-testid="search-submit">
            <Search aria-hidden className="size-4" />
            Buscar
          </Button>
        </form>

        <div className="flex items-center gap-2">
          <label
            htmlFor="search-sort"
            className="text-sm text-muted-foreground"
          >
            Ordenar por
          </label>
          <select
            id="search-sort"
            className="h-8 rounded-lg border border-input bg-transparent px-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            value={sort}
            onChange={(event) => setSort(event.target.value as SearchSort)}
            data-testid="search-sort"
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {state.status === "idle" && (
          <p
            className="text-sm text-muted-foreground"
            data-testid="search-idle"
          >
            Escribe un material y pulsa Buscar para ver precios por retailer.
          </p>
        )}

        {state.status === "loading" && (
          <p
            className="flex items-center gap-2 text-sm text-muted-foreground"
            role="status"
            aria-live="polite"
            data-testid="search-loading"
          >
            <span
              aria-hidden
              className="size-2 animate-pulse rounded-full bg-muted-foreground"
            />
            Buscando…
          </p>
        )}

        {state.status === "error" && (
          <p
            className="flex items-center gap-2 text-sm text-destructive"
            role="status"
            aria-live="polite"
            data-testid="search-error"
          >
            <span aria-hidden className="size-2 rounded-full bg-destructive" />
            No se pudo completar la búsqueda. Revisa tu conexión e inténtalo de
            nuevo.
          </p>
        )}

        {state.status === "empty" && (
          <p
            className="text-sm text-muted-foreground"
            role="status"
            aria-live="polite"
            data-testid="search-empty"
          >
            Sin resultados para tu búsqueda.
          </p>
        )}

        {state.status === "ready" && (
          <div className="flex flex-col gap-3" data-testid="search-results">
            {state.results.map((result) => (
              <ResultCard
                key={result.canonical_product.id}
                result={result}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
