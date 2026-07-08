import { expect, test } from "@playwright/test";

/**
 * E2E de búsqueda + resultados comparados (F020, flujo feliz B1) y de la
 * sección cruda por tienda (F033).
 *
 * Playwright levanta backend (migrate + seed → zona "Monterrey Metro",
 * categoría varilla con precios en Home Depot y Construrama) y frontend vía
 * `webServer`. El primer test ejerce: abrir la home, elegir la zona, buscar
 * "varilla", ver ≥1 resultado con precios de AMBOS retailers, y comprobar que
 * al ordenar por precio el menor aparece primero.
 *
 * F033 (segundo test, SIN red a retailers): el seed deja las observaciones de
 * "varilla" FRESCAS, así que la búsqueda NO dispara la corrida en vivo (por
 * eso aquí no debe aparecer el badge de vivo) y además siembra un hallazgo
 * crudo real de Construrama sin matchear (el amarrador de varillas Truper,
 * SKU 0204000086, $125/pieza) cuyo raw_name matchea "varilla": la misma
 * búsqueda muestra los canónicos comparados Y la sección "Resultados de las
 * tiendas (sin comparar)", desde la que se puede agregar a la cotización.
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

test("F033: buscar varilla muestra la sección cruda (amarrador Truper) y cotiza desde ahí", async ({
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

  // Los canónicos comparados siguen ahí (F031 intacto).
  await expect(page.getByTestId("search-result").first()).toBeVisible({
    timeout: 15_000,
  });

  // Y ADEMÁS aparece la sección cruda por tienda (F033).
  const rawSection = page.getByTestId("raw-results-section");
  await expect(rawSection).toBeVisible();
  await expect(rawSection).toContainText(
    /resultados de las tiendas \(sin comparar\)/i
  );

  // Grupo de Construrama con el hallazgo real del seed: el amarrador Truper.
  const crGroup = rawSection
    .getByTestId("raw-retailer-group")
    .filter({ hasText: /construrama/i });
  await expect(crGroup).toBeVisible();
  const amarrador = crGroup
    .getByTestId("raw-result")
    .filter({ hasText: /amarrador de varillas/i });
  await expect(amarrador).toBeVisible();

  // Precio NATIVO con su unidad de venta ($125.00 / pieza).
  const rawPrice = amarrador.getByTestId("raw-result-price");
  await expect(rawPrice).toContainText("$125.00");
  await expect(rawPrice).toContainText(/pieza/i);

  // Frescura "hace X" y disponibilidad visibles.
  const freshness = amarrador.getByTestId("raw-result-freshness");
  await expect(freshness).toContainText(/actualizado hace/i);
  await expect(freshness).toContainText(/disponible/i);

  // Link a la ficha del retailer en pestaña nueva.
  const fichaLink = amarrador.getByTestId("raw-result-link");
  await expect(fichaLink).toHaveAttribute("target", "_blank");
  await expect(fichaLink).toHaveAttribute("rel", /noopener/);
  await expect(fichaLink).toHaveAttribute("href", /construrama\.com/);

  // Datos FRESCOS del seed ⇒ la corrida en vivo NO se disparó: sin badge.
  // (Garantiza de paso que este E2E fue 100 % offline.)
  await expect(page.getByTestId("live-run-badge")).toHaveCount(0);

  // Agregar el hallazgo crudo a la cotización (mismo mecanismo con
  // retailer_product_id): el botón confirma y el badge del shell incrementa.
  const addButton = amarrador.getByTestId("add-to-quote");
  await expect(addButton).toBeVisible();
  await addButton.click();
  await expect(addButton).toHaveAttribute("data-state", "added", {
    timeout: 15_000,
  });
  await expect(page.getByTestId("quote-badge-count")).toHaveText("1", {
    timeout: 15_000,
  });
});
