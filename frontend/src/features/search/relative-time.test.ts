import { describe, expect, it } from "vitest";

import { freshnessLabel, relativeTime } from "./relative-time";

// "Ahora" fijo para que el test sea determinista (función pura).
const NOW = new Date("2026-06-14T12:00:00.000Z");

describe("relativeTime", () => {
  it("devuelve null ante fecha nula o indefinida", () => {
    expect(relativeTime(null, NOW)).toBeNull();
    expect(relativeTime(undefined, NOW)).toBeNull();
  });

  it("devuelve null ante una fecha inválida", () => {
    expect(relativeTime("no-es-fecha", NOW)).toBeNull();
  });

  it("trata el futuro y < 60s como 'hace un momento'", () => {
    expect(relativeTime("2026-06-14T12:30:00.000Z", NOW)).toBe("hace un momento");
    expect(relativeTime("2026-06-14T11:59:30.000Z", NOW)).toBe("hace un momento");
  });

  it("formatea minutos con singular y plural", () => {
    expect(relativeTime("2026-06-14T11:59:00.000Z", NOW)).toBe("hace 1 minuto");
    expect(relativeTime("2026-06-14T11:45:00.000Z", NOW)).toBe("hace 15 minutos");
  });

  it("formatea horas con singular y plural", () => {
    expect(relativeTime("2026-06-14T11:00:00.000Z", NOW)).toBe("hace 1 hora");
    expect(relativeTime("2026-06-14T07:00:00.000Z", NOW)).toBe("hace 5 horas");
  });

  it("formatea días con singular y plural", () => {
    expect(relativeTime("2026-06-13T12:00:00.000Z", NOW)).toBe("hace 1 día");
    expect(relativeTime("2026-06-08T09:00:00.000Z", NOW)).toBe("hace 6 días");
  });

  it("acepta un Date además de un string ISO", () => {
    const d = new Date("2026-06-14T09:00:00.000Z");
    expect(relativeTime(d, NOW)).toBe("hace 3 horas");
  });
});

describe("freshnessLabel", () => {
  it("prefija 'actualizado' cuando hay fecha", () => {
    expect(freshnessLabel("2026-06-14T07:00:00.000Z", NOW)).toBe(
      "actualizado hace 5 horas"
    );
  });

  it("explicita la ausencia de fecha sin inventarla", () => {
    expect(freshnessLabel(null, NOW)).toBe("actualización sin fecha");
  });
});
