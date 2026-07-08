import { describe, expect, it } from "vitest";

import {
  bestPriceIndex,
  formatNativePrice,
  formatPrice,
  formatPricePerKg,
  formatPricePerPiece,
  formatRawPrice,
  saleUnitLabel,
  sortPricesAsc,
} from "./format";

/**
 * Tests de los helpers PUROS de formato/orden de F031 (normalización de unidad).
 * Replican la lógica que consumen `result-card.tsx` y `product-prices.tsx`.
 */

/** Construye una fila mínima con los campos que usan los helpers. */
function row(overrides: {
  name: string;
  price?: string | null;
  price_per_piece?: string | null;
  price_per_kg?: string | null;
  sale_unit?: string;
}) {
  return {
    retailer: { name: overrides.name },
    currency: "MXN",
    price: overrides.price ?? null,
    price_per_piece: overrides.price_per_piece ?? null,
    price_per_kg: overrides.price_per_kg ?? null,
    sale_unit: overrides.sale_unit ?? "",
  };
}

describe("formatPrice", () => {
  it("formatea un Decimal string a moneda es-MX", () => {
    expect(formatPrice("20085.00", "MXN")).toBe("$20,085.00");
  });

  it("devuelve el valor crudo + moneda si no es numérico", () => {
    expect(formatPrice("n/d", "MXN")).toBe("n/d MXN");
  });
});

describe("saleUnitLabel", () => {
  it("mapea las unidades conocidas a su abreviatura", () => {
    expect(saleUnitLabel("tonelada")).toBe("ton");
    expect(saleUnitLabel("kg")).toBe("kg");
    expect(saleUnitLabel("pieza")).toBe("pieza");
  });

  it("devuelve el valor tal cual para unidades sin abreviatura", () => {
    expect(saleUnitLabel("m")).toBe("m");
    expect(saleUnitLabel("saco")).toBe("saco");
    expect(saleUnitLabel("")).toBe("");
  });
});

describe("formatPricePerPiece", () => {
  it("formatea el titular por pieza", () => {
    expect(formatPricePerPiece("236.65", "MXN")).toBe("$236.65 / pieza");
  });

  it("devuelve null cuando no hay normalizado por pieza", () => {
    expect(formatPricePerPiece(null, "MXN")).toBeNull();
    expect(formatPricePerPiece(undefined, "MXN")).toBeNull();
  });
});

describe("formatPricePerKg", () => {
  it("formatea la base de comparación por kg", () => {
    expect(formatPricePerKg("20.09", "MXN")).toBe("$20.09 / kg");
  });

  it("devuelve null cuando no hay normalizado por kg", () => {
    expect(formatPricePerKg(null, "MXN")).toBeNull();
  });
});

describe("formatNativePrice", () => {
  it("muestra el nativo por tonelada (transparencia)", () => {
    expect(formatNativePrice("20085.00", "tonelada", "MXN")).toBe(
      "listado a $20,085.00 / ton"
    );
  });

  it("muestra el nativo por kg", () => {
    expect(formatNativePrice("21.53", "kg", "MXN")).toBe(
      "listado a $21.53 / kg"
    );
  });

  it("omite la unidad cuando es desconocida", () => {
    expect(formatNativePrice("100.00", "", "MXN")).toBe("listado a $100.00");
  });

  it("devuelve null sin precio en la zona", () => {
    expect(formatNativePrice(null, "tonelada", "MXN")).toBeNull();
  });
});

describe("formatRawPrice", () => {
  it("formatea el precio nativo (number del contrato F033) con su unidad", () => {
    expect(formatRawPrice(125, "pieza", "MXN")).toBe("$125.00 / pieza");
  });

  it("abrevia la unidad con saleUnitLabel (tonelada → ton)", () => {
    expect(formatRawPrice(20085, "tonelada", "MXN")).toBe(
      "$20,085.00 / ton"
    );
  });

  it("omite la unidad cuando sale_unit es null o desconocida", () => {
    expect(formatRawPrice(99.5, null, "MXN")).toBe("$99.50");
    expect(formatRawPrice(99.5, undefined, "MXN")).toBe("$99.50");
    expect(formatRawPrice(99.5, "", "MXN")).toBe("$99.50");
  });
});

describe("sortPricesAsc", () => {
  it("ordena por price_per_kg ascendente, no por el price nativo crudo", () => {
    // HD nativo es ENORME (20085/ton) pero por kg es el más barato (20.09);
    // CR nativo es chico (21.53/kg) pero por kg es más caro. El orden debe
    // poner a HD primero pese a que su número nativo es mayor.
    const hd = row({
      name: "Home Depot",
      price: "20085.00",
      price_per_kg: "20.09",
      sale_unit: "tonelada",
    });
    const cr = row({
      name: "Construrama",
      price: "21.53",
      price_per_kg: "21.53",
      sale_unit: "kg",
    });
    const sorted = sortPricesAsc([cr, hd]);
    expect(sorted.map((p) => p.retailer.name)).toEqual([
      "Home Depot",
      "Construrama",
    ]);
  });

  it("manda al final las filas sin price_per_kg (no normalizable)", () => {
    const normalizable = row({ name: "Con kg", price_per_kg: "30.00" });
    const sinKg = row({ name: "Sin kg", price: "10.00", price_per_kg: null });
    const sorted = sortPricesAsc([sinKg, normalizable]);
    expect(sorted.map((p) => p.retailer.name)).toEqual(["Con kg", "Sin kg"]);
  });

  it("no muta el arreglo de entrada", () => {
    const input = [
      row({ name: "B", price_per_kg: "2.00" }),
      row({ name: "A", price_per_kg: "1.00" }),
    ];
    const copy = [...input];
    sortPricesAsc(input);
    expect(input).toEqual(copy);
  });
});

describe("bestPriceIndex", () => {
  it("apunta a la fila con menor price_per_kg", () => {
    const list = [
      row({ name: "A", price_per_kg: "21.53" }),
      row({ name: "B", price_per_kg: "20.09" }),
    ];
    expect(bestPriceIndex(list)).toBe(1);
  });

  it("ignora filas sin price_per_kg", () => {
    const list = [
      row({ name: "A", price_per_kg: null }),
      row({ name: "B", price_per_kg: "20.09" }),
    ];
    expect(bestPriceIndex(list)).toBe(1);
  });

  it("devuelve -1 cuando ninguna fila es normalizable", () => {
    const list = [
      row({ name: "A", price_per_kg: null }),
      row({ name: "B", price_per_kg: null }),
    ];
    expect(bestPriceIndex(list)).toBe(-1);
  });
});
