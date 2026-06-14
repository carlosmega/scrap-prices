/**
 * Identidad anónima por sesión (F022 + F017).
 *
 * Sin login, la cotización del usuario se scope-a por una clave de sesión que el
 * navegador genera una vez y persiste en `localStorage`. Esa clave viaja como
 * header `X-Session-Key` en TODAS las llamadas a `/api/lists*` (vía el soporte
 * de `sessionKey` de los helpers de `lib/api/client.ts`).
 *
 * `getSessionKey()` es idempotente: la primera vez genera un UUID v4 con
 * `crypto.randomUUID()` y lo guarda; las siguientes devuelven el mismo valor, de
 * modo que recargar la página conserva la cotización. Es resiliente a SSR (sin
 * `window`) y a valores corruptos en el almacenamiento.
 */

/** Clave de `localStorage` donde vive la clave de sesión anónima. */
export const SESSION_KEY_STORAGE_KEY = "construscan.sessionKey";

/**
 * UUID v4 canónico (8-4-4-4-12 hex, con el nibble de versión `4` y el de
 * variante `8|9|a|b`). Usado para validar lo persistido antes de reutilizarlo.
 */
const UUID_V4 =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/** `true` si `value` tiene el formato de un UUID v4. */
export function isUuidV4(value: string): boolean {
  return UUID_V4.test(value);
}

/**
 * Devuelve la clave de sesión persistida, generándola la primera vez.
 *
 * - Si hay un UUID v4 válido guardado, lo devuelve (estable entre recargas).
 * - Si no hay (o lo guardado está corrupto), genera uno nuevo con
 *   `crypto.randomUUID()`, lo persiste y lo devuelve.
 * - En SSR (sin `window`) devuelve un UUID efímero sin persistir: nunca debe
 *   usarse así en producción (las llamadas a listas son client-side), pero evita
 *   romper si se invoca durante el render del servidor.
 */
export function getSessionKey(): string {
  if (typeof window === "undefined") {
    return crypto.randomUUID();
  }

  const stored = window.localStorage.getItem(SESSION_KEY_STORAGE_KEY);
  if (stored !== null && isUuidV4(stored)) {
    return stored;
  }

  const fresh = crypto.randomUUID();
  window.localStorage.setItem(SESSION_KEY_STORAGE_KEY, fresh);
  return fresh;
}
