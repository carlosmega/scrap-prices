import { describe, expect, it } from "vitest";

import { groupRawResultsByRetailer } from "./raw-results";

/**
 * Tests del agrupador PURO de hallazgos crudos por retailer (F033), la lógica
 * que consume `raw-results-section.tsx`.
 */

/** Fila mínima con los campos que usa el agrupador (patrón de format.test). */
function raw(slug: string, name: string, sku: string) {
  return { retailer_slug: slug, retailer_name: name, external_sku: sku };
}

describe("groupRawResultsByRetailer", () => {
  it("agrupa por retailer preservando el orden de llegada del backend", () => {
    const grouped = groupRawResultsByRetailer([
      raw("construrama", "Construrama", "0204000086"),
      raw("construrama", "Construrama", "0204000099"),
      raw("home-depot", "Home Depot", "123456"),
    ]);

    expect(grouped.map((g) => g.slug)).toEqual(["construrama", "home-depot"]);
    expect(grouped[0].name).toBe("Construrama");
    expect(grouped[0].items.map((i) => i.external_sku)).toEqual([
      "0204000086",
      "0204000099",
    ]);
    expect(grouped[1].items).toHaveLength(1);
  });

  it("conserva el orden interno de los ítems (backend: precio ascendente)", () => {
    const grouped = groupRawResultsByRetailer([
      raw("home-depot", "Home Depot", "barato"),
      raw("home-depot", "Home Depot", "caro"),
    ]);
    expect(grouped[0].items.map((i) => i.external_sku)).toEqual([
      "barato",
      "caro",
    ]);
  });

  it("agrupa entradas intercaladas del mismo retailer (por slug, no contigüidad)", () => {
    const grouped = groupRawResultsByRetailer([
      raw("home-depot", "Home Depot", "hd-1"),
      raw("construrama", "Construrama", "cr-1"),
      raw("home-depot", "Home Depot", "hd-2"),
    ]);

    expect(grouped.map((g) => g.slug)).toEqual(["home-depot", "construrama"]);
    expect(grouped[0].items.map((i) => i.external_sku)).toEqual([
      "hd-1",
      "hd-2",
    ]);
  });

  it("devuelve [] con entrada vacía (la sección no se renderiza)", () => {
    expect(groupRawResultsByRetailer([])).toEqual([]);
  });

  it("no muta el arreglo de entrada", () => {
    const input = [
      raw("construrama", "Construrama", "a"),
      raw("home-depot", "Home Depot", "b"),
    ];
    const copy = [...input];
    groupRawResultsByRetailer(input);
    expect(input).toEqual(copy);
  });
});
