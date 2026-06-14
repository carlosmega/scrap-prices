/**
 * Lista de `specs` del canónico (calibre/diámetro/longitud…). Presentación pura
 * sobre datos ya cargados: sin `"use client"`. Aplana el objeto `specs` libre del
 * contrato a pares clave/valor (ver `specEntries`). Si no hay specs, lo indica
 * explícitamente para no mostrar una sección vacía.
 */
import { specEntries } from "../format";
import type { ProductCanonical } from "../types";

export function ProductSpecs({ specs }: { specs: ProductCanonical["specs"] }) {
  const entries = specEntries(specs);

  if (entries.length === 0) {
    return (
      <p className="text-sm text-muted-foreground" data-testid="product-no-specs">
        Sin especificaciones registradas.
      </p>
    );
  }

  return (
    <dl
      className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm"
      data-testid="product-specs"
    >
      {entries.map((entry) => (
        <div key={entry.key} className="contents">
          <dt className="text-muted-foreground">{entry.key}</dt>
          <dd className="font-medium text-foreground">{entry.value}</dd>
        </div>
      ))}
    </dl>
  );
}
