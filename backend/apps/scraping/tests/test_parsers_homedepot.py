"""Tests del parser puro de Home Depot (F025) contra golden fixtures.

100% OFFLINE: el parser es una función pura; estos tests cargan respuestas
REALES sanitizadas extraídas del HAR (`fixtures/homedepot_*.json`) y verifican
precio Decimal, sku, disponibilidad y unidad. Ningún test pega a una URL real.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from apps.scraping.parsers import (
    HOMEDEPOT_SOURCE,
    homedepot_unit,
    parse_homedepot,
    parse_homedepot_prices,
)

FIXTURES = Path(__file__).parent / "fixtures"
# physicalStoreId interno de la tienda piloto Monterrey (recon §3: 1333 ↔ 18503).
STORE_ID = "18503"
CAPTURED_AT = datetime(2026, 6, 14, 12, 0, tzinfo=UTC)


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_parse_varilla_precio_decimal_sku_unidad():
    """Una varilla real: sku, precio Decimal exacto, moneda y unidad correctos."""
    payload = _load("homedepot_varilla_482588.json")
    productos = parse_homedepot(payload, store_id=STORE_ID)

    assert len(productos) == 1
    prod = productos[0]
    assert prod.sku == "482588"
    assert prod.raw_name == "VARILLA CORRUGADA RECTA R-42 1'' 12 METROS 1 TONELADA"
    assert prod.source == HOMEDEPOT_SOURCE
    # La unidad de venta cruda se conserva en raw_payload (C62 = pieza/unidad).
    assert homedepot_unit(prod.raw_payload) == "C62"


def test_parse_varilla_prices_precio_y_disponibilidad():
    """`parse_homedepot_prices` da precio Decimal y disponibilidad por tienda."""
    payload = _load("homedepot_varilla_482588.json")
    precios = parse_homedepot_prices(
        payload, store_id=STORE_ID, captured_at=CAPTURED_AT
    )

    assert len(precios) == 1
    precio = precios[0]
    assert precio.sku == "482588"
    assert precio.price == Decimal("20068.0")
    assert isinstance(precio.price, Decimal)
    assert precio.currency == "MXN"
    assert precio.captured_at == CAPTURED_AT
    # inventories.18503.quantity == "0.0" en la tienda piloto ⇒ NO disponible.
    assert precio.is_available is False


def test_parse_disponibilidad_cae_a_inventario_total_si_no_hay_tienda():
    """Sin store_id se usa `inventories.total.quantity` (7937.29 > 0 ⇒ disponible)."""
    payload = _load("homedepot_varilla_482588.json")
    precios = parse_homedepot_prices(payload, store_id=None, captured_at=CAPTURED_AT)

    assert len(precios) == 1
    assert precios[0].is_available is True


def test_parse_batch_devuelve_todos_los_productos_con_precio():
    """Un batch de 4 SKUs: todos traen precio Decimal > 0 y sku."""
    payload = _load("homedepot_varilla_batch.json")
    precios = parse_homedepot_prices(
        payload, store_id=STORE_ID, captured_at=CAPTURED_AT
    )

    assert len(precios) == 4
    skus = {p.sku for p in precios}
    assert skus == {"462843", "179194", "749917", "480919"}
    for precio in precios:
        assert isinstance(precio.price, Decimal)
        assert precio.price > 0


def test_parse_omite_supersku_sin_precio_fiable():
    """El SuperSKU 'padre' (`Offer.value:""`, `Display:"0.0"`) se OMITE (recon §2.1)."""
    payload = _load("homedepot_supersku_empty.json")

    productos = parse_homedepot(payload, store_id=STORE_ID)
    precios = parse_homedepot_prices(
        payload, store_id=STORE_ID, captured_at=CAPTURED_AT
    )

    # No se inventa precio: el padre SuperSKU no produce ni producto ni precio.
    assert productos == []
    assert precios == []


def test_parse_payload_vacio_no_revienta():
    """Un payload sin `contents` devuelve lista vacía (robustez)."""
    assert parse_homedepot({}, store_id=STORE_ID) == []
    assert parse_homedepot_prices({}, store_id=STORE_ID, captured_at=CAPTURED_AT) == []
