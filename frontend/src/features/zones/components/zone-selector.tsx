"use client";

/**
 * Selector de zona (Client Component) — corazón de F019.
 *
 * Lista las zonas activas (`useZones`, tres estados) y persiste la elegida
 * (`useSelectedZone`, localStorage). Incluye el botón opcional "usar mi
 * ubicación" (geolocalización → `POST /api/zones/resolve`), que ante 404
 * muestra un mensaje amable "aún sin cobertura en tu zona" (A1·CA4).
 *
 * `"use client"` vive aquí (lo más abajo posible): la home sigue siendo Server
 * Component y solo compone este organismo.
 */
import { MapPin } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { ApiError } from "@/lib/api/client";
import { resolveZone } from "../api";
import { useSelectedZone } from "../hooks/use-selected-zone";
import { useZones } from "../hooks/use-zones";
import type { Zone } from "../types";

/** Estado del flujo de geolocalización (botón "usar mi ubicación"). */
type GeoState =
  | { status: "idle" }
  | { status: "locating" }
  | { status: "no-coverage" }
  | { status: "error"; message: string };

export function ZoneSelector() {
  const zonesState = useZones();
  const { selectedZone, selectZone } = useSelectedZone();
  const [geo, setGeo] = useState<GeoState>({ status: "idle" });

  function handleSelect(zoneId: string, zones: Zone[]) {
    const zone = zones.find((z) => z.id === zoneId);
    if (zone) {
      selectZone({ id: zone.id, name: zone.name });
    }
  }

  function handleUseLocation() {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setGeo({
        status: "error",
        message: "Tu navegador no permite obtener tu ubicación.",
      });
      return;
    }
    setGeo({ status: "locating" });
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolveZone({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        })
          .then((zone) => {
            selectZone({ id: zone.id, name: zone.name });
            setGeo({ status: "idle" });
          })
          .catch((error: unknown) => {
            if (error instanceof ApiError && error.status === 404) {
              setGeo({ status: "no-coverage" });
            } else {
              setGeo({
                status: "error",
                message:
                  error instanceof Error
                    ? error.message
                    : "No se pudo resolver tu zona.",
              });
            }
          });
      },
      () => {
        setGeo({
          status: "error",
          message: "No pudimos obtener tu ubicación. Elige tu zona de la lista.",
        });
      }
    );
  }

  return (
    <Card className="w-full max-w-md" data-testid="zone-selector">
      <CardHeader>
        <CardTitle>Tu zona</CardTitle>
        <CardDescription>
          Los precios se muestran para la zona que elijas.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {zonesState.status === "loading" && (
          <p
            className="flex items-center gap-2 text-sm text-muted-foreground"
            role="status"
            aria-live="polite"
          >
            <span
              aria-hidden
              className="size-2 animate-pulse rounded-full bg-muted-foreground"
            />
            Cargando zonas…
          </p>
        )}

        {zonesState.status === "error" && (
          <p
            className="flex items-center gap-2 text-sm text-destructive"
            role="status"
            aria-live="polite"
          >
            <span aria-hidden className="size-2 rounded-full bg-destructive" />
            No se pudieron cargar las zonas. Revisa que el backend esté en
            ejecución e inténtalo de nuevo.
          </p>
        )}

        {zonesState.status === "ready" && (
          <>
            <Select
              value={selectedZone?.id ?? undefined}
              onValueChange={(value) => handleSelect(value, zonesState.zones)}
            >
              <SelectTrigger
                className="w-full"
                aria-label="Selecciona tu zona"
                data-testid="zone-select-trigger"
              >
                <SelectValue placeholder="Selecciona tu zona" />
              </SelectTrigger>
              <SelectContent>
                {zonesState.zones.map((zone) => (
                  <SelectItem key={zone.id} value={zone.id}>
                    {zone.name} · {zone.state}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={handleUseLocation}
              disabled={geo.status === "locating"}
            >
              <MapPin aria-hidden className="size-4" />
              {geo.status === "locating"
                ? "Obteniendo tu ubicación…"
                : "Usar mi ubicación"}
            </Button>

            {geo.status === "no-coverage" && (
              <p
                className="text-sm text-muted-foreground"
                role="status"
                aria-live="polite"
              >
                Aún sin cobertura en tu zona. Elige una de la lista.
              </p>
            )}
            {geo.status === "error" && (
              <p
                className="text-sm text-destructive"
                role="status"
                aria-live="polite"
              >
                {geo.message}
              </p>
            )}

            {selectedZone && (
              <p className="text-sm text-foreground" data-testid="selected-zone">
                Zona seleccionada:{" "}
                <span className="font-medium">{selectedZone.name}</span>
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
