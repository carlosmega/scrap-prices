import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

// Vitest + Testing Library en entorno jsdom para unit tests de componentes/hooks.
// `tsconfigPaths` resuelve el alias "@/*" igual que Next. El setup carga los
// matchers de @testing-library/jest-dom.
export default defineConfig({
  plugins: [tsconfigPaths(), react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    css: true,
  },
});
