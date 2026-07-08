/**
 * Helpers PUROS del badge de corrida en vivo (F033).
 *
 * La búsqueda puede haber consultado las tiendas EN VIVO (`SearchOut.live`);
 * estos helpers traducen el estado por retailer a etiquetas cortas en español
 * para el badge. Sin DOM, sin red: formateo puro sobre tipos del contrato.
 */
import type { LiveRetailerStatus } from "./types";

/**
 * Etiqueta corta del estado de un retailer en la corrida en vivo:
 * "ok · N" (N = productos hallados) / "bloqueado" / "omitido" / "falló".
 * El `detail` (motivo breve) lo añade la UI aparte cuando viene.
 */
export function liveStatusLabel(
  entry: Pick<LiveRetailerStatus, "status" | "items_found">,
): string {
  switch (entry.status) {
    case "ok":
      return `ok · ${entry.items_found}`;
    case "blocked":
      return "bloqueado";
    case "skipped":
      return "omitido";
    case "failed":
      return "falló";
  }
}

/**
 * Nombre display de un retailer a partir de su slug ("home-depot" → "Home
 * Depot"). `LiveRetailerStatusOut` solo trae el slug; esto es presentación
 * (capitalizar palabras), no un dato nuevo de la API.
 */
export function retailerNameFromSlug(slug: string): string {
  return slug
    .split("-")
    .filter((word) => word.length > 0)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
