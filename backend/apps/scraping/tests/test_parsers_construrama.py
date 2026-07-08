"""Tests del parser puro de Construrama (F026) contra golden fixtures.

100% OFFLINE: el parser es una función pura; estos tests cargan la respuesta
Algolia REAL sanitizada (`fixtures/construrama_varilla_algolia.json`, 7 hits de
"varilla" en el store OSS7) y verifican precio Decimal de la zona, sku
(`code_string`), nombre, marca (filtrando el token "brands"), url absoluta,
disponibilidad (`inStockFlag_boolean`) y `sale_unit` inferida del nombre (F031).
Ningún test pega a una URL real.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from apps.scraping.parsers import (
    CONSTRURAMA_SOURCE,
    construrama_brand,
    construrama_sale_unit,
    construrama_unit_raw,
    construrama_url,
    parse_construrama,
    parse_construrama_prices,
)

FIXTURES = Path(__file__).parent / "fixtures"
CAPTURED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_parse_construrama_productos_reales():
    """La respuesta real (7 hits) produce 7 RawProduct con sku/nombre/source."""
    payload = _load("construrama_varilla_algolia.json")
    productos = parse_construrama(payload)

    assert len(productos) == 7
    skus = {p.sku for p in productos}
    assert "6000111693" in skus  # varilla corrugada grado 42 1/2" 9.15m
    assert "0204000061" in skus  # varilla 1/2" 12m pieza
    for prod in productos:
        assert prod.source == CONSTRURAMA_SOURCE
        assert prod.sku
        assert prod.raw_name
        assert prod.raw_payload  # hit crudo conservado para auditoría


def test_parse_construrama_precio_decimal_de_la_zona_oss7():
    """El precio es el Decimal exacto de `OSS7_priceValue_mxn_double` (no el base 0)."""
    payload = _load("construrama_varilla_algolia.json")
    precios = parse_construrama_prices(payload, captured_at=CAPTURED_AT)

    por_sku = {p.sku: p for p in precios}
    varilla_12 = por_sku["6000111693"]
    assert varilla_12.price == Decimal("258.0")
    assert isinstance(varilla_12.price, Decimal)
    assert varilla_12.currency == "MXN"
    assert varilla_12.captured_at == CAPTURED_AT
    # inStockFlag_boolean == false en toda la captura ⇒ no disponible.
    assert varilla_12.is_available is False
    # otro precio de la zona, exacto.
    assert por_sku["0204000065"].price == Decimal("568.0")


def test_parse_construrama_ignora_hits_sin_precio_en_la_zona():
    """Un hit con `OSS7_priceValue_mxn_double` == 0 se OMITE (no se inventa precio)."""
    payload = _load("construrama_sin_precio.json")

    productos = parse_construrama(payload)
    precios = parse_construrama_prices(payload, captured_at=CAPTURED_AT)

    # De 2 hits, solo el que tiene precio de zona > 0 sobrevive.
    assert [p.sku for p in productos] == ["6000111693"]
    assert [p.sku for p in precios] == ["6000111693"]


def test_parse_construrama_prefijo_de_precio_configurable():
    """Con un prefijo de zona distinto (sin ese atributo) no hay precios (robustez)."""
    payload = _load("construrama_varilla_algolia.json")
    # La captura solo trae `OSS7_priceValue...`; pedir otro prefijo ⇒ 0 precios.
    precios = parse_construrama_prices(payload, price_prefix="OSS9", captured_at=CAPTURED_AT)
    assert precios == []


def test_parse_construrama_payload_vacio_no_revienta():
    """Respuestas vacías/malformadas devuelven lista vacía (robustez)."""
    assert parse_construrama({}) == []
    assert parse_construrama({"results": []}) == []
    assert parse_construrama_prices({}, captured_at=CAPTURED_AT) == []


@pytest.mark.parametrize(
    ("brand_mv", "esperado"),
    [
        (["brands", "GENÉRICO"], "GENÉRICO"),
        (["TRUPER", "brands"], "TRUPER"),
        (["brands"], ""),  # solo el token ruido ⇒ sin marca
        ([], ""),
    ],
)
def test_construrama_brand_filtra_el_token_brands(brand_mv, esperado):
    """La marca sale de `brand_string_mv` filtrando el token literal 'brands'."""
    assert construrama_brand({"brand_string_mv": brand_mv}) == esperado


def test_construrama_url_absoluta_desde_relativa():
    """`url` = base + `url_es_mx_string` (relativa)."""
    hit = {"url_es_mx_string": "/catalogo/aceros/varilla/varilla/x/p/6000111693"}
    assert construrama_url(hit) == (
        "https://www.construrama.com/catalogo/aceros/varilla/varilla/x/p/6000111693"
    )
    # sin url relativa ⇒ "" (no se inventa).
    assert construrama_url({}) == ""


@pytest.mark.parametrize(
    ("name", "unit_raw", "sale_unit"),
    [
        ("Varilla Corrugada Grado 42 De 1/2” 9.15 M, Kilogramos", "Kilogramos", "kg"),
        ('Varilla 5/8" 12 m, Pieza', "Pieza", "pieza"),
        ("Truper, Amarrador De Varillas Con Grip, Pieza", "Pieza", "pieza"),
        # sin coma ⇒ no se infiere unidad.
        ("Varilla sin unidad", "", ""),
    ],
)
def test_construrama_unit_y_sale_unit_desde_el_nombre(name, unit_raw, sale_unit):
    """`unit_raw` = cola tras la última coma; `sale_unit` (F031) mapea kg/pieza/m."""
    assert construrama_unit_raw(name) == unit_raw
    assert construrama_sale_unit(name) == sale_unit
