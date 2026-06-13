"""Lógica de negocio de precios (F008). Sin HTTP, sin routers.

La regla "precio más fresco por producto y zona" vive aquí (no en api.py): es
lógica de dominio y se apoya en el índice compuesto de `PriceObservation`. En
M3 los endpoints de historial/precio delegarán en estos helpers.
"""

from apps.catalog.models import RetailerProduct
from apps.geo.models import Zone
from apps.prices.models import PriceObservation


def ultima_observacion(
    retailer_product: RetailerProduct,
    zone: Zone | None = None,
) -> PriceObservation | None:
    """Devuelve la `PriceObservation` más reciente de un producto en una zona.

    "Más reciente" se mide por `captured_at` (el momento de la lectura que fija
    el scraper), no por `created_at`. Si `zone` es None, filtra observaciones
    sin zona asignada. Devuelve None si no hay observaciones.
    """
    return (
        PriceObservation.objects.filter(retailer_product=retailer_product, zone=zone)
        .order_by("-captured_at")
        .first()
    )
