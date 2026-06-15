"""Tests de la interfaz de adapters y los dataclasses normalizados (F024).

Offline puro: no toca red ni DB. Verifica que `BaseRetailerAdapter` es una ABC
real (no instanciable sin implementar la interfaz §9.3) y que `RawProduct` /
`RawPrice` exponen los campos del contrato con `price` como Decimal.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.scraping.base import BaseRetailerAdapter, RawPrice, RawProduct
from apps.scraping.tests.fakes import FakeRetailerAdapter


def test_base_adapter_no_es_instanciable_directamente():
    """`BaseRetailerAdapter` es ABC: no se puede instanciar sin implementar §9.3."""
    with pytest.raises(TypeError):
        BaseRetailerAdapter()  # type: ignore[abstract]


def test_fake_adapter_implementa_interfaz_9_3():
    """Un adapter concreto implementa list_products/get_price/set_zone."""
    adapter = FakeRetailerAdapter()
    adapter.set_zone("loc-123")
    assert adapter.zone_set_to == "loc-123"

    productos = adapter.list_products("varilla", "loc-123")
    assert len(productos) == 1
    assert isinstance(productos[0], RawProduct)
    assert productos[0].sku == "FAKE-001"

    precio = adapter.get_price(productos[0], "loc-123")
    assert isinstance(precio, RawPrice)
    assert precio.sku == "FAKE-001"


def test_rawprice_price_es_decimal_exacto():
    """RawPrice.price es Decimal (nunca float): exactitud monetaria (PRD §8)."""
    precio = RawPrice(
        sku="X",
        raw_name="n",
        price=Decimal("12.34"),
        currency="MXN",
        is_available=True,
        source="xhr",
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )
    assert isinstance(precio.price, Decimal)
    assert precio.price == Decimal("12.34")


def test_rawproduct_raw_payload_default_es_dict_independiente():
    """raw_payload tiene default dict y no se comparte entre instancias."""
    a = RawProduct(sku="A", raw_name="a", source="xhr")
    b = RawProduct(sku="B", raw_name="b", source="xhr")
    assert a.raw_payload == {}
    assert a.raw_payload is not b.raw_payload
