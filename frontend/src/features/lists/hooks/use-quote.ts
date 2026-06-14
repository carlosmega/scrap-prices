"use client";

/**
 * Hook compartido de la cotización (F022).
 *
 * Une las tres vistas de la cotización (botón "Agregar", badge del shell y página
 * de lista) sobre un único estado en memoria, para que agregar/editar/quitar un
 * ítem se refleje al instante en todas. Sigue el patrón de `use-selected-zone`:
 * un store a nivel de módulo con suscriptores in-tab (el evento `storage` solo
 * cruza pestañas; dentro de la misma página varias instancias del hook no se
 * enterarían sin este canal).
 *
 * - Identidad: `getSessionKey()` (header `X-Session-Key`); recargar conserva la
 *   cotización porque la clave es persistente y el estado se recarga del backend.
 * - Lista por defecto perezosa: no se crea hasta el primer "Agregar". Se cachea su
 *   id en `localStorage` para reusarla entre montajes/recargas; si el backend ya
 *   no la conoce (404), se recrea.
 * - El `fetch` real vive en `lib/api/client.ts` vía las funciones de `../api`.
 * - Los totales (`subtotal`/`total`/`line_total`) vienen del backend; la UI NUNCA
 *   recalcula precios.
 */
import { useCallback, useEffect, useState } from "react";

import {
  addItem as apiAddItem,
  createList,
  fetchListDetail,
  removeItem as apiRemoveItem,
  updateItemQuantity,
} from "../api";
import { getSessionKey } from "../session";
import type { ListDetail } from "../types";

/** Clave de `localStorage` donde se cachea el id de la lista por defecto. */
export const DEFAULT_LIST_ID_STORAGE_KEY = "construscan.defaultListId";

/** Nombre de la lista por defecto que se crea en el primer "Agregar". */
const DEFAULT_LIST_NAME = "Mi cotización";

/** Estado de la cotización tal como lo consumen las vistas. */
export type QuoteState =
  | { status: "idle" } // sin lista aún (nadie ha cargado/agregado)
  | { status: "loading" }
  | { status: "ready"; detail: ListDetail }
  | { status: "empty" } // hay sesión pero no hay lista/ítems
  | { status: "error"; message: string };

// --- Store a nivel de módulo: estado único + suscriptores in-tab ------------

let quoteState: QuoteState = { status: "idle" };
const listeners = new Set<(state: QuoteState) => void>();

function setQuoteState(next: QuoteState): void {
  quoteState = next;
  for (const listener of listeners) {
    listener(next);
  }
}

/** Lee el id de la lista por defecto cacheado (o `null`). */
function readCachedListId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(DEFAULT_LIST_ID_STORAGE_KEY);
}

/** Cachea (o limpia) el id de la lista por defecto. */
function writeCachedListId(listId: string | null): void {
  if (typeof window === "undefined") {
    return;
  }
  if (listId === null) {
    window.localStorage.removeItem(DEFAULT_LIST_ID_STORAGE_KEY);
  } else {
    window.localStorage.setItem(DEFAULT_LIST_ID_STORAGE_KEY, listId);
  }
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

/**
 * Devuelve el id de la lista por defecto de la sesión, creándola si hace falta.
 * Reusa la cacheada; si el backend ya no la conoce, la recrea. Se le pasa la zona
 * actual para que el snapshot de los ítems se tome de la observación en esa zona.
 */
async function ensureDefaultList(
  sessionKey: string,
  zoneId: string | null
): Promise<string> {
  const cached = readCachedListId();
  if (cached !== null) {
    try {
      await fetchListDetail(cached, sessionKey);
      return cached;
    } catch {
      // La lista cacheada ya no existe para esta sesión: la recreamos abajo.
      writeCachedListId(null);
    }
  }
  const created = await createList(sessionKey, DEFAULT_LIST_NAME, zoneId);
  writeCachedListId(created.id);
  return created.id;
}

/** Recarga el detalle de la lista por defecto al store (si existe). */
async function refreshQuote(sessionKey: string): Promise<void> {
  const listId = readCachedListId();
  if (listId === null) {
    setQuoteState({ status: "empty" });
    return;
  }
  setQuoteState({ status: "loading" });
  try {
    const detail = await fetchListDetail(listId, sessionKey);
    setQuoteState(
      detail.items.length === 0
        ? { status: "empty" }
        : { status: "ready", detail }
    );
  } catch {
    // La lista cacheada ya no existe: limpiamos y mostramos vacío.
    writeCachedListId(null);
    setQuoteState({ status: "empty" });
  }
}

export interface UseQuote {
  /** Estado actual de la cotización (idle/loading/ready/empty/error). */
  state: QuoteState;
  /** Cantidad total de ítems (filas) para el badge; 0 si no hay datos. */
  itemCount: number;
  /** Carga (o recarga) la cotización desde el backend. */
  load: () => void;
  /**
   * Agrega un SKU a la cotización; crea la lista por defecto en el primer uso.
   * `zoneId` fija la zona de la lista nueva (para el snapshot). Lanza si falla.
   */
  add: (
    retailerProductId: string,
    quantity: number,
    zoneId: string | null
  ) => Promise<void>;
  /** Cambia la cantidad de un ítem y recarga totales. */
  setQuantity: (itemId: string, quantity: number) => Promise<void>;
  /** Quita un ítem de la cotización. */
  remove: (itemId: string) => Promise<void>;
}

export function useQuote(): UseQuote {
  const [state, setState] = useState<QuoteState>(quoteState);

  useEffect(() => {
    listeners.add(setState);
    // Sincroniza por si el store cambió entre el render y el efecto.
    setState(quoteState);
    return () => {
      listeners.delete(setState);
    };
  }, []);

  const load = useCallback(() => {
    const sessionKey = getSessionKey();
    void refreshQuote(sessionKey);
  }, []);

  const add = useCallback(
    async (
      retailerProductId: string,
      quantity: number,
      zoneId: string | null
    ) => {
      const sessionKey = getSessionKey();
      try {
        const listId = await ensureDefaultList(sessionKey, zoneId);
        await apiAddItem(listId, sessionKey, retailerProductId, quantity);
        await refreshQuote(sessionKey);
      } catch (error) {
        setQuoteState({
          status: "error",
          message: errorMessage(
            error,
            "No se pudo agregar el producto a tu cotización."
          ),
        });
        throw error;
      }
    },
    []
  );

  const setQuantity = useCallback(async (itemId: string, quantity: number) => {
    const sessionKey = getSessionKey();
    const listId = readCachedListId();
    if (listId === null) {
      return;
    }
    await updateItemQuantity(listId, itemId, sessionKey, quantity);
    await refreshQuote(sessionKey);
  }, []);

  const remove = useCallback(async (itemId: string) => {
    const sessionKey = getSessionKey();
    const listId = readCachedListId();
    if (listId === null) {
      return;
    }
    await apiRemoveItem(listId, itemId, sessionKey);
    await refreshQuote(sessionKey);
  }, []);

  const itemCount =
    state.status === "ready" ? state.detail.items.length : 0;

  return { state, itemCount, load, add, setQuantity, remove };
}
