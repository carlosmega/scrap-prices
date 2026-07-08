import { defineConfig, devices } from "@playwright/test";

/**
 * Config E2E de ConstruScan.
 *
 * `webServer` es un array de dos procesos que Playwright levanta antes de la
 * suite y derriba al terminar: el backend Django (SQLite, sin Docker) y el
 * frontend Next.js. En local `reuseExistingServer` evita relevantar servidores
 * ya en marcha; en CI siempre arranca limpio.
 *
 * El gate formal de E2E es `pnpm test:e2e` (Fase 6 de `./init.sh --e2e`).
 */
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  reporter: [["html", { outputFolder: "playwright-report", open: "never" }]],
  use: {
    baseURL: "http://localhost:3300",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      // Backend Django + Ninja con SQLite. Antes de servir aplica migraciones
      // y siembra el grafo demo (Monterrey Metro · varilla) para que la UI
      // tenga zonas reales que listar (F019). `seed` es idempotente.
      command:
        "uv run python manage.py migrate && uv run python manage.py seed && uv run python manage.py runserver 127.0.0.1:8800",
      cwd: "../backend",
      url: "http://127.0.0.1:8800/api/health",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        // F033: la búsqueda dispara scraping EN VIVO cuando no hay datos
        // frescos para término+zona. En E2E eso jamás debe ocurrir (suite
        // offline): el seed deja los términos buscados frescos, y este TTL
        // enorme blinda además el caso de un backend reusado entre corridas
        // (reuseExistingServer) cuyo seed corrió hace días. OJO: no protege
        // términos SIN ninguna observación — ningún test E2E debe buscar
        // términos fuera del seed.
        SEARCH_LIVE_TTL_HOURS: "876000",
      },
    },
    {
      // Frontend Next.js en modo dev.
      command: "pnpm dev --port 3300",
      cwd: "../frontend",
      url: "http://localhost:3300",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
