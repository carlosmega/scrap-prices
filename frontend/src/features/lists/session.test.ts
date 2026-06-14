import { afterEach, describe, expect, it } from "vitest";

import {
  getSessionKey,
  isUuidV4,
  SESSION_KEY_STORAGE_KEY,
} from "./session";

afterEach(() => {
  window.localStorage.clear();
});

describe("getSessionKey", () => {
  it("genera un UUID v4 y lo persiste en localStorage", () => {
    expect(window.localStorage.getItem(SESSION_KEY_STORAGE_KEY)).toBeNull();

    const key = getSessionKey();

    expect(isUuidV4(key)).toBe(true);
    expect(window.localStorage.getItem(SESSION_KEY_STORAGE_KEY)).toBe(key);
  });

  it("es idempotente: devuelve la misma clave entre llamadas (sobrevive recarga)", () => {
    const first = getSessionKey();
    const second = getSessionKey();

    expect(second).toBe(first);
  });

  it("reutiliza una clave válida ya presente en localStorage", () => {
    const existing = "11111111-2222-4333-8444-555555555555";
    window.localStorage.setItem(SESSION_KEY_STORAGE_KEY, existing);

    expect(getSessionKey()).toBe(existing);
  });

  it("regenera la clave si lo persistido no es un UUID v4 válido", () => {
    window.localStorage.setItem(SESSION_KEY_STORAGE_KEY, "no-es-uuid");

    const key = getSessionKey();

    expect(key).not.toBe("no-es-uuid");
    expect(isUuidV4(key)).toBe(true);
    expect(window.localStorage.getItem(SESSION_KEY_STORAGE_KEY)).toBe(key);
  });
});

describe("isUuidV4", () => {
  it("acepta un UUID v4 canónico", () => {
    expect(isUuidV4("11111111-2222-4333-8444-555555555555")).toBe(true);
  });

  it("rechaza cadenas que no son UUID v4", () => {
    expect(isUuidV4("")).toBe(false);
    expect(isUuidV4("no-es-uuid")).toBe(false);
    // Versión 1 (tercer grupo empieza con 1, no 4).
    expect(isUuidV4("11111111-2222-1333-8444-555555555555")).toBe(false);
  });
});
