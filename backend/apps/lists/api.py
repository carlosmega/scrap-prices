"""Router de Ninja de las listas de cotización (F017): SOLO parseo, validación y delegación.

Ninguna llamada al ORM aquí (regla de capas, ver docs/conventions-backend.md):
el CRUD, el scoping por sesión y la captura del snapshot viven en `services.py`.
Este módulo solo:
- lee la identidad anónima del header `X-Session-Key` (400 si falta donde se
  requiere) y la pasa a los services;
- traduce las excepciones de dominio de `services` a códigos HTTP (404/422);
- declara `response=` explícito por endpoint (incluido `{204: None}` en los DELETE).
"""

from ninja import Header, Router, Status
from ninja.errors import HttpError

from apps.lists import services
from apps.lists.schemas import (
    UserListCreateIn,
    UserListDetailOut,
    UserListItemCreateIn,
    UserListItemOut,
    UserListItemPatchIn,
    UserListOut,
    UserListPatchIn,
)

router = Router(tags=["lists"])


def _require_session_key(x_session_key: str | None) -> str:
    """Devuelve la clave de sesión o lanza 400 si falta el header."""
    if not x_session_key:
        raise HttpError(400, "falta el header X-Session-Key")
    return x_session_key


@router.get("/lists", response=list[UserListOut])
def listar_listas(request, x_session_key: str | None = Header(default=None)):
    """Lista las listas de la sesión (`X-Session-Key`). 400 sin header."""
    session_key = _require_session_key(x_session_key)
    return services.listar_listas(session_key=session_key)


@router.post("/lists", response={201: UserListOut})
def crear_lista(
    request,
    data: UserListCreateIn,
    x_session_key: str | None = Header(default=None),
):
    """Crea una lista para la sesión. 400 sin header; 422 cuerpo inválido."""
    session_key = _require_session_key(x_session_key)
    lista = services.crear_lista(
        session_key=session_key, name=data.name, zone_id=data.zone_id
    )
    return Status(201, lista)


@router.get("/lists/{list_id}", response=UserListDetailOut)
def detalle_lista(
    request, list_id: str, x_session_key: str | None = Header(default=None)
):
    """Detalle de una lista de la sesión (ítems + subtotal/total). 400 sin header; 404 ajena."""
    session_key = _require_session_key(x_session_key)
    try:
        return services.detalle_lista(list_id=list_id, session_key=session_key)
    except services.ListaNoEncontrada:
        raise HttpError(404, "lista no encontrada") from None


@router.patch("/lists/{list_id}", response=UserListOut)
def actualizar_lista(
    request,
    list_id: str,
    data: UserListPatchIn,
    x_session_key: str | None = Header(default=None),
):
    """Actualiza nombre y/o zona de una lista de la sesión. 400 sin header; 404 si no es suya."""
    session_key = _require_session_key(x_session_key)
    # `zone_id` en el payload distingue "desasignar" (None explícito) de "no tocar".
    zone_id_provisto = "zone_id" in data.model_fields_set
    try:
        return services.actualizar_lista(
            list_id=list_id,
            session_key=session_key,
            name=data.name,
            zone_id=data.zone_id,
            zone_id_provisto=zone_id_provisto,
        )
    except services.ListaNoEncontrada:
        raise HttpError(404, "lista no encontrada") from None


@router.delete("/lists/{list_id}", response={204: None})
def eliminar_lista(
    request, list_id: str, x_session_key: str | None = Header(default=None)
):
    """Borra una lista de la sesión (sin body). 400 sin header; 404 si no es suya; 204 si ok."""
    session_key = _require_session_key(x_session_key)
    try:
        services.eliminar_lista(list_id=list_id, session_key=session_key)
    except services.ListaNoEncontrada:
        raise HttpError(404, "lista no encontrada") from None
    return Status(204, None)


@router.post("/lists/{list_id}/items", response={201: UserListItemOut})
def agregar_item(
    request,
    list_id: str,
    data: UserListItemCreateIn,
    x_session_key: str | None = Header(default=None),
):
    """Agrega un SKU con snapshot inmutable. 400 sin header; 404 lista/SKU; 422 sin precio."""
    session_key = _require_session_key(x_session_key)
    try:
        item = services.agregar_item(
            list_id=list_id,
            session_key=session_key,
            retailer_product_id=data.retailer_product_id,
            quantity=data.quantity,
        )
    except (services.ListaNoEncontrada, services.ProductoNoEncontrado):
        raise HttpError(404, "lista o producto no encontrados") from None
    except services.SinPrecioParaSnapshot:
        raise HttpError(422, "sin precio para snapshot") from None
    return Status(201, item)


@router.patch("/lists/{list_id}/items/{item_id}", response=UserListItemOut)
def actualizar_item(
    request,
    list_id: str,
    item_id: str,
    data: UserListItemPatchIn,
    x_session_key: str | None = Header(default=None),
):
    """Cambia la cantidad de un ítem (el snapshot no se toca). 400 sin header; 404; 422 cantidad."""
    session_key = _require_session_key(x_session_key)
    try:
        return services.actualizar_item(
            list_id=list_id,
            item_id=item_id,
            session_key=session_key,
            quantity=data.quantity,
        )
    except services.ListaNoEncontrada:
        raise HttpError(404, "ítem no encontrado") from None


@router.delete("/lists/{list_id}/items/{item_id}", response={204: None})
def eliminar_item(
    request,
    list_id: str,
    item_id: str,
    x_session_key: str | None = Header(default=None),
):
    """Quita un ítem de la lista de la sesión (sin body). 400 sin header; 404; 204 si ok."""
    session_key = _require_session_key(x_session_key)
    try:
        services.eliminar_item(
            list_id=list_id, item_id=item_id, session_key=session_key
        )
    except services.ListaNoEncontrada:
        raise HttpError(404, "ítem no encontrado") from None
    return Status(204, None)
