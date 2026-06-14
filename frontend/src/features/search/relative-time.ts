/**
 * Helper PURO de frescura: convierte un instante (`captured_at` del contrato) en
 * un texto "hace X" en español (B1: frescura visible, RNF3 el dato nunca se
 * oculta).
 *
 * Es una función pura y determinista: recibe `now` como segundo argumento (por
 * defecto el reloj real) para que el test unitario fije el "ahora" y no dependa
 * del momento de ejecución. No toca el DOM ni la red.
 */

/**
 * Devuelve la frescura relativa de `date` respecto a `now`.
 *
 * - Entrada inválida o nula → `null` (la UI muestra un fallback como
 *   "sin fecha"); así el dato crudo nunca se inventa.
 * - Futuro o < 60 s → "hace un momento".
 * - El resto escala por minutos / horas / días, con singular/plural correcto.
 *
 * @param date instante ISO-8601 (string) o `Date`; admite `null`/`undefined`.
 * @param now  referencia temporal; por defecto `new Date()`.
 */
export function relativeTime(
  date: string | Date | null | undefined,
  now: Date = new Date()
): string | null {
  if (date === null || date === undefined) {
    return null;
  }

  const then = date instanceof Date ? date : new Date(date);
  const thenMs = then.getTime();
  if (Number.isNaN(thenMs)) {
    return null;
  }

  const diffMs = now.getTime() - thenMs;
  const diffSeconds = Math.floor(diffMs / 1000);

  // Futuro (reloj desfasado) o menos de un minuto: lo tratamos igual.
  if (diffSeconds < 60) {
    return "hace un momento";
  }

  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) {
    return `hace ${diffMinutes} ${diffMinutes === 1 ? "minuto" : "minutos"}`;
  }

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `hace ${diffHours} ${diffHours === 1 ? "hora" : "horas"}`;
  }

  const diffDays = Math.floor(diffHours / 24);
  return `hace ${diffDays} ${diffDays === 1 ? "día" : "días"}`;
}

/**
 * Variante prefijada para la UI de resultados: "actualizado hace X" o, si no hay
 * fecha, un texto explícito que conserva la transparencia del dato.
 */
export function freshnessLabel(
  date: string | Date | null | undefined,
  now?: Date
): string {
  const relative = relativeTime(date, now);
  return relative === null ? "actualización sin fecha" : `actualizado ${relative}`;
}
