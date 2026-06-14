"""Lógica de negocio de listas de cotización (F009 + F017). Sin HTTP, sin routers.

Aquí vive TODO: cálculo de subtotal (F009), CRUD de listas/ítems scope-ado por
`session_key`, y la captura del **snapshot inmutable** de precio al agregar un
ítem (CA2 de C1). El router (`api.py`) solo parsea, delega y traduce las
excepciones de dominio a códigos HTTP — nunca toca el ORM.

Reglas de dominio (de la spec F017):
- Scoping estricto por `session_key`: una sesión NO accede a listas/ítems de otra.
  Si la `{id}`/`{item_id}` no pertenece a la sesión → `ListaNoEncontrada` (404).
- Snapshot al agregar: se copia `captured_price`/`captured_at` de la ÚLTIMA
  `PriceObservation` del `retailer_product` en la zona de la lista (si la lista no
  tiene zona, la última observación disponible del producto). Si no hay ninguna →
  `SinPrecioParaSnapshot` (422). El snapshot NO cambia después.
- `quantity >= 1` lo garantiza el schema (422); aquí no se revalida.

Estas excepciones de dominio existen para no acoplar los services a HTTP: el
router las mapea a 404/422.
"""

from decimal import Decimal

from apps.catalog.models import RetailerProduct
from apps.catalog.schemas import RetailerRefOut
from apps.lists.models import UserList, UserListItem
from apps.lists.schemas import (
    UserListDetailOut,
    UserListItemOut,
    UserListOut,
)
from apps.prices.services import ultima_observacion


class ListaNoEncontrada(Exception):
    """La lista (o el ítem) no existe o no pertenece a la sesión → 404."""


class ProductoNoEncontrado(Exception):
    """El `retailer_product_id` no existe o está inactivo → 404."""


class SinPrecioParaSnapshot(Exception):
    """No hay `PriceObservation` para capturar el snapshot del ítem → 422."""


# --- Cálculo de totales (F009) ---------------------------------------------


def subtotal_lista(user_list: UserList) -> Decimal:
    """Suma `quantity * captured_price` de todos los ítems de la lista.

    Usa el `captured_price` (snapshot) de cada ítem, nunca el precio en vivo del
    catálogo. Devuelve Decimal("0.00") si la lista no tiene ítems.
    """
    total = Decimal("0.00")
    for item in user_list.items.all():
        total += item.captured_price * item.quantity
    return total


# --- Serialización a schemas -----------------------------------------------


def _serializar_lista(user_list: UserList) -> UserListOut:
    """Arma el `UserListOut` (resumen) de una lista."""
    return UserListOut(
        id=str(user_list.id),
        name=user_list.name,
        zone_id=(str(user_list.zone_id) if user_list.zone_id else None),
        created_at=user_list.created_at,
        item_count=user_list.items.count(),
    )


def _serializar_item(item: UserListItem) -> UserListItemOut:
    """Arma el `UserListItemOut` de un ítem, con su snapshot y `line_total`."""
    retailer = item.retailer_product.retailer
    return UserListItemOut(
        id=str(item.id),
        retailer_product_id=str(item.retailer_product_id),
        retailer=RetailerRefOut(slug=retailer.slug, name=retailer.name),
        product_name=item.retailer_product.raw_name,
        quantity=item.quantity,
        captured_price=item.captured_price,
        captured_at=item.captured_at,
        line_total=item.captured_price * item.quantity,
    )


def _serializar_detalle(user_list: UserList) -> UserListDetailOut:
    """Arma el `UserListDetailOut`: resumen + ítems + subtotal/total."""
    items = list(
        user_list.items.select_related("retailer_product__retailer").all()
    )
    subtotal = subtotal_lista(user_list)
    return UserListDetailOut(
        id=str(user_list.id),
        name=user_list.name,
        zone_id=(str(user_list.zone_id) if user_list.zone_id else None),
        created_at=user_list.created_at,
        item_count=len(items),
        items=[_serializar_item(i) for i in items],
        subtotal=subtotal,
        total=subtotal,  # MVP: sin impuestos ni envío, total == subtotal.
    )


# --- Helpers de scoping (privados): nunca filtran datos de otra sesión ------


def _lista_de_sesion(list_id: str, session_key: str) -> UserList:
    """Devuelve la lista `list_id` SOLO si pertenece a `session_key`.

    Cualquier otro caso (no existe, inactiva, o de otra sesión) → 404 vía
    `ListaNoEncontrada`. No se distingue "ajena" de "inexistente" para no filtrar
    información de otras sesiones.
    """
    lista = UserList.objects.filter(
        id=list_id, session_key=session_key, is_active=True
    ).first()
    if lista is None:
        raise ListaNoEncontrada()
    return lista


def _item_de_sesion(
    list_id: str, item_id: str, session_key: str
) -> UserListItem:
    """Devuelve el ítem `item_id` de la lista `list_id` SOLO si es de la sesión.

    Valida el scoping de la lista (vía `_lista_de_sesion`) y que el ítem cuelgue
    de ella. Cualquier desajuste → `ListaNoEncontrada` (404).
    """
    lista = _lista_de_sesion(list_id, session_key)
    item = lista.items.filter(id=item_id).first()
    if item is None:
        raise ListaNoEncontrada()
    return item


# --- CRUD de listas ---------------------------------------------------------


def listar_listas(session_key: str) -> list[UserListOut]:
    """Lista las listas activas de la sesión, orden `-created_at` (default del modelo)."""
    listas = UserList.objects.filter(session_key=session_key, is_active=True)
    return [_serializar_lista(lista) for lista in listas]


def crear_lista(
    session_key: str, name: str, zone_id: str | None = None
) -> UserListOut:
    """Crea una lista para la sesión. `zone_id` opcional."""
    lista = UserList.objects.create(
        session_key=session_key,
        name=name,
        zone_id=zone_id,
    )
    return _serializar_lista(lista)


def detalle_lista(list_id: str, session_key: str) -> UserListDetailOut:
    """Detalle de una lista de la sesión: ítems + subtotal/total. 404 si no es suya."""
    lista = _lista_de_sesion(list_id, session_key)
    return _serializar_detalle(lista)


def actualizar_lista(
    list_id: str,
    session_key: str,
    name: str | None = None,
    zone_id: str | None = None,
    zone_id_provisto: bool = False,
) -> UserListOut:
    """Actualiza nombre y/o zona de una lista de la sesión (parcial). 404 si no es suya.

    `zone_id_provisto` distingue "no tocar la zona" (campo ausente) de "desasignar"
    (`zone_id=None` explícito en el cuerpo).
    """
    lista = _lista_de_sesion(list_id, session_key)
    campos: list[str] = []
    if name is not None:
        lista.name = name
        campos.append("name")
    if zone_id_provisto:
        lista.zone_id = zone_id
        campos.append("zone")
    if campos:
        lista.save(update_fields=campos)
    return _serializar_lista(lista)


def eliminar_lista(list_id: str, session_key: str) -> None:
    """Borra una lista de la sesión (y sus ítems en cascada). 404 si no es suya."""
    lista = _lista_de_sesion(list_id, session_key)
    lista.delete()


# --- CRUD de ítems ----------------------------------------------------------


def agregar_item(
    list_id: str,
    session_key: str,
    retailer_product_id: str,
    quantity: int,
) -> UserListItemOut:
    """Agrega un SKU a la lista con snapshot inmutable de precio (CA2 de C1).

    Copia `captured_price`/`captured_at` de la ÚLTIMA `PriceObservation` del
    `retailer_product` en la zona de la lista (si la lista no tiene zona, la
    última observación disponible del producto). Si no hay observación →
    `SinPrecioParaSnapshot` (422). 404 si la lista no es de la sesión o el SKU no
    existe/está inactivo.
    """
    lista = _lista_de_sesion(list_id, session_key)

    retailer_product = RetailerProduct.objects.filter(
        id=retailer_product_id, is_active=True
    ).first()
    if retailer_product is None:
        raise ProductoNoEncontrado()

    observacion = ultima_observacion(retailer_product, zone=lista.zone)
    if observacion is None:
        raise SinPrecioParaSnapshot()

    item = UserListItem.objects.create(
        user_list=lista,
        retailer_product=retailer_product,
        quantity=quantity,
        captured_price=observacion.price,
        captured_at=observacion.captured_at,
    )
    return _serializar_item(item)


def actualizar_item(
    list_id: str,
    item_id: str,
    session_key: str,
    quantity: int,
) -> UserListItemOut:
    """Cambia la cantidad de un ítem de la sesión. El snapshot NO se toca. 404 si no es suyo."""
    item = _item_de_sesion(list_id, item_id, session_key)
    item.quantity = quantity
    item.save(update_fields=["quantity"])
    return _serializar_item(item)


def eliminar_item(list_id: str, item_id: str, session_key: str) -> None:
    """Quita un ítem de la lista de la sesión. 404 si no es suyo."""
    item = _item_de_sesion(list_id, item_id, session_key)
    item.delete()
