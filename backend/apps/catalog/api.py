"""Router de Ninja del catálogo: SOLO parseo, validación y delegación.

Ninguna llamada al ORM aquí (regla de capas, ver docs/conventions-backend.md):
la búsqueda, el ensamblado de precios, el orden y la orquestación de la
búsqueda EN VIVO (F033: gatillo, adapters, ingestión) viven en services.
"""

from typing import Literal

from ninja import Query, Router
from ninja.errors import HttpError

from apps.catalog import services
from apps.catalog.schemas import ProductDetailOut, SearchOut

router = Router(tags=["catalog"])


@router.get("/search", response=SearchOut)
def buscar(
    request,
    q: str = Query(...),
    zone_id: str = Query(...),
    sort: str = Query("price"),
    live: Literal["auto", "never"] = Query("auto"),
):
    """Busca `q` en la zona: canónicos comparados + crudos por tienda (F033).

    BREAKING F033: la respuesta pasa de lista a objeto (`SearchOut`). Con
    `live=auto` (default), si no hay datos frescos para `q`+zona el service
    consulta ambos retailers EN VIVO (puede tardar hasta ~25 s), ingesta y
    responde; `live=never` desactiva el vivo. 404 si `zone_id` no existe o
    está inactiva (el service devuelve None).
    """
    resultado = services.buscar(q=q, zone_id=zone_id, sort=sort, live=live)
    if resultado is None:
        raise HttpError(404, "zona no encontrada")
    return resultado


@router.get("/products/{id}", response=ProductDetailOut)
def detalle_producto(request, id: str, zone_id: str = Query(...)):
    """Detalle de un canónico en la zona: producto, precios actuales e historial.

    404 si el producto no existe/inactivo o si `zone_id` no existe/inactiva
    (el service devuelve None).
    """
    detalle = services.detalle_producto(product_id=id, zone_id=zone_id)
    if detalle is None:
        raise HttpError(404, "producto o zona no encontrados")
    return detalle
