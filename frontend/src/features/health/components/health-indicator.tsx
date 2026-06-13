"use client";

/**
 * Indicador de salud del backend (Client Component).
 *
 * Renderiza los tres estados del fetch: cargando, error amable y datos ("ok").
 * Vive lo más abajo posible del árbol para que la home siga siendo Server
 * Component; el fetch ocurre en el navegador, nunca en build/prerender.
 */
import { useHealth } from "../hooks/use-health";

export function HealthIndicator() {
  const health = useHealth();

  if (health.status === "loading") {
    return (
      <p
        className="flex items-center gap-2 text-sm text-muted-foreground"
        role="status"
        aria-live="polite"
      >
        <span
          aria-hidden
          className="size-2 animate-pulse rounded-full bg-muted-foreground"
        />
        Verificando el estado del backend…
      </p>
    );
  }

  if (health.status === "error") {
    return (
      <p
        className="flex items-center gap-2 text-sm text-destructive"
        role="status"
        aria-live="polite"
      >
        <span aria-hidden className="size-2 rounded-full bg-destructive" />
        No se pudo conectar con el backend. Revisa que esté en ejecución e
        inténtalo de nuevo.
      </p>
    );
  }

  return (
    <p
      className="flex items-center gap-2 text-sm text-foreground"
      role="status"
      aria-live="polite"
    >
      <span aria-hidden className="size-2 rounded-full bg-emerald-500" />
      Backend:{" "}
      <span className="font-medium">{health.value}</span>
    </p>
  );
}
