/**
 * Helpers de formato PUROS para la UI de detalle de producto.
 *
 * `specs` del canónico es un objeto libre (`{ [key: string]: unknown }` en el
 * contrato); aquí lo aplanamos a pares clave/valor legibles para mostrarlos sin
 * inventar estructura. La fecha del historial se formatea para lectura humana en
 * es-MX. No se usan estos valores para cálculo monetario (el precio sigue siendo
 * el string del Decimal, formateado por `formatPrice` del dominio search).
 */
import type { ProductCanonical } from "./types";

/** Un par clave/valor de `specs` ya listo para renderizar. */
export interface SpecEntry {
  key: string;
  value: string;
}

/** Etiquetas legibles para las claves de `specs` conocidas; el resto cae al raw. */
const SPEC_LABELS: Readonly<Record<string, string>> = {
  calibre: "Calibre",
  diametro: "Diámetro",
  longitud_m: "Longitud (m)",
};

/** Convierte un valor arbitrario de spec en texto mostrable. */
function specValueToString(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

/**
 * Aplana el objeto `specs` a una lista ordenada de pares clave/valor. La etiqueta
 * usa `SPEC_LABELS` cuando la clave es conocida; si no, muestra la clave cruda
 * (transparencia del dato). Mantiene el orden de inserción del objeto.
 */
export function specEntries(specs: ProductCanonical["specs"]): SpecEntry[] {
  return Object.entries(specs).map(([key, value]) => ({
    key: SPEC_LABELS[key] ?? key,
    value: specValueToString(value),
  }));
}

/**
 * Formatea un instante ISO-8601 (`captured_at` del contrato) a una fecha legible
 * es-MX (p.ej. "13 jun 2026, 09:00"). Si la fecha no es válida, la devuelve tal
 * cual (transparencia del dato, RNF3).
 */
export function formatHistoryDate(captured_at: string): string {
  const date = new Date(captured_at);
  if (Number.isNaN(date.getTime())) {
    return captured_at;
  }
  return new Intl.DateTimeFormat("es-MX", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
