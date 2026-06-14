"""Lógica de negocio del catálogo (F015): búsqueda y ensamblado de precios.

Sin HTTP, sin routers. La búsqueda consulta SOLO la DB propia (principio no
negociable del PRD §1/B1): por cada `CanonicalProduct` que matchea `q`, ensambla
un `PriceByRetailerOut` por cada `RetailerProduct` enlazado, con el precio más
fresco en la zona (reutiliza `apps.prices.services.ultima_observacion`). Tolera
acentos en SQLite normalizando (NFKD + strip de diacríticos) en memoria; Postgres
FTS llega en M5. El orden (`price`|`name`) también vive aquí.
"""

import unicodedata

from apps.catalog.models import CanonicalProduct
from apps.catalog.schemas import (
    CanonicalProductDetailOut,
    CanonicalProductRefOut,
    PriceByRetailerOut,
    PriceHistoryPointOut,
    ProductDetailOut,
    RetailerRefOut,
    SearchResultOut,
)
from apps.geo.models import Zone
from apps.prices.models import PriceObservation
from apps.prices.services import ultima_observacion

# Tamaño por defecto del historial de precios en el detalle (PRD/F016: N=20).
_HISTORIAL_DEFAULT = 20

# Ordena los retailers-sin-precio al final cuando se ordena por precio.
_PRECIO_INFINITO = None  # marcador semántico; se traduce a +inf en la key


def _normalizar(texto: str) -> str:
    """Minúsculas sin diacríticos (NFKD) para comparar tolerando acentos.

    'Varilla' y 'várilla' colapsan al mismo token; suficiente para el MVP en
    SQLite (Postgres adoptará unaccent/SearchVector en M5).
    """
    descompuesto = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(ch for ch in descompuesto if not unicodedata.combining(ch))


def _ensamblar_precio(retailer_product, zone: Zone) -> PriceByRetailerOut:
    """Arma el PriceByRetailerOut de un RetailerProduct con su precio más fresco.

    Sin observación en la zona → price/captured_at None, is_available False.
    """
    obs = ultima_observacion(retailer_product, zone=zone)
    retailer = retailer_product.retailer
    return PriceByRetailerOut(
        retailer=RetailerRefOut(slug=retailer.slug, name=retailer.name),
        retailer_product_id=str(retailer_product.id),
        price=(obs.price if obs is not None else None),
        currency=(obs.currency if obs is not None else "MXN"),
        is_available=(obs.is_available if obs is not None else False),
        captured_at=(obs.captured_at if obs is not None else None),
        url=retailer_product.url,
    )


def _menor_precio_disponible(prices: list[PriceByRetailerOut]):
    """Menor precio entre los retailers disponibles; None si ninguno tiene precio."""
    disponibles = [p.price for p in prices if p.price is not None and p.is_available]
    return min(disponibles) if disponibles else None


def buscar(
    q: str,
    zone_id: str,
    sort: str = "price",
) -> list[SearchResultOut] | None:
    """Busca canónicos que matchean `q` y ensambla sus precios en la zona.

    Devuelve None si la zona no existe o está inactiva (el router lo traduce a
    404). En caso contrario, devuelve la lista de `SearchResultOut` ordenada por
    `sort` (`price`: menor precio disponible primero; `name`: alfabético).
    """
    zona = Zone.objects.filter(id=zone_id, is_active=True).first()
    if zona is None:
        return None

    termino = _normalizar(q.strip())

    resultados: list[tuple[SearchResultOut, object, str]] = []
    canonicos = (
        CanonicalProduct.objects.filter(is_active=True)
        .select_related("category")
        .order_by("name")
    )
    for canonico in canonicos:
        if termino and termino not in _normalizar(canonico.name):
            continue

        retailer_products = (
            canonico.retailer_products.filter(is_active=True)
            .select_related("retailer")
            .order_by("retailer__name")
        )
        prices = [_ensamblar_precio(rp, zona) for rp in retailer_products]

        item = SearchResultOut(
            canonical_product=CanonicalProductRefOut(
                id=str(canonico.id),
                name=canonico.name,
                category=canonico.category.name,
                unit=canonico.unit,
            ),
            prices=prices,
        )
        resultados.append((item, _menor_precio_disponible(prices), canonico.name))

    if sort == "name":
        resultados.sort(key=lambda r: _normalizar(r[2]))
    else:  # sort == "price": menor precio disponible primero; sin precio al final.
        resultados.sort(
            key=lambda r: (r[1] is None, r[1] if r[1] is not None else 0, _normalizar(r[2]))
        )

    return [item for item, _, _ in resultados]


def _historial(canonico: CanonicalProduct, zona: Zone, n: int) -> list[PriceHistoryPointOut]:
    """Últimas `n` observaciones del canónico en la zona, orden `-captured_at`.

    Combina todos los `RetailerProduct` activos enlazados al canónico; cada punto
    lleva su retailer. La consulta se apoya en el índice (retailer_product, zone,
    -captured_at) y el orden por `-captured_at` del modelo.
    """
    observaciones = (
        PriceObservation.objects.filter(
            retailer_product__canonical_product=canonico,
            retailer_product__is_active=True,
            zone=zona,
        )
        .select_related("retailer_product__retailer")
        .order_by("-captured_at")[:n]
    )
    return [
        PriceHistoryPointOut(
            retailer=RetailerRefOut(
                slug=obs.retailer_product.retailer.slug,
                name=obs.retailer_product.retailer.name,
            ),
            price=obs.price,
            currency=obs.currency,
            is_available=obs.is_available,
            captured_at=obs.captured_at,
        )
        for obs in observaciones
    ]


def detalle_producto(
    product_id: str,
    zone_id: str,
    historial_n: int = _HISTORIAL_DEFAULT,
) -> ProductDetailOut | None:
    """Detalle de un canónico en una zona: producto, precios actuales e historial.

    Devuelve None si el canónico no existe/inactivo o si la zona no existe/inactiva
    (el router lo traduce a 404). `prices` reutiliza el ensamblado "precio más
    fresco por retailer/zona" de F015; `history` son las últimas `historial_n`
    observaciones en la zona, orden `-captured_at`.
    """
    zona = Zone.objects.filter(id=zone_id, is_active=True).first()
    if zona is None:
        return None

    canonico = (
        CanonicalProduct.objects.filter(id=product_id, is_active=True)
        .select_related("category")
        .first()
    )
    if canonico is None:
        return None

    retailer_products = (
        canonico.retailer_products.filter(is_active=True)
        .select_related("retailer")
        .order_by("retailer__name")
    )
    prices = [_ensamblar_precio(rp, zona) for rp in retailer_products]

    return ProductDetailOut(
        canonical_product=CanonicalProductDetailOut(
            id=str(canonico.id),
            name=canonico.name,
            category=canonico.category.name,
            unit=canonico.unit,
            specs=canonico.specs,
        ),
        prices=prices,
        history=_historial(canonico, zona, historial_n),
    )
