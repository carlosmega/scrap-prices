"use client";

/**
 * Hook de la zona seleccionada, persistente en `localStorage` (A1·CA3).
 *
 * Guarda solo `{ id, name }` (ver `SelectedZone`) bajo una clave estable.
 *
 * **SSR-safe (F030):** el `getServerSnapshot` devuelve SIEMPRE el default
 * (`null`), igual que el primer snapshot del cliente. `localStorage` NO se lee
 * en el render inicial: `useSyncExternalStore` lo lee una vez montado, y la
 * suscripción mantiene el valor sincronizado. Así el HTML del servidor y el
 * primer render del cliente coinciden (sin hydration mismatch) y, tras hidratar,
 * se refleja la zona guardada. Es resiliente a SSR (sin `window`) y a JSON
 * corrupto en el almacenamiento.
 */
import { useCallback, useSyncExternalStore } from "react";

import type { SelectedZone } from "../types";

/** Clave de `localStorage` donde vive la zona seleccionada. */
export const SELECTED_ZONE_STORAGE_KEY = "construscan.selectedZone";

/**
 * Suscriptores in-tab (mismo documento). El evento `storage` del navegador SOLO
 * se dispara en OTRAS pestañas, no en la que hace el cambio; por eso varias
 * instancias de este hook en la misma página (p.ej. `ZoneSelector` y
 * `SearchPanel`) no se enterarían entre sí sin este canal. Cada instancia se
 * suscribe (vía `useSyncExternalStore`) y `selectZone`/`clearZone` notifican a
 * todas.
 */
const inTabListeners = new Set<() => void>();

/** Notifica a todas las instancias del hook en esta misma pestaña. */
function broadcastInTab(): void {
  for (const listener of inTabListeners) {
    listener();
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

/**
 * Snapshot cacheado del cliente. `useSyncExternalStore` exige que
 * `getSnapshot()` devuelva un valor referencialmente estable mientras no haya
 * cambiado, o entra en bucle de renders. Recalculamos (y cacheamos) solo cuando
 * una notificación (`storage`/in-tab) indica que pudo cambiar.
 */
let zoneSnapshot: SelectedZone | null = null;
let zoneSnapshotInitialized = false;

/** Refresca el snapshot cacheado desde `localStorage` (tras un cambio). */
function refreshZoneSnapshot(): void {
  zoneSnapshot = readStoredZone();
  zoneSnapshotInitialized = true;
}

/** Snapshot del cliente: lee `localStorage` una sola vez y reusa la referencia. */
function getClientSnapshot(): SelectedZone | null {
  if (!zoneSnapshotInitialized) {
    refreshZoneSnapshot();
  }
  return zoneSnapshot;
}

/**
 * Snapshot del servidor (y del primer render del cliente, en hidratación):
 * SIEMPRE el default sin `localStorage`. Esto es lo que elimina el mismatch.
 */
function getServerSnapshot(): SelectedZone | null {
  return null;
}

/**
 * Suscripción a cambios de la zona: evento `storage` (otras pestañas) y canal
 * in-tab (esta pestaña). Cualquier notificación refresca el snapshot y avisa a
 * `useSyncExternalStore` para re-renderizar.
 */
function subscribe(onStoreChange: () => void): () => void {
  // Al reactivarse el store (primer suscriptor), re-leemos `localStorage` por si
  // cambió mientras no había instancias montadas (p.ej. otra pestaña).
  refreshZoneSnapshot();
  function onStorage(event: StorageEvent) {
    if (event.key === SELECTED_ZONE_STORAGE_KEY) {
      refreshZoneSnapshot();
      onStoreChange();
    }
  }
  window.addEventListener("storage", onStorage);
  inTabListeners.add(onStoreChange);
  return () => {
    window.removeEventListener("storage", onStorage);
    inTabListeners.delete(onStoreChange);
  };
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
  // SSR-safe: server snapshot == default (null); el cliente lee localStorage
  // solo tras montar/suscribirse, así el primer paint del cliente == SSR.
  const selectedZone = useSyncExternalStore(
    subscribe,
    getClientSnapshot,
    getServerSnapshot
  );

  const selectZone = useCallback((zone: SelectedZone) => {
    const value: SelectedZone = { id: zone.id, name: zone.name };
    if (typeof window !== "undefined") {
      window.localStorage.setItem(
        SELECTED_ZONE_STORAGE_KEY,
        JSON.stringify(value)
      );
    }
    refreshZoneSnapshot();
    broadcastInTab();
  }, []);

  const clearZone = useCallback(() => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(SELECTED_ZONE_STORAGE_KEY);
    }
    refreshZoneSnapshot();
    broadcastInTab();
  }, []);

  return { selectedZone, selectZone, clearZone };
}
