# impl F017 — backend (API de listas de cotización)

Spec aplicada: `specs/F017-api-listas.md` (8 endpoints CRUD de `/api/lists`,
identidad anónima por `X-Session-Key`, snapshot inmutable de precio, totales).

## Decisiones tomadas (máx. 5 líneas)
1. Identidad anónima: el header `X-Session-Key` se lee en el router como `Header`
   y se pasa a services; falta de header donde se requiere → 400 vía `HttpError`.
2. Scoping estricto en services: helpers privados `_lista_de_sesion` /
   `_item_de_sesion` filtran por `session_key`; cualquier ajeno/inexistente →
   excepción de dominio `ListaNoEncontrada` (404), sin filtrar info de otra sesión.
3. Snapshot inmutable: `agregar_item` copia `captured_price`/`captured_at` de
   `prices.services.ultima_observacion(rp, zone=lista.zone)` (si la lista no tiene
   zona, `zone=None` → última observación sin zona); sin observación →
   `SinPrecioParaSnapshot` (422). El ítem nunca relee el precio en vivo.
4. `quantity >= 1` validado en schema (`Field(ge=1)`) → 422 automático. DELETE
   devuelve 204 sin body con `Status(204, None)`; POST devuelve 201 con `Status(201, ...)`
   (evita el `DeprecationWarning` del retorno por tupla en Ninja 1.6).
5. Router sin ORM (regla de capas, verificado con `lint-imports`): toda la lógica
   y el ORM viven en `apps/lists/services.py`; subtotal/total reutilizan
   `subtotal_lista` (F009), `total == subtotal` en MVP (sin impuestos/envío).

## Archivos creados/modificados
- `backend/apps/lists/schemas.py` — CREADO: `UserListOut`, `UserListItemOut`,
  `UserListDetailOut`, `UserListCreateIn`, `UserListPatchIn`,
  `UserListItemCreateIn`, `UserListItemPatchIn` (shapes exactas de la spec;
  `RetailerRefOut` reutilizado de `catalog.schemas`).
- `backend/apps/lists/services.py` — MODIFICADO: añadidos CRUD scope-ado por
  sesión, captura de snapshot, serializadores a schemas y excepciones de dominio
  (`ListaNoEncontrada`, `ProductoNoEncontrado`, `SinPrecioParaSnapshot`).
  Se conserva `subtotal_lista` (F009).
- `backend/apps/lists/api.py` — CREADO: router `lists` con los 8 endpoints,
  `response=` explícito por endpoint (incl. `{204: None}`), lectura del header y
  traducción de excepciones a 400/404/422. Sin ORM.
- `backend/config/api.py` — MODIFICADO: monta `lists_router` con prefijo `""`
  (rutas quedan EXACTAS bajo `/api/lists`).
- `backend/apps/lists/tests/test_api.py` — CREADO: 28 tests (flujo completo,
  snapshot inmutable, scoping A/B, 400 sin header, 422 quantity/sin-precio, 404).
- `backend/openapi.json` — REGENERADO (contrato cambió).

## ¿Cambió el contrato OpenAPI?
**SÍ.** Regenerado con
`uv run python manage.py export_openapi_schema --api config.api.api --indent 2 --output openapi.json`.
Contiene las 4 plantillas de ruta (`/api/lists`, `/api/lists/{list_id}`,
`/api/lists/{list_id}/items`, `/api/lists/{list_id}/items/{item_id}`) cubriendo
los 8 endpoints, los 7 schemas nuevos, el parámetro header `x_session_key` y las
respuestas 204 "No Content" en los DELETE.
**Acción para el líder:** disparar `pnpm gen:api` en frontend antes del
implementer-frontend (la capa frontend de F017 extiende `client.ts`).

## Output REAL de las verificaciones

### `uv run ruff check .`
```
All checks passed!
```

### `uv run python manage.py makemigrations --check --dry-run`
```
No changes detected
```
(Sin modelos nuevos: los modelos `UserList`/`UserListItem` ya existían de F009.)

### `uv run pytest apps/lists -q`
```
............................                                             [100%]
28 passed in 1.45s
```

### Verificaciones adicionales
- `uv run pytest -q` (suite completa): pasa, sin regresiones.
- `uv run lint-imports`: `Contracts: 1 kept, 0 broken` (api.py no toca el ORM).
- `openapi.json`: contiene `/api/lists` (×4 plantillas) y los schemas
  `UserListOut`/`UserListItemOut`/`UserListDetailOut` + inputs.

## Deuda / seguimientos detectados
- Frontend pendiente (parte de F017, otra capa): `pnpm gen:api` + helpers tipados
  `apiPost`/`apiPatch`/`apiDelete` en `src/lib/api/client.ts` (lo hará el
  implementer-frontend tras la regeneración del contrato).
- `total == subtotal` en MVP por diseño (sin impuestos/envío). Si se añaden, será
  cambio de contrato futuro.
- PATCH de lista soporta desasignar zona (`zone_id: null` explícito) vs no tocar
  (campo ausente) usando `model_fields_set`; documentado en código por si la UI
  lo necesita.
