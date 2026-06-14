"use client";

/**
 * Hook de la zona seleccionada, persistente en `localStorage` (A1·CA3).
 *
 * Guarda solo `{ id, name }` (ver `SelectedZone`) bajo una clave estable. La
 * lectura inicial es perezosa (lazy initializer) para no parpadear y para
 * sobrevivir a recargas completas. Es resiliente a SSR (sin `window`) y a JSON
 * corrupto en el almacenamiento.
 */
import { useCallback, useEffect, useState } from "react";

import type { SelectedZone } from "../types";

/** Clave de `localStorage` donde vive la zona seleccionada. */
export const SELECTED_ZONE_STORAGE_KEY = "construscan.selectedZone";

/**
 * Suscriptores in-tab (mismo documento). El evento `storage` del navegador SOLO
 * se dispara en OTRAS pestañas, no en la que hace el cambio; por eso varias
 * instancias de este hook en la misma página (p.ej. `ZoneSelector` y
 * `SearchPanel`) no se enterarían entre sí sin este canal. Cada instancia se
 * suscribe y `selectZone`/`clearZone` notifican a todas.
 */
const inTabListeners = new Set<(zone: SelectedZone | null) => void>();

/** Notifica a todas las instancias del hook en esta misma pestaña. */
function broadcastInTab(zone: SelectedZone | null): void {
  for (const listener of inTabListeners) {
    listener(zone);
  }
}

/** Lee y valida la zona persistida; `null` si no hay o está corrupta. */
function readStoredZone(): SelectedZone | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = window.localStorage.getItem(SELECTED_ZONE_STORAGE_KEY);
  if (raw === null) {
    return null;
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (
      typeof parsed === "object" &&
      parsed !== null &&
      "id" in parsed &&
      "name" in parsed &&
      typeof (parsed as { id: unknown }).id === "string" &&
      typeof (parsed as { name: unknown }).name === "string"
    ) {
      const { id, name } = parsed as { id: string; name: string };
      return { id, name };
    }
  } catch {
    // JSON inválido: lo tratamos como "sin selección".
  }
  return null;
}

export interface UseSelectedZone {
  /** Zona elegida, o `null` si el usuario aún no eligió. */
  selectedZone: SelectedZone | null;
  /** Persiste la zona elegida y actualiza el estado. */
  selectZone: (zone: SelectedZone) => void;
  /** Borra la selección persistida. */
  clearZone: () => void;
}

export function useSelectedZone(): UseSelectedZone {
  // Lazy initializer: en el primer render del cliente ya leemos localStorage,
  // así la selección sobrevive a una recarga sin un flash de "sin zona".
  const [selectedZone, setSelectedZone] = useState<SelectedZone | null>(
    readStoredZone
  );

  // Sync entre pestañas (evento `storage`) Y dentro de la misma pestaña
  // (suscriptores in-tab): así otras instancias del hook en esta página
  // reaccionan al instante a un `selectZone`/`clearZone`.
  useEffect(() => {
    function onStorage(event: StorageEvent) {
      if (event.key === SELECTED_ZONE_STORAGE_KEY) {
        setSelectedZone(readStoredZone());
      }
    }
    window.addEventListener("storage", onStorage);
    inTabListeners.add(setSelectedZone);
    return () => {
      window.removeEventListener("storage", onStorage);
      inTabListeners.delete(setSelectedZone);
    };
  }, []);

  const selectZone = useCallback((zone: SelectedZone) => {
    const value: SelectedZone = { id: zone.id, name: zone.name };
    setSelectedZone(value);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(
        SELECTED_ZONE_STORAGE_KEY,
        JSON.stringify(value)
      );
    }
    broadcastInTab(value);
  }, []);

  const clearZone = useCallback(() => {
    setSelectedZone(null);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(SELECTED_ZONE_STORAGE_KEY);
    }
    broadcastInTab(null);
  }, []);

  return { selectedZone, selectZone, clearZone };
}
