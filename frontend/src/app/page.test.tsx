import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import Home from "./page";

// Test de humo (F002): demuestra que el runner corre y que la home renderiza
// con un componente shadcn visible. No toca red.
describe("Home", () => {
  it("renderiza el título de la app", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { name: /construscan/i })
    ).toBeInTheDocument();
  });

  it("muestra un componente shadcn (botón Buscar)", () => {
    render(<Home />);
    expect(screen.getByRole("button", { name: /buscar/i })).toBeInTheDocument();
  });
});
