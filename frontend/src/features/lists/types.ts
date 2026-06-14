/**
 * Tipos derivados del contrato para el dominio "lists" (cotización).
 *
 * NO se declara a mano ninguna forma de la API: el detalle de la lista, sus ítems
 * y el resumen se infieren del retorno de las funciones de `api.ts` (que a su vez
 * derivan de `schema.d.ts`). Si el contrato cambia, estos tipos cambian con él.
 */
import type {
  createList,
  fetchListDetail,
  fetchLists,
} from "./api";

/** Detalle de una lista con ítems y totales (`UserListDetailOut`). */
export type ListDetail = Awaited<ReturnType<typeof fetchListDetail>>;

/** Un ítem de la cotización (`UserListItemOut`). */
export type ListItem = ListDetail["items"][number];

/** Resumen de una lista (`UserListOut`). */
export type ListSummary = Awaited<ReturnType<typeof fetchLists>>[number];

/** Lista recién creada (`UserListOut`). */
export type CreatedList = Awaited<ReturnType<typeof createList>>;
