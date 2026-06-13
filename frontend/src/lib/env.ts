/**
 * Configuración de entorno pública del frontend.
 *
 * `NEXT_PUBLIC_API_URL` apunta al backend (Django Ninja). El consumo real de
 * la API llega en F003 a través de `src/lib/api/client.ts`; aquí solo se
 * expone el valor con su default para que la app lo lea de forma tipada.
 */
export const env = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
} as const;
