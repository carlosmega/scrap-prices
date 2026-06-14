import { afterEach, describe, expect, it } from "vitest";
import { act, renderHook } from "@testing-library/react";

import {
  SELECTED_ZONE_STORAGE_KEY,
  useSelectedZone,
} from "./use-selected-zone";

afterEach(() => {
  window.localStorage.clear();
});

describe("useSelectedZone", () => {
  it("arranca sin selección cuando localStorage está vacío", () => {
    const { result } = renderHook(() => useSelectedZone());
    expect(result.current.selectedZone).toBeNull();
  });

  it("persiste la zona elegida en localStorage", () => {
    const { result } = renderHook(() => useSelectedZone());

    act(() => {
      result.current.selectZone({ id: "z1", name: "Monterrey Metro" });
    });

    expect(result.current.selectedZone).toEqual({
      id: "z1",
      name: "Monterrey Metro",
    });
    expect(
      JSON.parse(window.localStorage.getItem(SELECTED_ZONE_STORAGE_KEY) ?? "{}")
    ).toEqual({ id: "z1", name: "Monterrey Metro" });
  });

  it("recupera la zona persistida en un montaje nuevo (sobrevive recarga)", () => {
    window.localStorage.setItem(
      SELECTED_ZONE_STORAGE_KEY,
      JSON.stringify({ id: "z9", name: "Guadalajara Metro" })
    );

    const { result } = renderHook(() => useSelectedZone());
    expect(result.current.selectedZone).toEqual({
      id: "z9",
      name: "Guadalajara Metro",
    });
  });

  it("ignora JSON corrupto y trata como sin selección", () => {
    window.localStorage.setItem(SELECTED_ZONE_STORAGE_KEY, "{not json");
    const { result } = renderHook(() => useSelectedZone());
    expect(result.current.selectedZone).toBeNull();
  });

  it("clearZone borra la selección persistida", () => {
    const { result } = renderHook(() => useSelectedZone());
    act(() => {
      result.current.selectZone({ id: "z1", name: "Monterrey Metro" });
    });
    act(() => {
      result.current.clearZone();
    });
    expect(result.current.selectedZone).toBeNull();
    expect(window.localStorage.getItem(SELECTED_ZONE_STORAGE_KEY)).toBeNull();
  });
});
