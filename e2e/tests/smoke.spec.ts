import { expect, test } from "@playwright/test";

/**
 * Smoke fullstack (F004): la home carga y el indicador de salud refleja el
 * backend arriba. Playwright levanta backend + frontend vía `webServer`, así
 * que este test ejerce el lazo completo (fetch client-side a /api/health con
 * CORS desde localhost:3300, configurado en F001).
 */
test("la home carga y el indicador de salud muestra ok", async ({ page }) => {
  await page.goto("/");

  // 1. La página carga: el heading "ConstruScan" es visible.
  await expect(
    page.getByRole("heading", { name: "ConstruScan" })
  ).toBeVisible();

  // 2. El indicador de salud resuelve a "ok" tras el fetch a /api/health.
  //    HealthIndicator renderiza "Backend: ok" en el estado de datos.
  await expect(page.getByText(/ok/i)).toBeVisible({ timeout: 15_000 });
});
