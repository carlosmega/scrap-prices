"""Schemas de entrada/salida del catálogo (F015/F033). El contrato vive aquí.

La frontera de la búsqueda: por cada `CanonicalProduct` que matchea `q`,
`SearchResultOut` lleva el producto canónico y una lista de precios por retailer
(`PriceByRetailerOut`) con el precio más fresco en la zona. Las shapes son las
exactas de la spec F015; el router no inventa dicts.

F033 (BREAKING): `/api/search` deja de responder una lista y responde
`SearchOut`: los canónicos comparados (`results`, igual que antes), los
hallazgos crudos por tienda aún sin matchear (`raw_results`) y la info de la
corrida en vivo (`live`, null si no se disparó).
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

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

    F031: `price` es el valor NATIVO del retailer (transparencia: "listado a
    $X/ton"); `sale_unit` es su unidad estructurada (`""` = desconocida). La
    comparación cross-retailer usa los campos NORMALIZADOS `price_per_piece`
    (titular de obra) y `price_per_kg` (base de orden/menor-precio). Cualquiera
    de los dos es None cuando no se puede normalizar (falta `mass_kg`, unidad
    desconocida o sin precio en la zona). También como string Decimal.
    """

    retailer: RetailerRefOut
    retailer_product_id: str
    price: Decimal | None = None
    currency: str = "MXN"
    is_available: bool = False
    captured_at: datetime | None = None
    url: str
    sale_unit: str = ""
    price_per_piece: Decimal | None = None
    price_per_kg: Decimal | None = None


class CanonicalProductRefOut(Schema):
    """Subconjunto público del producto canónico para el resultado de búsqueda.

    F031: `mass_kg` (peso de una pieza canónica) es el factor de conversión que
    permite a la UI explicar la normalización; None si el canónico no es
    normalizable. String Decimal por exactitud.
    """

    id: str
    name: str
    category: str
    unit: str
    mass_kg: Decimal | None = None


class SearchResultOut(Schema):
    """Un producto canónico matcheado con sus precios por retailer en la zona."""

    canonical_product: CanonicalProductRefOut
    prices: list[PriceByRetailerOut]


class RawRetailerResultOut(Schema):
    """Un hallazgo CRUDO de una tienda, aún sin matchear a un canónico (F033).

    Es un `RetailerProduct` sin `canonical_product` cuyo `raw_name` matchea `q`
    (acento-insensible), con su observación más fresca en la zona. El precio es
    NATIVO en la unidad del retailer (`sale_unit`, None = desconocida): NO es
    comparable cross-retailer hasta curarse en Admin (matching manual, PRD D1).
    `price` va como float por contrato F033 (dato informativo, no monetario
    exacto como los Decimal de `PriceByRetailerOut`).
    """

    retailer_slug: str
    retailer_name: str
    retailer_product_id: UUID
    external_sku: str
    raw_name: str
    url: str | None = None
    brand: str | None = None
    sale_unit: str | None = None
    price: float
    currency: str = "MXN"
    is_available: bool
    captured_at: datetime


class LiveRetailerStatusOut(Schema):
    """Cómo le fue a UN retailer en la corrida en vivo (F033).

    `detail` es un motivo breve legible (jamás un stacktrace): por qué se
    bloqueó, falló u omitió. `ok` con `items_found=0` significa "consultado
    con éxito pero sin hallazgos".
    """

    retailer_slug: str
    status: Literal["ok", "failed", "blocked", "skipped"]
    items_found: int = 0
    detail: str | None = None


class LiveSearchInfoOut(Schema):
    """Info de la corrida en vivo que acompañó a la búsqueda (F033)."""

    triggered: bool
    duration_ms: int
    retailers: list[LiveRetailerStatusOut]


class SearchOut(Schema):
    """Respuesta completa de `/api/search` (F033, BREAKING: lista → objeto).

    - `results`: canónicos comparados (idéntico al contrato F015/F031).
    - `raw_results`: hallazgos por tienda sin matchear (orden retailer →
      precio asc, tope 50).
    - `live`: info de la corrida en vivo; null si NO se disparó (datos frescos,
      `live=never`, `q` corto o cooldown).
    """

    results: list[SearchResultOut]
    raw_results: list[RawRetailerResultOut]
    live: LiveSearchInfoOut | None = None


class CanonicalProductDetailOut(Schema):
    """Producto canónico expandido para el detalle (incluye `specs` libres).

    F031: incluye `mass_kg` (factor de conversión para la normalización; None si
    no es normalizable). String Decimal por exactitud.
    """

    id: str
    name: str
    category: str
    unit: str
    mass_kg: Decimal | None = None
    specs: dict


class PriceHistoryPointOut(Schema):
    """Una lectura histórica de precio (una `PriceObservation`) con su retailer.

    `price` se serializa como string del Decimal por exactitud monetaria
    (PRD §8). El historial combina todos los retailers en la zona, ordenado por
    `-captured_at` (la UI de F021 puede agrupar por retailer).

    F031: cada punto gana `sale_unit` para ETIQUETAR su unidad nativa (`""` =
    desconocida). El historial NO se normaliza (fuera de alcance): `price` sigue
    siendo el valor nativo.
    """

    retailer: RetailerRefOut
    price: Decimal
    currency: str = "MXN"
    is_available: bool
    captured_at: datetime
    sale_unit: str = ""


class ProductDetailOut(Schema):
    """Detalle de un canónico: producto, precios actuales por retailer e historial.

    `prices` reutiliza el ensamblado "precio más fresco por retailer/zona" de
    F015; `history` son las últimas N observaciones en la zona (orden
    `-captured_at`).
    """

    canonical_product: CanonicalProductDetailOut
    prices: list[PriceByRetailerOut]
    history: list[PriceHistoryPointOut]
