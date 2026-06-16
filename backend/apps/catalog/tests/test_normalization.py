"""Tests de la normalización pura de precios (F031).

`normaliza_precio` es una función pura (sin ORM, sin HTTP): se prueba 1:1 con
una tabla de casos que cubre cada regla de la spec — tonelada/kg/pieza con y sin
`mass_kg`, `price=None`, unidad desconocida y la cuantización a 2 decimales con
ROUND_HALF_UP. Ningún test toca la DB.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.catalog.normalization import normaliza_precio

# masa de la varilla #4 (1/2", 12 m) del seed: 0.996 kg/m × 12 m = 11.952 kg.
_MASS_4 = Decimal("11.952")


@pytest.mark.parametrize(
    ("price", "sale_unit", "mass_kg", "esperado"),
    [
        # --- kg: per_kg = price; per_piece = price × mass_kg --------------------
        ("20.90", "kg", _MASS_4, (Decimal("249.80"), Decimal("20.90"))),
        # kg sin masa: per_kg sí, per_piece None (resultado parcial).
        ("20.90", "kg", None, (None, Decimal("20.90"))),
        # --- tonelada: per_kg = price/1000; per_piece = per_kg × mass_kg --------
        # HD #4 nativo $19500/ton → $19.50/kg → $233.06/pieza.
        ("19500.00", "tonelada", _MASS_4, (Decimal("233.06"), Decimal("19.50"))),
        # tonelada sin masa: per_kg sí, per_piece None.
        ("19500.00", "tonelada", None, (None, Decimal("19.50"))),
        # --- pieza: per_piece = price; per_kg = price/mass_kg -------------------
        ("236.65", "pieza", _MASS_4, (Decimal("236.65"), Decimal("19.80"))),
        # pieza sin masa: per_piece sí, per_kg None.
        ("236.65", "pieza", None, (Decimal("236.65"), None)),
        # --- price None: (None, None) sin importar la unidad/masa --------------
        (None, "kg", _MASS_4, (None, None)),
        (None, "tonelada", None, (None, None)),
        # --- unidad desconocida / no convertible: (None, None) -----------------
        ("100.00", "saco", _MASS_4, (None, None)),
        ("100.00", "m", _MASS_4, (None, None)),
        ("100.00", "", _MASS_4, (None, None)),
        # --- mass_kg == 0 se trata como "sin masa" (evita división por cero) ----
        ("100.00", "pieza", Decimal("0"), (Decimal("100.00"), None)),
    ],
)
def test_normaliza_precio_tabla(price, sale_unit, mass_kg, esperado):
    """Cada fila de la tabla de la spec produce (price_per_piece, price_per_kg)."""
    price_dec = Decimal(price) if price is not None else None
    assert normaliza_precio(price_dec, sale_unit, mass_kg) == esperado


def test_cuantiza_round_half_up():
    """La cuantización a 2dp usa ROUND_HALF_UP (no el banker's rounding de Python).

    price/mass_kg = 1.005 → con ROUND_HALF_UP es 1.01 (no 1.00).
    """
    # pieza: per_kg = price / mass_kg. 1.005 → 1.01 (half up).
    per_piece, per_kg = normaliza_precio(
        Decimal("2.010"), "pieza", Decimal("2.000")
    )
    assert per_piece == Decimal("2.01")
    assert per_kg == Decimal("1.01")


def test_resultado_es_decimal():
    """Los resultados no-None son Decimal (exactitud monetaria)."""
    per_piece, per_kg = normaliza_precio(Decimal("20.90"), "kg", _MASS_4)
    assert isinstance(per_piece, Decimal)
    assert isinstance(per_kg, Decimal)
