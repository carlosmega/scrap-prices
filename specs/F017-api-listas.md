# F017 — API de listas de cotización (Django Ninja)

> Milestone M3. PRD §12 (`/api/lists`, `/api/lists/{id}`, `/api/lists/{id}/items`),
> Épica C (lista de cotización con snapshots y totales). MVP **anónimo/sesión**.

## Contexto y objetivo
El usuario arma su cotización: crea listas, agrega productos con cantidad, y al
agregar se guarda un **snapshot inmutable** del precio (Épica C1·CA2). Sin login:
la lista se asocia a una clave de sesión que el cliente provee.

## Identidad anónima (decisión MVP)
El cliente genera y persiste una clave (UUID) y la envía en el header
**`X-Session-Key`** en cada request. La API scope-a las listas a esa clave
(mapea a `UserList.session_key`, de F009). Acceder a una lista de otra sesión → 404.
Si falta el header en endpoints que lo requieren → 400. (Sin cookies de Django ni
CORS-credentials, para simplicidad del MVP.)

## Contrato API
| Método | Ruta | Request | Response | Errores |
| ------ | ---- | ------- | -------- | ------- |
| GET | /api/lists | header `X-Session-Key` | `UserListOut[]` | 400 sin header |
| POST | /api/lists | `{name, zone_id?}` | `UserListOut` (201) | 400, 422 |
| GET | /api/lists/{id} | — | `UserListDetailOut` (items + subtotal/total) | 404 |
| PATCH | /api/lists/{id} | `{name?, zone_id?}` | `UserListOut` | 404, 422 |
| DELETE | /api/lists/{id} | — | 204 | 404 |
| POST | /api/lists/{id}/items | `{retailer_product_id, quantity}` | `UserListItemOut` (201) | 404, 422 |
| PATCH | /api/lists/{id}/items/{item_id} | `{quantity}` | `UserListItemOut` | 404, 422 |
| DELETE | /api/lists/{id}/items/{item_id} | — | 204 | 404 |

```
UserListOut = {"id": str, "name": str, "zone_id": str|null, "created_at": datetime, "item_count": int}
UserListItemOut = {
  "id": str, "retailer_product_id": str, "retailer": {"slug","name"},
  "product_name": str, "quantity": int,
  "captured_price": str(Decimal), "captured_at": datetime,   # snapshot inmutable
  "line_total": str(Decimal)   # quantity * captured_price
}
UserListDetailOut = UserListOut + {"items": UserListItemOut[], "subtotal": str(Decimal), "total": str(Decimal)}
```

- **Snapshot al agregar** (C1·CA2): al POST item, copia `captured_price`/`captured_at`
  de la **última `PriceObservation`** del `retailer_product` en la zona de la lista
  (si la lista no tiene zona, usar la última observación disponible del producto;
  si no hay observación, 422 "sin precio para snapshot"). El snapshot NO cambia después.
- Subtotal/total reutilizan `apps/lists/services.subtotal_lista` (F009).
- Todo scoping por `X-Session-Key`; `{id}`/`{item_id}` que no pertenezcan a la
  sesión → 404 (no se filtra info de otras sesiones).

## Alcance
**Incluye:** endpoints en `apps/lists/api.py`, schemas en `schemas.py`, lógica
(crear/editar/snapshot/totales/scoping) en `services.py`. Regenera `openapi.json`.
Frontend: `pnpm gen:api` + **extender `src/lib/api/client.ts`** con helpers tipados
`apiPost`/`apiPatch`/`apiDelete` (el `fetch` sigue SOLO en client.ts) — los usará M4.
**No incluye:** UI (es F022); export CSV/Excel (backlog C2); login.

## Criterios de aceptación
- [ ] **Backend:** flujo completo con `X-Session-Key`: crear lista, agregar 2 items
      (snapshot capturado), editar cantidad, quitar item, ver detalle con subtotal/total
      correctos; borrar lista. Tests cubren cada endpoint.
- [ ] **Backend:** el snapshot es **inmutable**: si cambia el precio (nueva
      PriceObservation) tras agregar, `captured_price` del item NO cambia (test).
- [ ] **Backend:** scoping por sesión: una sesión NO ve ni modifica listas de otra
      (404). Falta de `X-Session-Key` donde se requiere → 400.
- [ ] **Backend:** router sin ORM, lógica en services, `response=` explícito; 404/422 correctos.
- [ ] **Backend:** `openapi.json` regenerado. **Contrato:** `pnpm gen:api`, Fase 5 sin drift.
- [ ] **Frontend:** `client.ts` expone `apiPost/apiPatch/apiDelete` tipados; `fetch`
      solo en client.ts; cero `any`; tsc/lint/build/test:unit limpios.
- [ ] `./init.sh` verde.

## Plan de verificación
```bash
cd backend && uv run python manage.py seed && uv run pytest apps/lists -q
uv run python manage.py export_openapi_schema --api config.api.api --indent 2 --output openapi.json
cd ../frontend && pnpm gen:api && cd .. && ./init.sh
```

## Notas y decisiones abiertas
- Cuando se añada login (fase posterior), `UserList.user` (FK nullable) coexiste con
  `session_key`; este contrato no cambia.
- `quantity` PositiveInteger ≥ 1 (422 si 0/negativo).
