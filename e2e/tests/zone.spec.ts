import { expect, test } from "@playwright/test";

/**
 * E2E de selección de zona (F019, flujo feliz A1·CA3).
 *
 * Playwright levanta backend (migrate + seed → zona "Monterrey Metro") y
 * frontend vía `webServer`. El test ejerce: abrir la home, elegir la zona en el
 * selector, ver que queda seleccionada, y que la selección PERSISTE tras
 * recargar la página (localStorage).
 */
test("elegir zona y que persista tras recargar", async ({ page }) => {
  await page.goto("/");

  // La home carga: encabezado ConstruScan visible.
  await expect(
    page.getByRole("heading", { name: "ConstruScan" })
  ).toBeVisible();

  // El selector se renderiza tras cargar las zonas (estado "datos").
  const trigger = page.getByTestId("zone-select-trigger");
  await expect(trigger).toBeVisible({ timeout: 15_000 });

  // Abrir el selector y elegir "Monterrey Metro" (la opción combina nombre y
  // estado: "Monterrey Metro · NL").
  await trigger.click();
  await page
    .getByRole("option", { name: /monterrey metro/i })
    .click();

  // Queda seleccionada: el indicador muestra el nombre de la zona.
  const selected = page.getByTestId("selected-zone");
  await expect(selected).toBeVisible();
  await expect(selected).toContainText("Monterrey Metro");

  // Persistencia: tras recargar, la selección sigue ahí (localStorage).
  await page.reload();
  const selectedAfterReload = page.getByTestId("selected-zone");
  await expect(selectedAfterReload).toBeVisible({ timeout: 15_000 });
  await expect(selectedAfterReload).toContainText("Monterrey Metro");
});
