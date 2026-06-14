import { expect, test } from "@playwright/test";

/**
 * E2E del detalle de producto + historial (F021, flujo feliz B2).
 *
 * Playwright levanta backend (migrate + seed → zona "Monterrey Metro", varilla
 * con precios e historial en Home Depot y Construrama) y frontend vía
 * `webServer`. El test ejerce el flujo completo: abrir la home, elegir la zona,
 * buscar "varilla", hacer click en un resultado para ir a `/products/{id}`, y
 * verificar en el detalle que se ven precios por retailer y al menos una entrada
 * de historial.
 */
test("desde la búsqueda al detalle: precios por retailer e historial", async ({
  page,
}) => {
  await page.goto("/");

  // La home carga.
  await expect(
    page.getByRole("heading", { name: "ConstruScan" })
  ).toBeVisible();

  // Elegir la zona "Monterrey Metro" (selector de F019).
  const trigger = page.getByTestId("zone-select-trigger");
  await expect(trigger).toBeVisible({ timeout: 15_000 });
  await trigger.click();
  await page.getByRole("option", { name: /monterrey metro/i }).click();
  await expect(page.getByTestId("selected-zone")).toContainText(
    "Monterrey Metro"
  );

  // Buscar "varilla".
  const input = page.getByTestId("search-input");
  await expect(input).toBeVisible();
  await input.fill("varilla");
  await page.getByTestId("search-submit").click();

  // Hay al menos un resultado; entrar al detalle del primero por su enlace.
  const results = page.getByTestId("search-result");
  await expect(results.first()).toBeVisible({ timeout: 15_000 });
  await page.getByTestId("search-result-link").first().click();

  // Estamos en la ruta del detalle.
  await expect(page).toHaveURL(/\/products\/[^/]+$/);

  // El detalle carga con sus datos.
  const detail = page.getByTestId("product-detail");
  await expect(detail).toBeVisible({ timeout: 15_000 });

  // Specs del canónico visibles.
  await expect(page.getByTestId("product-specs")).toBeVisible();

  // Precios ACTUALES por retailer: AMBOS retailers del seed (HD y Construrama)
  // con precio en la zona piloto.
  const prices = page.getByTestId("product-retailer-price");
  await expect(prices.first()).toBeVisible();
  expect(await prices.count()).toBe(2);

  // Frescura visible ("actualizado hace X") en al menos un retailer.
  await expect(
    page.getByTestId("product-retailer-freshness").first()
  ).toContainText(/actualizado hace/i);

  // Enlace a la ficha del retailer abre en pestaña nueva.
  const retailerLink = page.getByTestId("product-retailer-link").first();
  await expect(retailerLink).toHaveAttribute("target", "_blank");
  await expect(retailerLink).toHaveAttribute("rel", /noopener/);

  // Historial: al menos una entrada (el seed crea varias lecturas por retailer).
  const historyRows = page.getByTestId("product-history-row");
  await expect(historyRows.first()).toBeVisible();
  expect(await historyRows.count()).toBeGreaterThanOrEqual(1);

  // El enlace de "volver a la búsqueda" existe.
  await expect(page.getByTestId("product-back")).toBeVisible();
});
