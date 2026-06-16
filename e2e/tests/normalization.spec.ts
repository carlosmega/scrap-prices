import { expect, test } from "@playwright/test";

/**
 * E2E de normalización de unidad (F031, criterio de aceptación clave).
 *
 * Playwright levanta backend (migrate + seed → zona "Monterrey Metro", varilla
 * con `mass_kg` por canónico y `sale_unit` por retailer: Home Depot LISTA por
 * tonelada, Construrama por kilogramo) y frontend vía `webServer`.
 *
 * El test prueba que la comparación cross-retailer es REAL, no por el número
 * nativo crudo: para la varilla 1/2" (#4), Home Depot —cuyo precio nativo es
 * ~$20,000/ton, un número MUCHO mayor que los ~$21/kg de Construrama— sale
 * marcado como "mejor precio" porque su $/kg normalizado es menor. Y su precio
 * NATIVO "$.../ton" sigue visible (transparencia F031).
 */

/** Convierte "$20,085.00" / "$20.09 / kg" a número para comparaciones. */
function parsePrice(text: string): number {
  const cleaned = text.replace(/[^0-9.]/g, "");
  return Number(cleaned);
}

test("varilla 1/2 en Monterrey Metro: Home Depot es mejor precio por $/kg y su nativo $/ton es visible", async ({
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

  // Ordenar por precio (menor $/kg primero) y buscar la varilla 1/2".
  // El match del backend es substring sobre el nombre del canónico (sin
  // tokenizar), así que `1/2` aísla a la #4 ("Varilla corrugada 1/2" (#4) 12m")
  // frente a la #3 (3/8") y la #2 (1/4").
  const input = page.getByTestId("search-input");
  await expect(input).toBeVisible();
  await page.getByTestId("search-sort").selectOption("price");
  await input.fill('1/2"');
  await page.getByTestId("search-submit").click();

  // Localizar la tarjeta de la varilla 1/2" (#4) por su título.
  const card = page
    .getByTestId("search-result")
    .filter({ hasText: /1\/2/ })
    .first();
  await expect(card).toBeVisible({ timeout: 15_000 });

  // Filas de ambos retailers.
  const hdRow = card.getByTestId("retailer-row").filter({ hasText: /home depot/i });
  const crRow = card
    .getByTestId("retailer-row")
    .filter({ hasText: /construrama/i });
  await expect(hdRow).toBeVisible();
  await expect(crRow).toBeVisible();

  // El badge "mejor precio" existe y está en la fila de Home Depot.
  await expect(card.getByTestId("best-price-badge")).toHaveCount(1);
  await expect(hdRow.getByTestId("best-price-badge")).toBeVisible();
  await expect(crRow.getByTestId("best-price-badge")).toHaveCount(0);

  // El precio NATIVO de Home Depot es "$.../ton" y es visible (transparencia).
  const hdNative = hdRow.getByTestId("retailer-native-price");
  await expect(hdNative).toBeVisible();
  await expect(hdNative).toContainText(/\/ ton/i);

  // Sanidad de la inversión nativo vs normalizado: el número NATIVO de HD
  // (miles, por tonelada) es MAYOR que el de Construrama (decenas, por kg),
  // pero por $/kg HD es MENOR (de ahí que sea el "mejor precio").
  const hdNativeValue = parsePrice((await hdNative.textContent()) ?? "");
  const crNativeValue = parsePrice(
    (await crRow.getByTestId("retailer-native-price").textContent()) ?? ""
  );
  expect(hdNativeValue).toBeGreaterThan(crNativeValue);

  const hdPerKg = parsePrice(
    (await hdRow.getByTestId("retailer-price-per-kg").textContent()) ?? ""
  );
  const crPerKg = parsePrice(
    (await crRow.getByTestId("retailer-price-per-kg").textContent()) ?? ""
  );
  expect(hdPerKg).toBeLessThan(crPerKg);
});
