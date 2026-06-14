import { expect, test } from "@playwright/test";

/**
 * E2E de la cotización (F022, flujo feliz Épica C).
 *
 * Playwright levanta backend (migrate + seed → zona "Monterrey Metro", varilla
 * con precios en Home Depot y Construrama) y frontend vía `webServer`. El test
 * ejerce el flujo completo de la cotización:
 *   zona MTY → buscar "varilla" → AGREGAR un producto a la cotización →
 *   abrir la lista y ver el ítem con su snapshot + total → EDITAR cantidad
 *   (el total cambia) → QUITAR el ítem (lista vacía).
 *
 * La identidad es anónima por `X-Session-Key` (localStorage); como cada test
 * arranca con un contexto limpio, la sesión empieza sin cotización.
 */

/** Convierte "$1,234.50 MXN" / "$59.50" a número para comparaciones. */
function parsePrice(text: string): number {
  const cleaned = text.replace(/[^0-9.]/g, "");
  return Number(cleaned);
}

test("cotización: agregar → ver snapshot+total → editar cantidad → quitar", async ({
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

  // Hay al menos un resultado con precios.
  const results = page.getByTestId("search-result");
  await expect(results.first()).toBeVisible({ timeout: 15_000 });

  // Agregar el PRIMER SKU con precio a la cotización.
  const addButton = page.getByTestId("add-to-quote").first();
  await expect(addButton).toBeVisible();
  await addButton.click();

  // El botón confirma que se agregó.
  await expect(addButton).toHaveAttribute("data-state", "added", {
    timeout: 15_000,
  });

  // El badge del shell muestra 1 ítem.
  await expect(page.getByTestId("quote-badge-count")).toHaveText("1", {
    timeout: 15_000,
  });

  // Abrir la cotización desde el badge.
  await page.getByTestId("quote-badge").click();
  await expect(page).toHaveURL(/\/cotizacion$/);

  // El detalle de la cotización carga con un ítem.
  const detail = page.getByTestId("quote-detail");
  await expect(detail).toBeVisible({ timeout: 15_000 });
  const item = page.getByTestId("quote-item");
  await expect(item).toHaveCount(1);

  // El ítem muestra su snapshot de precio y un line-total.
  await expect(page.getByTestId("quote-item-snapshot")).toBeVisible();
  const lineTotalText = await page
    .getByTestId("quote-item-line-total")
    .textContent();
  expect(lineTotalText).toBeTruthy();

  // El total de la cotización es visible y > 0.
  const totalBefore = parsePrice(
    (await page.getByTestId("quote-total").textContent()) ?? ""
  );
  expect(totalBefore).toBeGreaterThan(0);

  // Cantidad inicial = 1.
  await expect(page.getByTestId("quote-item-quantity-value")).toHaveText("1");

  // EDITAR cantidad: incrementar a 2 → el total cambia (sube).
  await page.getByTestId("quote-item-increment").click();
  await expect(page.getByTestId("quote-item-quantity-value")).toHaveText("2", {
    timeout: 15_000,
  });
  await expect
    .poll(
      async () =>
        parsePrice(
          (await page.getByTestId("quote-total").textContent()) ?? ""
        ),
      { timeout: 15_000 }
    )
    .toBeGreaterThan(totalBefore);

  // Con cantidad 2, el total debe ser ~2x el snapshot inicial.
  const totalAfter = parsePrice(
    (await page.getByTestId("quote-total").textContent()) ?? ""
  );
  expect(totalAfter).toBeCloseTo(totalBefore * 2, 2);

  // QUITAR el ítem → la cotización queda vacía.
  await page.getByTestId("quote-item-remove").click();
  await expect(page.getByTestId("quote-empty")).toBeVisible({
    timeout: 15_000,
  });
  await expect(page.getByTestId("quote-item")).toHaveCount(0);
});
