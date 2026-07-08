"use client";

/**
 * Indicador de progreso de la búsqueda (F033).
 *
 * La búsqueda puede tardar: si no hay datos frescos para término+zona, el
 * backend consulta Home Depot y Construrama EN VIVO (~2–25 s). El mensaje es
 * progresivo: arranca con "Buscando…" y, si la respuesta no llegó tras
 * ~1.5 s, cambia a avisar que se está consultando en vivo para que la espera
 * no parezca un cuelgue. El timer vive en el componente: al desmontar (llegó
 * la respuesta) se limpia solo.
 *
 * `"use client"`: tiene estado propio (el timer del mensaje).
 */
import { useEffect, useState } from "react";

/** Ms de espera antes de cambiar al mensaje de "consultando en vivo". */
export const LIVE_HINT_DELAY_MS = 1500;

export function SearchProgress() {
  const [showLiveHint, setShowLiveHint] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowLiveHint(true), LIVE_HINT_DELAY_MS);
    return () => clearTimeout(timer);
  }, []);

  return (
    <p
      className="flex items-center gap-2 text-sm text-muted-foreground"
      role="status"
      aria-live="polite"
      data-testid="search-loading"
      data-live-hint={showLiveHint ? "true" : "false"}
    >
      <span
        aria-hidden
        className="size-2 animate-pulse rounded-full bg-muted-foreground"
      />
      {showLiveHint
        ? "Consultando Home Depot y Construrama en vivo, puede tardar unos segundos…"
        : "Buscando…"}
    </p>
  );
}
