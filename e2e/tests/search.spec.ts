import { expect, test } from "@playwright/test";

/**
 * E2E de búsqueda + resultados comparados (F020, flujo feliz B1).
 *
 * Playwright levanta backend (migrate + seed → zona "Monterrey Metro",
 * categoría varilla con precios en Home Depot y Construrama) y frontend vía
 * `webServer`. El test ejerce: abrir la home, elegir la zona, buscar "varilla",
 * ver ≥1 resultado con precios de AMBOS retailers, y comprobar que al ordenar
 * por precio el menor aparece primero.
 */

/** Convierte "$1,234.50 MXN" / "$20.09 / kg" a número para comparaciones. */
function parsePrice(text: string): number {
  const cleaned = text.replace(/[^0-9.]/g, "");
  return Number(cleaned);
}

test("buscar varilla en Monterrey Metro: ambos retailers y orden por precio", async ({
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

  // El panel de búsqueda ya no pide zona: el input es visible.
  const input = page.getByTestId("search-input");
  await expect(input).toBeVisible();

  // Asegurar orden por precio (menor primero) y buscar "varilla".
  await page.getByTestId("search-sort").selectOption("price");
  await input.fill("varilla");
  await page.getByTestId("search-submit").click();

  // Hay al menos un resultado.
  const results = page.getByTestId("search-result");
  await expect(results.first()).toBeVisible({ timeout: 15_000 });
  expect(await results.count()).toBeGreaterThanOrEqual(1);

  // El primer resultado muestra precios de AMBOS retailers (HD y Construrama).
  const firstCard = results.first();
  await expect(
    firstCard.getByRole("listitem").filter({ hasText: /home depot/i })
  ).toBeVisible();
  await expect(
    firstCard.getByRole("listitem").filter({ hasText: /construrama/i })
  ).toBeVisible();

  // Ambos retailers tienen precio en la zona piloto (no "sin precio").
  await expect(firstCard.getByTestId("retailer-price")).toHaveCount(2);

  // Frescura visible ("actualizado hace X").
  await expect(
    firstCard.getByTestId("retailer-freshness").first()
  ).toContainText(/actualizado hace/i);

  // Orden por precio = base de comparación $/kg (F031), NO el titular $/pieza
  // ni el nativo crudo. Dentro de la primera tarjeta, la PRIMERA fila de
  // retailer tiene el menor $/kg de la tarjeta y es la marcada "mejor precio".
  const perKgTexts = await firstCard
    .getByTestId("retailer-price-per-kg")
    .allTextContents();
  const perKg = perKgTexts.map(parsePrice);
  expect(perKg.length).toBeGreaterThanOrEqual(2);
  const minPerKg = Math.min(...perKg);
  expect(perKg[0]).toBeCloseTo(minPerKg, 2);

  // El badge "mejor precio" está en la primera fila (menor $/kg) de la tarjeta.
  await expect(firstCard.getByTestId("best-price-badge")).toHaveCount(1);
  await expect(
    firstCard.getByTestId("retailer-row").first().getByTestId("best-price-badge")
  ).toBeVisible();
});
