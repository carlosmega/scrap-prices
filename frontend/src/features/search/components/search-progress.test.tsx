import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LIVE_HINT_DELAY_MS, SearchProgress } from "./search-progress";

/**
 * Tests del mensaje progresivo de carga (F033): "Buscando…" de inmediato y,
 * pasado el umbral (~1.5 s), el aviso de consulta en vivo. Timers falsos para
 * no depender del reloj real.
 */
describe("SearchProgress", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("muestra 'Buscando…' de inmediato", () => {
    render(<SearchProgress />);
    const status = screen.getByTestId("search-loading");
    expect(status).toHaveTextContent("Buscando…");
    expect(status).toHaveAttribute("data-live-hint", "false");
  });

  it("antes del umbral NO menciona la consulta en vivo", () => {
    render(<SearchProgress />);
    act(() => {
      vi.advanceTimersByTime(LIVE_HINT_DELAY_MS - 1);
    });
    expect(screen.getByTestId("search-loading")).toHaveTextContent(
      "Buscando…"
    );
  });

  it("tras ~1.5 s cambia al mensaje de consulta en vivo a las tiendas", () => {
    render(<SearchProgress />);
    act(() => {
      vi.advanceTimersByTime(LIVE_HINT_DELAY_MS);
    });
    const status = screen.getByTestId("search-loading");
    expect(status).toHaveTextContent(
      /consultando home depot y construrama en vivo, puede tardar unos segundos/i
    );
    expect(status).toHaveAttribute("data-live-hint", "true");
  });
});
