/**
 * Cliente HTTP tipado: ÚNICO punto de salida hacia el backend (Django Ninja).
 *
 * - Base URL desde `NEXT_PUBLIC_API_URL` vía `src/lib/env.ts`.
 * - Todos los tipos de respuesta y de cuerpo se derivan de `schema.d.ts`
 *   (generado por `pnpm gen:api`); aquí NO se declara a mano ningún tipo de la
 *   API.
 * - Es el único archivo donde `fetch` está permitido (regla ESLint de F002).
 *
 * El import del schema es relativo a propósito (`./schema`): la regla
 * `no-restricted-imports` prohíbe el patrón "lib/api/schema" al resto del
 * código, que debe consumir la API a través de este cliente.
 *
 * Identidad anónima (F017): los endpoints de `/api/lists` se scope-an por una
 * clave de sesión que el cliente provee en el header `X-Session-Key`. Los
 * helpers aceptan `{ sessionKey }` en sus opciones y lo traducen a ese header.
 */
import { env } from "@/lib/env";
import type { paths } from "./schema";

/**
 * Opciones comunes a todos los helpers. Extiende `RequestInit` (para casos
 * avanzados: `signal`, `cache`, etc.) y añade `sessionKey`, que se envía como
 * header `X-Session-Key` (identidad anónima de F017). `method` se fija dentro
 * de cada helper y por eso se excluye aquí.
 */
export interface ApiRequestOptions extends Omit<RequestInit, "method" | "body"> {
  /** Clave de sesión anónima; se envía como header `X-Session-Key`. */
  sessionKey?: string;
}

/** Rutas que exponen un método dado según el contrato OpenAPI. */
type PathsWith<M extends "get" | "post" | "patch" | "delete"> = {
  [P in keyof paths]: paths[P] extends Record<M, unknown> ? P : never;
}[keyof paths];

type GetPaths = PathsWith<"get">;
type PostPaths = PathsWith<"post">;
type PatchPaths = PathsWith<"patch">;
type DeletePaths = PathsWith<"delete">;

/**
 * Parámetros de query de un GET, derivados del contrato. Resuelve a `never`
 * cuando la operación no declara `query` (p.ej. `/api/zones`); en ese caso el
 * helper `apiGetQuery` no es aplicable y se usa `apiGet`.
 */
type GetQuery<P extends GetPaths> = paths[P]["get"] extends {
  parameters: { query: infer Q };
}
  ? Q
  : never;

/** Solo las rutas GET cuya operación declara parámetros de query obligatorios. */
type GetPathsWithQuery = {
  [P in GetPaths]: [GetQuery<P>] extends [never] ? never : P;
}[GetPaths];

/**
 * Parámetros de ruta de un GET (p.ej. `{ id }` en `/api/products/{id}`),
 * derivados del contrato. Resuelve a `never` cuando la operación no declara
 * `path`; en ese caso se usa `apiGet`/`apiGetQuery`.
 */
type GetPathParams<P extends GetPaths> = paths[P]["get"] extends {
  parameters: { path: infer T };
}
  ? T
  : never;

/** Solo las rutas GET cuya operación declara parámetros de ruta (`{id}`). */
type GetPathsWithParams = {
  [P in GetPaths]: [GetPathParams<P>] extends [never] ? never : P;
}[GetPaths];

/**
 * Parámetros de query de un GET cuando pueden ser opcionales. A diferencia de
 * `GetQuery`, no exige que `query` exista: resuelve a `never` si la operación no
 * la declara, para componerlo con los parámetros de ruta.
 */
type GetOptionalQuery<P extends GetPaths> = paths[P]["get"] extends {
  parameters: { query: infer Q };
}
  ? Q
  : never;

/**
 * JSON de la respuesta exitosa (200 o 201) de un método/ruta, derivado del
 * contrato. Si la respuesta no tiene cuerpo JSON (p.ej. 204), resuelve a
 * `never` aquí; los helpers sin cuerpo (DELETE) lo tratan aparte.
 */
type SuccessJson<O> = O extends {
  responses: {
    200: { content: { "application/json": infer R } };
  };
}
  ? R
  : O extends {
        responses: {
          201: { content: { "application/json": infer R } };
        };
      }
    ? R
    : never;

/** Cuerpo JSON requerido por un método/ruta (request body), derivado del contrato. */
type RequestJson<O> = O extends {
  requestBody: { content: { "application/json": infer B } };
}
  ? B
  : never;

/** Respuesta JSON de un GET tipado. */
type GetJson200<P extends GetPaths> = SuccessJson<paths[P]["get"]>;
/** Respuesta JSON de un POST tipado (200 o 201). */
type PostJson<P extends PostPaths> = SuccessJson<paths[P]["post"]>;
/** Respuesta JSON de un PATCH tipado. */
type PatchJson<P extends PatchPaths> = SuccessJson<paths[P]["patch"]>;
/** Cuerpo requerido por un POST tipado. */
type PostBody<P extends PostPaths> = RequestJson<paths[P]["post"]>;
/** Cuerpo requerido por un PATCH tipado. */
type PatchBody<P extends PatchPaths> = RequestJson<paths[P]["patch"]>;

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
 * Sustituye los marcadores `{nombre}` de una plantilla de ruta del contrato
 * (p.ej. `/api/products/{id}`) por los valores de `params`, codificando cada uno
 * para la URL. Mantiene la plantilla como única fuente de verdad: el `path` que
 * recibe el helper sigue siendo una clave literal del schema.
 */
function buildPath(template: string, params: Record<string, unknown>): string {
  return template.replace(/\{([^}]+)\}/g, (_, name: string) => {
    const value = params[name];
    if (value === undefined || value === null) {
      throw new ApiError(`Falta el parámetro de ruta "${name}".`, 0);
    }
    return encodeURIComponent(String(value));
  });
}

/**
 * Serializa un objeto de query params (tipado por el contrato) a `?a=1&b=2`.
 * Omite valores `undefined`/`null` y convierte el resto a string. Devuelve "" si
 * no queda ningún parámetro, para no dejar un `?` colgando.
 */
function buildQueryString(query: Record<string, unknown>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null) {
      params.append(key, String(value));
    }
  }
  const serialized = params.toString();
  return serialized ? `?${serialized}` : "";
}

/**
 * Construye los headers comunes: `Accept` siempre, `X-Session-Key` si se
 * proveyó, `Content-Type: application/json` solo cuando hay cuerpo. Los headers
 * explícitos del caller (`options.headers`) tienen prioridad.
 */
function buildHeaders(
  hasBody: boolean,
  options?: ApiRequestOptions
): HeadersInit {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (hasBody) {
    headers["Content-Type"] = "application/json";
  }
  if (options?.sessionKey !== undefined) {
    headers["X-Session-Key"] = options.sessionKey;
  }
  return { ...headers, ...options?.headers };
}

/**
 * Núcleo de todas las peticiones: arma URL/headers/body, dispara `fetch` y
 * normaliza fallos de red y status no-2xx a `ApiError`. Devuelve la `Response`
 * cruda; cada helper decide cómo interpretar el cuerpo (JSON o vacío).
 */
async function request(
  path: string,
  method: "GET" | "POST" | "PATCH" | "DELETE",
  body: unknown,
  options?: ApiRequestOptions
): Promise<Response> {
  const hasBody = body !== undefined;
  let response: Response;
  try {
    response = await fetch(buildUrl(path), {
      ...options,
      method,
      headers: buildHeaders(hasBody, options),
      ...(hasBody ? { body: JSON.stringify(body) } : {}),
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

  return response;
}

/**
 * GET tipado contra el contrato. El `path` solo acepta rutas GET reales del
 * schema; el tipo devuelto es el JSON 200 de esa ruta. Lanza `ApiError` ante
 * fallo de red o status no-2xx.
 */
export async function apiGet<P extends GetPaths>(
  path: P,
  options?: ApiRequestOptions
): Promise<GetJson200<P>> {
  const response = await request(path, "GET", undefined, options);
  return (await response.json()) as GetJson200<P>;
}

/**
 * GET tipado con parámetros de query derivados del contrato. El `path` solo
 * acepta rutas GET cuya operación declara `query` en el schema, y `query` queda
 * tipado por esa forma exacta (cero `any`, cero tipos a mano). Internamente
 * serializa los params a la URL y delega en el núcleo `request`. Lanza
 * `ApiError` ante fallo de red o status no-2xx.
 */
export async function apiGetQuery<P extends GetPathsWithQuery>(
  path: P,
  query: GetQuery<P>,
  options?: ApiRequestOptions
): Promise<GetJson200<P>> {
  const queryString = buildQueryString(query as Record<string, unknown>);
  const response = await request(`${path}${queryString}`, "GET", undefined, options);
  return (await response.json()) as GetJson200<P>;
}

/**
 * GET tipado para rutas con parámetros de ruta (`{id}`) y, opcionalmente, query.
 *
 * El `path` solo acepta rutas GET cuya operación declara `path` en el contrato;
 * `params` queda tipado por esa forma exacta (p.ej. `{ id: string }`) y `query`
 * por su `query` del contrato (`{ zone_id }` en `/api/products/{id}`). Sustituye
 * los marcadores en la plantilla, serializa la query y delega en `request`.
 * Cero `any`, cero tipos a mano. Lanza `ApiError` ante fallo de red o no-2xx
 * (p.ej. 404 cuando el producto/zona no existe).
 */
export async function apiGetPath<P extends GetPathsWithParams>(
  path: P,
  params: GetPathParams<P>,
  query?: GetOptionalQuery<P>,
  options?: ApiRequestOptions
): Promise<GetJson200<P>> {
  const resolvedPath = buildPath(path, params as Record<string, unknown>);
  const queryString =
    query === undefined
      ? ""
      : buildQueryString(query as Record<string, unknown>);
  const response = await request(
    `${resolvedPath}${queryString}`,
    "GET",
    undefined,
    options
  );
  return (await response.json()) as GetJson200<P>;
}

/**
 * POST tipado: el `path` solo acepta rutas POST reales del schema, el `body`
 * está tipado por su `requestBody` y la respuesta por su 200/201. Lanza
 * `ApiError` ante fallo de red o status no-2xx.
 */
export async function apiPost<P extends PostPaths>(
  path: P,
  body: PostBody<P>,
  options?: ApiRequestOptions
): Promise<PostJson<P>> {
  const response = await request(path, "POST", body, options);
  return (await response.json()) as PostJson<P>;
}

/**
 * PATCH tipado: el `path` solo acepta rutas PATCH reales del schema, el `body`
 * está tipado por su `requestBody` y la respuesta por su 200. Lanza `ApiError`
 * ante fallo de red o status no-2xx.
 */
export async function apiPatch<P extends PatchPaths>(
  path: P,
  body: PatchBody<P>,
  options?: ApiRequestOptions
): Promise<PatchJson<P>> {
  const response = await request(path, "PATCH", body, options);
  return (await response.json()) as PatchJson<P>;
}

/**
 * DELETE tipado: el `path` solo acepta rutas DELETE reales del schema. Las
 * rutas DELETE del contrato responden 204 sin cuerpo, así que el helper no
 * intenta parsear JSON y resuelve a `void`. Lanza `ApiError` ante fallo de red
 * o status no-2xx.
 */
export async function apiDelete<P extends DeletePaths>(
  path: P,
  options?: ApiRequestOptions
): Promise<void> {
  await request(path, "DELETE", undefined, options);
}
