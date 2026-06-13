/**
 * Cliente HTTP tipado: ÚNICO punto de salida hacia el backend (Django Ninja).
 *
 * - Base URL desde `NEXT_PUBLIC_API_URL` vía `src/lib/env.ts`.
 * - Todos los tipos de respuesta se derivan de `schema.d.ts` (generado por
 *   `pnpm gen:api`); aquí NO se declara a mano ningún tipo de respuesta de API.
 * - Es el único archivo donde `fetch` está permitido (regla ESLint de F002).
 *
 * El import del schema es relativo a propósito (`./schema`): la regla
 * `no-restricted-imports` prohíbe el patrón "lib/api/schema" al resto del
 * código, que debe consumir la API a través de este cliente.
 */
import { env } from "@/lib/env";
import type { paths } from "./schema";

/** Rutas GET disponibles según el contrato OpenAPI. */
type GetPaths = {
  [P in keyof paths]: paths[P] extends { get: unknown } ? P : never;
}[keyof paths];

/** Tipo del cuerpo JSON de la respuesta 200 de un GET, derivado del contrato. */
type GetJson200<P extends GetPaths> = paths[P] extends {
  get: {
    responses: {
      200: { content: { "application/json": infer R } };
    };
  };
}
  ? R
  : never;

/**
 * Error de API normalizado. Se lanza cuando el backend responde con un código
 * fuera del rango 2xx o cuando la petición de red falla (backend caído, CORS).
 */
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Quita la barra final de la base URL para no duplicar `/`. */
function buildUrl(path: string): string {
  const base = env.apiUrl.replace(/\/+$/, "");
  return `${base}${path}`;
}

/**
 * GET tipado contra el contrato. El `path` solo acepta rutas GET reales del
 * schema; el tipo devuelto es el JSON 200 de esa ruta. Lanza `ApiError` ante
 * fallo de red o status no-2xx.
 */
export async function apiGet<P extends GetPaths>(
  path: P,
  init?: RequestInit
): Promise<GetJson200<P>> {
  let response: Response;
  try {
    response = await fetch(buildUrl(path), {
      ...init,
      method: "GET",
      headers: {
        Accept: "application/json",
        ...init?.headers,
      },
    });
  } catch (cause) {
    // Fallo de red: backend caído, DNS, CORS bloqueado, etc.
    throw new ApiError(
      cause instanceof Error
        ? `No se pudo contactar al backend: ${cause.message}`
        : "No se pudo contactar al backend.",
      0
    );
  }

  if (!response.ok) {
    throw new ApiError(
      `El backend respondió con estado ${response.status}.`,
      response.status
    );
  }

  return (await response.json()) as GetJson200<P>;
}
