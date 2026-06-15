"""Parsers puros de payloads de retailer (F025+). Sin red, sin DB, sin Django.

Cada parser traduce el JSON crudo de un retailer a los dataclasses normalizados
de F024 (`RawProduct`/`RawPrice`). Son funciones **puras**: reciben un `dict` ya
deserializado y devuelven dataclasses, sin tocar HTTP ni el ORM. Eso los hace
testeables 1:1 contra golden fixtures extraídos del HAR (docs/testing-strategy).

`parse_homedepot` cubre la plataforma HCL Commerce de Home Depot México
(docs/recon/homedepot.md §2.1): los precios viven en `contents[].price[]`
(usage `Offer`/`Display`) y/o `x_prices.<physicalStoreId>.mxn`; la disponibilidad
en `inventories.<store>.quantity`; la unidad en `x_measurements.quantityMeasure`.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from apps.scraping.base import RawPrice, RawProduct

# `source` de Home Depot: el precio viaja por XHR/JSON (HCL Commerce REST), no
# requiere render JS (recon §1). Se mapea a PriceObservation.Source.XHR de F008.
HOMEDEPOT_SOURCE = "xhr"

# Moneda por defecto del catálogo MX (recon §0: currency=MXN).
DEFAULT_CURRENCY = "MXN"


def _decimal_or_none(value: object) -> Decimal | None:
    """Convierte un valor de precio (string del payload) a Decimal seguro.

    Devuelve `None` si el valor está vacío, no es numérico o es 0 (el perfil
    SuperSKU "padre" devuelve `value:""`/`"0.0"`; el precio real está en los SKU
    hijos — recon §2.1). Tratar 0/vacío como "sin precio fiable" evita ingerir
    precios falsos de productos no comprables directamente.
    """
    if value is None:
        return None
    texto = str(value).strip()
    if not texto:
        return None
    try:
        precio = Decimal(texto)
    except (InvalidOperation, ValueError):
        return None
    if precio <= 0:
        return None
    return precio


def _extract_price(content: dict, store_id: str | None) -> tuple[Decimal | None, str]:
    """Obtiene el precio Decimal de un `content` de Home Depot y su moneda.

    Prioridad (recon §2.1):
    1. `price[]` con `usage == "Offer"` (precio de venta vigente, description "I").
    2. `x_prices.<physicalStoreId>.mxn` (precio de esa tienda física).
    3. `price[]` con `usage == "Display"` (precio de lista, description "L").

    Devuelve `(None, currency)` si ninguna fuente da un precio fiable (> 0).
    """
    price_entries = content.get("price") or []
    by_usage = {
        str(p.get("usage", "")).lower(): p
        for p in price_entries
        if isinstance(p, dict)
    }

    offer = by_usage.get("offer")
    if offer is not None:
        precio = _decimal_or_none(offer.get("value"))
        if precio is not None:
            return precio, str(offer.get("currency") or DEFAULT_CURRENCY)

    if store_id:
        precio = _decimal_or_none(content.get(f"x_prices.{store_id}.mxn"))
        if precio is not None:
            return precio, DEFAULT_CURRENCY

    display = by_usage.get("display")
    if display is not None:
        precio = _decimal_or_none(display.get("value"))
        if precio is not None:
            return precio, str(display.get("currency") or DEFAULT_CURRENCY)

    return None, DEFAULT_CURRENCY


def _extract_availability(content: dict, store_id: str | None) -> bool:
    """Deriva la disponibilidad del `content` para la tienda dada.

    Prefiere el inventario de la tienda física (`inventories.<store>.quantity`);
    si no existe, usa `inventories.total.quantity`; si tampoco, cae al flag
    `buyable`. Cantidad > 0 ⇒ disponible.
    """
    candidates: list[str] = []
    if store_id:
        candidates.append(f"inventories.{store_id}.quantity")
    candidates.append("inventories.total.quantity")

    for key in candidates:
        if key in content:
            cantidad = _decimal_or_none(content.get(key))
            return cantidad is not None and cantidad > 0

    return str(content.get("buyable", "")).lower() == "true"


def parse_homedepot(payload: dict, *, store_id: str | None = None) -> list[RawProduct]:
    """Parsea una respuesta de `/search/resources/api/v2/products` de Home Depot.

    Función pura (sin red): de `contents[]` extrae SKU (`partNumber`) y nombre,
    descartando los `content` sin precio fiable, y devuelve un `RawProduct` por
    cada producto válido (su `raw_payload` conserva el `content` crudo para
    auditoría y para resolver el precio aguas abajo con `parse_homedepot_prices`).

    Los `content` sin precio fiable (SuperSKU "padre" con `value:""`/`"0.0"`,
    recon §2.1) se OMITEN: no se inventan precios.

    `store_id` es el `physicalStoreId` de la tienda; permite leer el inventario
    y el precio específicos de esa tienda cuando están presentes.
    """
    productos: list[RawProduct] = []
    for content in payload.get("contents") or []:
        if not isinstance(content, dict):
            continue
        sku = content.get("partNumber")
        if not sku:
            continue
        precio, _currency = _extract_price(content, store_id)
        if precio is None:
            # SuperSKU padre o producto sin precio fiable: se omite (recon §2.1).
            continue
        productos.append(
            RawProduct(
                sku=str(sku),
                raw_name=str(content.get("name") or ""),
                source=HOMEDEPOT_SOURCE,
                raw_payload=content,
            )
        )
    return productos


def parse_homedepot_prices(
    payload: dict,
    *,
    store_id: str | None = None,
    captured_at: datetime,
) -> list[RawPrice]:
    """Devuelve las lecturas de precio (`RawPrice`) de un payload de Home Depot.

    Misma lógica de extracción que `parse_homedepot` (precio Decimal, moneda,
    disponibilidad, unidad), pero produce `RawPrice` con `captured_at` fijado por
    el llamador (el adapter). Omite los `content` sin precio fiable.
    """
    precios: list[RawPrice] = []
    for content in payload.get("contents") or []:
        if not isinstance(content, dict):
            continue
        sku = content.get("partNumber")
        if not sku:
            continue
        precio, currency = _extract_price(content, store_id)
        if precio is None:
            continue
        precios.append(
            RawPrice(
                sku=str(sku),
                raw_name=str(content.get("name") or ""),
                price=precio,
                currency=currency,
                is_available=_extract_availability(content, store_id),
                source=HOMEDEPOT_SOURCE,
                captured_at=captured_at,
                raw_payload=content,
            )
        )
    return precios


def homedepot_unit(content: dict) -> str:
    """Unidad de venta cruda (`x_measurements.quantityMeasure`), p.ej. C62/TN."""
    return str(content.get("x_measurements.quantityMeasure") or "")
