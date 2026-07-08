/**
 * Badge de corrida en vivo (F033): visible cuando la búsqueda disparó la
 * consulta EN VIVO a las tiendas (`live.triggered`). Muestra, por retailer,
 * cómo le fue — "ok · N" / "bloqueado" / "omitido" / "falló" — con el motivo
 * breve (`detail`) si el backend lo mandó (jamás llega un stacktrace).
 *
 * Presentación pura sobre datos ya cargados: vive sin `"use client"` (el
 * estado está en `SearchPanel`, patrón de `ResultCard`).
 */
import { Badge } from "@/components/ui/badge";

import { liveStatusLabel, retailerNameFromSlug } from "../live";
import type { LiveInfo, LiveRetailerStatus } from "../types";

/** Variante visual según el estado: ok informativo, fallos en destructivo. */
function badgeVariant(status: LiveRetailerStatus["status"]) {
  switch (status) {
    case "ok":
      return "secondary" as const;
    case "skipped":
      return "outline" as const;
    case "blocked":
    case "failed":
      return "destructive" as const;
  }
}

export function LiveRunBadge({ live }: { live: LiveInfo }) {
  if (!live.triggered) {
    return null;
  }

  return (
    <div
      className="flex flex-wrap items-center gap-2"
      role="status"
      aria-live="polite"
      data-testid="live-run-badge"
    >
      <span className="text-xs font-medium text-muted-foreground">
        Consulta en vivo a las tiendas:
      </span>
      {live.retailers.map((entry) => (
        <Badge
          key={entry.retailer_slug}
          variant={badgeVariant(entry.status)}
          data-testid="live-retailer-status"
          data-retailer={entry.retailer_slug}
          data-status={entry.status}
        >
          {retailerNameFromSlug(entry.retailer_slug)}: {liveStatusLabel(entry)}
          {entry.detail ? ` — ${entry.detail}` : null}
        </Badge>
      ))}
    </div>
  );
}
