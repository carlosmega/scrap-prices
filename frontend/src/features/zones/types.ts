/**
 * Tipos derivados del contrato para el dominio "zones".
 *
 * NO se declara a mano ninguna forma de la API: el tipo de una zona se infiere
 * del retorno de `fetchZones()` (que a su vez deriva de `schema.d.ts`). Si el
 * contrato cambia, este tipo cambia con él sin tocar nada.
 */
import type { fetchZones } from "./api";

/** Una zona tal como la entrega la API (elemento de `ZoneOut[]`). */
export type Zone = Awaited<ReturnType<typeof fetchZones>>[number];

/**
 * Subconjunto persistido de la zona seleccionada. La spec (A1·CA3) solo exige
 * guardar `{ id, name }`; el resto se vuelve a cargar de la API cuando hace
 * falta.
 */
export type SelectedZone = Pick<Zone, "id" | "name">;
