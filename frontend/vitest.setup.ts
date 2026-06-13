import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// Desmonta el árbol React entre tests para evitar fugas de DOM.
afterEach(() => {
  cleanup();
});
