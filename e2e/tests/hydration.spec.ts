import { expect, test } from "@playwright/test";

/**
 * Guardia de regresión de hidratación (F030).
 *
 * El bug original: los hooks que leían `localStorage` en el render inicial
 * (`useSelectedZone`, cotización) hacían que el HTML del servidor (sin
 * `localStorage` → "Elige tu zona…") difiriera del primer render del cliente
 * (con zona guardada → "Precios para…"), disparando un "Hydration failed".
 *
 * Este test PRE-SETEA una zona en `localStorage` ANTES de cargar `/` (vía
 * `page.addInitScript`, que corre antes del bundle de la app), escucha errores
 * de consola y de página, navega a `/`, y FALLA si aparece cualquier mensaje de
 * hidratación. Con el fix SSR-safe debe pasar: el primer paint muestra el estado
 * por-defecto (server snapshot) y, tras hidratar, refleja la zona guardada.
 */

/** Patrón que delata un error de hidratación de React/Next. */
const HYDRATION_PATTERN = /hydration|did not match|hydration failed/i;

/** Clave de `localStorage` de la zona seleccionada (ver `use-selected-zone.ts`). */
const SELECTED_ZONE_STORAGE_KEY = "construscan.selectedZone";

test("cargar / con una zona ya guardada no produce hydration mismatch", async ({
  page,
}) => {
  // Pre-seteamos la zona en localStorage ANTES de que cargue cualquier script de
  // la app. `addInitScript` se ejecuta en el contexto de la página antes de la
  // navegación, así el primer render del cliente ya "vería" la zona guardada
  // (que era justo lo que provocaba el mismatch antes del fix).
  await page.addInitScript(
    ([key, value]) => {
      window.localStorage.setItem(key, value);
    },
    [
      SELECTED_ZONE_STORAGE_KEY,
      JSON.stringify({ id: "seed-zone", name: "Monterrey Metro" }),
    ]
  );

  // Capturamos errores de hidratación tanto de consola como de página.
  const hydrationErrors: string[] = [];
  page.on("console", (message) => {
    if (HYDRATION_PATTERN.test(message.text())) {
      hydrationErrors.push(`console: ${message.text()}`);
    }
  });
  page.on("pageerror", (error) => {
    if (HYDRATION_PATTERN.test(error.message)) {
      hydrationErrors.push(`pageerror: ${error.message}`);
    }
  });

  await page.goto("/");

  // La home carga: encabezado ConstruScan visible.
  await expect(
    page.getByRole("heading", { name: "ConstruScan" })
  ).toBeVisible();

  // Tras hidratar, la zona guardada se refleja en el panel de búsqueda
  // ("Precios para Monterrey Metro"): demuestra que el fix NO se quedó en el
  // estado por-defecto, sino que pobló desde localStorage tras montar.
  await expect(page.getByTestId("search-panel")).toContainText(
    "Monterrey Metro",
    { timeout: 15_000 }
  );

  // Damos un instante a que React termine de hidratar y vacíe la consola.
  await page.waitForTimeout(500);

  // El gate: cero mensajes de hidratación.
  expect(
    hydrationErrors,
    `Se detectaron errores de hidratación:\n${hydrationErrors.join("\n")}`
  ).toHaveLength(0);
});
