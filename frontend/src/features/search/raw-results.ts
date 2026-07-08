/**
 * Helper PURO de agrupado de los hallazgos crudos por tienda (F033).
 *
 * El backend ya ordena `raw_results` por retailer y luego precio ascendente;
 * aquí solo se agrupan para el render "sección por retailer", preservando el
 * orden de llegada (primer retailer visto primero; dentro del grupo, el orden
 * del backend). Es robusto ante entradas intercaladas: agrupa por slug, no
 * por contigüidad. No muta la entrada.
 */
import type { RawResult } from "./types";

/** Un grupo de hallazgos crudos de UNA tienda, listo para render. */
export interface RawRetailerGroup<T> {
  /** Slug del retailer (`retailer_slug`), estable para keys/testids. */
  slug: string;
  /** Nombre display del retailer (`retailer_name`). */
  name: string;
  /** Hallazgos del retailer en el orden en que llegaron del backend. */
  items: T[];
}

/**
 * Agrupa los hallazgos crudos por retailer. Genérico sobre el subconjunto de
 * campos que usa (patrón de `sortPricesAsc`): los tests pueden pasar filas
 * mínimas sin fabricar el `RawResult` completo.
 */
export function groupRawResultsByRetailer<
  T extends Pick<RawResult, "retailer_slug" | "retailer_name">,
>(rawResults: readonly T[]): Array<RawRetailerGroup<T>> {
  const bySlug = new Map<string, RawRetailerGroup<T>>();
  for (const item of rawResults) {
    const group = bySlug.get(item.retailer_slug);
    if (group === undefined) {
      bySlug.set(item.retailer_slug, {
        slug: item.retailer_slug,
        name: item.retailer_name,
        items: [item],
      });
    } else {
      group.items.push(item);
    }
  }
  return [...bySlug.values()];
}
