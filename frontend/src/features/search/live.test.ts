import { describe, expect, it } from "vitest";

import { liveStatusLabel, retailerNameFromSlug } from "./live";

/**
 * Tests de los helpers PUROS del badge de corrida en vivo (F033), la lógica
 * que consume `live-run-badge.tsx`.
 */

describe("liveStatusLabel", () => {
  it("ok incluye el número de productos hallados", () => {
    expect(liveStatusLabel({ status: "ok", items_found: 12 })).toBe("ok · 12");
  });

  it("ok con 0 hallazgos sigue siendo ok (consultado con éxito, sin datos)", () => {
    expect(liveStatusLabel({ status: "ok", items_found: 0 })).toBe("ok · 0");
  });

  it("traduce los estados de fallo/omisión al español del PRD", () => {
    expect(liveStatusLabel({ status: "blocked", items_found: 0 })).toBe(
      "bloqueado"
    );
    expect(liveStatusLabel({ status: "skipped", items_found: 0 })).toBe(
      "omitido"
    );
    expect(liveStatusLabel({ status: "failed", items_found: 0 })).toBe("falló");
  });
});

describe("retailerNameFromSlug", () => {
  it("capitaliza cada palabra del slug", () => {
    expect(retailerNameFromSlug("home-depot")).toBe("Home Depot");
    expect(retailerNameFromSlug("construrama")).toBe("Construrama");
  });

  it("ignora separadores duplicados sin producir palabras vacías", () => {
    expect(retailerNameFromSlug("home--depot")).toBe("Home Depot");
  });
});
