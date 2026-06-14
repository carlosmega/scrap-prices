"""Schemas de entrada/salida del catálogo (F015). El contrato vive aquí.

La frontera de la búsqueda: por cada `CanonicalProduct` que matchea `q`,
`SearchResultOut` lleva el producto canónico y una lista de precios por retailer
(`PriceByRetailerOut`) con el precio más fresco en la zona. Las shapes son las
exactas de la spec F015; el router no inventa dicts.
"""

from datetime import datetime
from decimal import Decimal

from ninja import Schema


class RetailerRefOut(Schema):
    """Referencia mínima a un retailer dentro de un precio."""

    slug: str
    name: str


class PriceByRetailerOut(Schema):
    """Precio más fresco de un retailer para un canónico en una zona.

    `price`/`captured_at` son None cuando el retailer no tiene observación en la
    zona (entonces `is_available=False`). `price` se serializa como string del
    Decimal para no perder exactitud monetaria (PRD §8).
    """

    retailer: RetailerRefOut
    retailer_product_id: str
    price: Decimal | None = None
    currency: str = "MXN"
    is_available: bool = False
    captured_at: datetime | None = None
    url: str


class CanonicalProductRefOut(Schema):
    """Subconjunto público del producto canónico para el resultado de búsqueda."""

    id: str
    name: str
    category: str
    unit: str


class SearchResultOut(Schema):
    """Un producto canónico matcheado con sus precios por retailer en la zona."""

    canonical_product: CanonicalProductRefOut
    prices: list[PriceByRetailerOut]
