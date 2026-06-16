"""Normalización pura de precios a base comparable (F031). Sin ORM, sin HTTP.

`PriceObservation.price` es un Decimal **sin unidad**: cada retailer lista en su
propia unidad (Home Depot por tonelada, Construrama por kg, el seed por pieza).
Comparar el número crudo cross-retailer es inválido. Aquí se traduce el precio
nativo a dos bases comparables — **por pieza** (titular intuitivo de obra) y
**por kg** (base de orden/menor-precio, agnóstica a la longitud) — usando el
peso de la pieza canónica (`mass_kg`).

Es una función **pura**: recibe/devuelve `Decimal`, sin tocar el ORM ni HTTP, lo
que la hace testeable 1:1 contra una tabla de casos (decisiones de producto en
`specs/F031-normalizacion-unidad.md`).
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

# Unidades que `normaliza_precio` sabe convertir. El resto (saco/m/"") cae a
# (None, None): "sin normalizar". El enum del modelo admite más, pero cerrarlas
# no es objetivo de F031.
_KG = "kg"
_TONELADA = "tonelada"
_PIEZA = "pieza"

# Kilogramos por tonelada (factor de conversión tonelada→kg).
_KG_POR_TONELADA = Decimal("1000")

# Cuantización monetaria: 2 decimales, ROUND_HALF_UP (igual criterio que el
# resto de montos del dominio; PRD §8 exactitud monetaria).
_CENTAVOS = Decimal("0.01")


def _cuantiza(valor: Decimal) -> Decimal:
    """Redondea a 2 decimales con ROUND_HALF_UP (centavos)."""
    return valor.quantize(_CENTAVOS, rounding=ROUND_HALF_UP)


def normaliza_precio(
    price: Decimal | None,
    sale_unit: str,
    mass_kg: Decimal | None,
) -> tuple[Decimal | None, Decimal | None]:
    """Convierte un precio nativo a `(price_per_piece, price_per_kg)`.

    `None` en cualquiera de los dos lados cuando no se puede computar (falta
    `price`, falta `mass_kg`, o la unidad no es convertible). Resultado parcial
    permitido: un lado puede tener valor y el otro `None`.

    Reglas (cada resultado no-None se cuantiza a 2 decimales, ROUND_HALF_UP):
    - `price is None` → `(None, None)`.
    - `sale_unit == "kg"`: `per_kg = price`; `per_piece = price × mass_kg` (si
      `mass_kg > 0`, si no `None`).
    - `sale_unit == "tonelada"`: `per_kg = price / 1000`; `per_piece = per_kg ×
      mass_kg` (si `mass_kg > 0`, si no `None`).
    - `sale_unit == "pieza"`: `per_piece = price`; `per_kg = price / mass_kg` (si
      `mass_kg > 0`, si no `None`).
    - cualquier otra unidad (`saco`/`m`/`""`/desconocida): `(None, None)`.
    """
    if price is None:
        return None, None

    tiene_masa = mass_kg is not None and mass_kg > 0

    if sale_unit == _KG:
        per_kg = price
        per_piece = price * mass_kg if tiene_masa else None
    elif sale_unit == _TONELADA:
        per_kg = price / _KG_POR_TONELADA
        per_piece = per_kg * mass_kg if tiene_masa else None
    elif sale_unit == _PIEZA:
        per_piece = price
        per_kg = price / mass_kg if tiene_masa else None
    else:
        return None, None

    return (
        _cuantiza(per_piece) if per_piece is not None else None,
        _cuantiza(per_kg) if per_kg is not None else None,
    )
