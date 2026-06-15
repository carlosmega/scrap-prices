"""Adapter FALSO para tests offline (sin red real).

Implementa `BaseRetailerAdapter` devolviendo datos en memoria. Sirve para
verificar que la interfaz del PRD §9.3 es implementable y que los dataclasses
normalizados tienen la forma esperada, sin tocar ningún retailer real.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from apps.scraping.base import BaseRetailerAdapter, RawPrice, RawProduct


class FakeRetailerAdapter(BaseRetailerAdapter):
    """Adapter en memoria: ni httpx ni red. Solo para tests."""

    source = "xhr"

    def __init__(self) -> None:
        self.zone_set_to: object | None = None

    def set_zone(self, location: object) -> None:
        self.zone_set_to = location

    def list_products(self, category: str, location: object) -> list[RawProduct]:
        return [
            RawProduct(
                sku="FAKE-001",
                raw_name=f"Varilla {category} 3/8",
                source=self.source,
                raw_payload={"category": category},
            )
        ]

    def get_price(self, product: RawProduct, location: object) -> RawPrice:
        return RawPrice(
            sku=product.sku,
            raw_name=product.raw_name,
            price=Decimal("199.99"),
            currency="MXN",
            is_available=True,
            source=self.source,
            captured_at=datetime(2026, 6, 14, 10, 0, tzinfo=UTC),
            raw_payload={"price_raw": "199.99"},
        )
