"""Router de Ninja del catálogo: SOLO parseo, validación y delegación.

Ninguna llamada al ORM aquí (regla de capas, ver docs/conventions-backend.md):
la búsqueda, el ensamblado de precios y el orden viven en services.py.
"""

from ninja import Query, Router
from ninja.errors import HttpError

from apps.catalog import services
from apps.catalog.schemas import ProductDetailOut, SearchResultOut

router = Router(tags=["catalog"])


@router.get("/search", response=list[SearchResultOut])
def buscar(
    request,
    q: str = Query(...),
    zone_id: str = Query(...),
    sort: str = Query("price"),
):
    """Busca canónicos por `q` con su precio más fresco por retailer en la zona.

    404 si `zone_id` no existe o está inactiva (el service devuelve None).
    """
    resultados = services.buscar(q=q, zone_id=zone_id, sort=sort)
    if resultados is None:
        raise HttpError(404, "zona no encontrada")
    return resultados


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
