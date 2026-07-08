"""Interfaz común de adapters de retailer (PRD §9.3) y tipos normalizados.

Cada retailer (Home Depot en F025, Construrama en F026) implementa
`BaseRetailerAdapter`. La capa de ingestión consume *solo* esta interfaz y los
dataclasses normalizados (`RawProduct` / `RawPrice`), nunca el HTML/JSON crudo
de cada sitio: así el parser concreto de cada retailer queda aislado y testeable
con golden fixtures (docs/testing-strategy.md).

`RawPrice.source` indica de dónde salió el dato (`xhr`/`html`/`playwright`) y se
mapea 1:1 a `PriceObservation.Source` de F008.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from apps.geo.models import RetailerLocation, Zone


@dataclass(frozen=True, slots=True)
class RawProduct:
    """Producto tal como lo expone un retailer, antes de normalizar al catálogo.

    `sku` y `raw_name` son los identificadores del retailer (no del catálogo
    interno); la normalización a `RetailerProduct`/`Product` ocurre aguas abajo.
    `raw_payload` conserva el objeto crudo para auditabilidad (guardrail §2.3).
    `url` es el href RELATIVO de la ficha (PDP) tal como lo expone el retailer
    (F034: HD lo trae en `seo.href`); "" si el payload no lo incluye. La URL
    absoluta la reconstruye la ingestión anteponiendo el host del retailer.
    """

    sku: str
    raw_name: str
    source: str
    raw_payload: dict = field(default_factory=dict)
    url: str = ""


@dataclass(frozen=True, slots=True)
class RawPrice:
    """Lectura de precio normalizada de un SKU en una zona/ubicación.

    `price` es `Decimal` (nunca float) por exactitud monetaria (PRD §8).
    `captured_at` es el momento de la lectura que fija el adapter. Estos campos
    se mapean directamente a `PriceObservation` al ingerir.
    """

    sku: str
    raw_name: str
    price: Decimal
    currency: str
    is_available: bool
    source: str
    captured_at: datetime
    raw_payload: dict = field(default_factory=dict)


class BaseRetailerAdapter(ABC):
    """Contrato que implementa cada adapter de retailer (PRD §9.3).

    Los adapters concretos NO heredan ninguna técnica de evasión: la base solo
    define la forma de la interfaz. La cortesía (rate-limit), los reintentos y
    el `stop-if-blocked` viven en el cliente HTTP (`PoliteClient`) que cada
    adapter usa por composición.
    """

    #: De qué tipo de captura provienen los datos del adapter
    #: (`xhr`/`html`/`playwright`). Cada adapter concreto lo fija.
    source: str

    @abstractmethod
    def set_zone(self, location: RetailerLocation | Zone) -> None:
        """Posiciona el adapter en una zona/ubicación antes de consultar.

        HD lo hace por cookie de tienda; Construrama por subpath de distribuidor.
        El adapter traduce la `location`/`zone` interna a lo que su sitio espera.
        """
        raise NotImplementedError

    @abstractmethod
    def list_products(self, category: str, location: RetailerLocation | Zone) -> list[RawProduct]:
        """Lista los productos de una categoría para una ubicación."""
        raise NotImplementedError

    @abstractmethod
    def get_price(self, product: RawProduct, location: RetailerLocation | Zone) -> RawPrice:
        """Obtiene el precio de un producto en una ubicación."""
        raise NotImplementedError
