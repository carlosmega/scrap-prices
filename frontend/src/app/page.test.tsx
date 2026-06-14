import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import Home from "./page";

// El cliente HTTP es el único punto de fetch; lo mockeamos para que la home
// renderice sin tocar red (los hijos Client Component llaman a la API al
// montar). Las promesas quedan pendientes: nos basta el render inicial.
vi.mock("@/lib/api/client", async () => {
  const actual =
    await vi.importActual<typeof import("@/lib/api/client")>(
      "@/lib/api/client"
    );
  return {
    ...actual,
    apiGet: vi.fn(() => new Promise(() => {})),
    apiPost: vi.fn(() => new Promise(() => {})),
  };
});

describe("Home", () => {
  it("renderiza el título de la app", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { name: /construscan/i })
    ).toBeInTheDocument();
  });

  it("muestra el selector de zona", () => {
    render(<Home />);
    expect(screen.getByTestId("zone-selector")).toBeInTheDocument();
    expect(
      screen.getByText("Tu zona", { selector: "[data-slot='card-title']" })
    ).toBeInTheDocument();
  });

  it("ya no muestra el placeholder de F003", () => {
    render(<Home />);
    expect(
      screen.queryByText(/aún sin consumo de api/i)
    ).not.toBeInTheDocument();
  });
});
