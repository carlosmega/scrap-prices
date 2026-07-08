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
    by_usage = {str(p.get("usage", "")).lower(): p for p in price_entries if isinstance(p, dict)}

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


# Mapa código UN/ECE Recommendation 20 → `RetailerProduct.SaleUnit` (F031).
# C62 = unidad/pieza; TNE/TN = tonelada métrica; KGM = kilogramo; MTR = metro.
# Lo desconocido cae a "" (no normalizable: se cura en Admin).
_HOMEDEPOT_UNECE_TO_SALE_UNIT = {
    "C62": "pieza",
    "TNE": "tonelada",
    "TN": "tonelada",
    "KGM": "kg",
    "MTR": "m",
}


def homedepot_sale_unit(code: str) -> str:
    """Mapea el código UN/ECE de `x_measurements.quantityMeasure` a `SaleUnit`.

    C62→pieza, TN/TNE→tonelada, KGM→kg, MTR→m; cualquier otro/desconocido→"".
    Función pura (sin red/DB): testeable 1:1. El "" deja el SKU sin normalizar
    para curarlo en Admin (igual que el matching a canónico queda `unmatched`).
    """
    return _HOMEDEPOT_UNECE_TO_SALE_UNIT.get(str(code or "").strip().upper(), "")


# ============================================================================
# Construrama (F026) — respuesta Algolia (índice construrama_mx)
# ============================================================================
# La búsqueda de Construrama la sirve Algolia (SAP Commerce + InstantSearch). La
# respuesta es el JSON estándar de Algolia: `{"results":[{"hits":[{...}]}]}`. El
# precio de la zona vive en un atributo *namespaced* por tienda/lista de precios,
# `{prefijo}_priceValue_mxn_double` (p.ej. `OSS7_priceValue_mxn_double` para
# Monterrey/Nuevo León). El campo base `priceValue_mxn_double` viene 0 → se ignora.

CONSTRURAMA_SOURCE = "xhr"

# Host base para reconstruir la URL absoluta del PDP a partir de la relativa
# `url_es_mx_string` (que trae el hit, p.ej. `/catalogo/.../p/{code}`).
CONSTRURAMA_BASE_URL = "https://www.construrama.com"

# Prefijo de precio por defecto (store/lista de precios de Nuevo León/Monterrey,
# `currentStore=OSS7` de `get/algolia`). Puede cambiar por zona (recon §2.1): el
# adapter lo pasa explícito desde `RetailerLocation.extra`.
CONSTRURAMA_DEFAULT_PRICE_PREFIX = "OSS7"

# Token literal a filtrar de `brand_string_mv` (Algolia lo incluye como faceta
# raíz, no como marca real): p.ej. `["brands", "GENÉRICO"]` → `"GENÉRICO"`.
_CONSTRURAMA_BRAND_NOISE = "brands"

# Palabras de la cola del nombre → `SaleUnit` (F031). El nombre de Construrama
# termina en la unidad de venta: "..., Kilogramos" (varilla grado-42 por kg) o
# "..., Pieza" (varilla lisa por pieza). Lo desconocido cae a "" (se cura en Admin).
_CONSTRURAMA_UNIT_TO_SALE_UNIT = {
    "kilogramo": "kg",
    "kilogramos": "kg",
    "kg": "kg",
    "pieza": "pieza",
    "piezas": "pieza",
    "metro": "m",
    "metros": "m",
    "m": "m",
}


def _construrama_hits(payload: dict) -> list[dict]:
    """Devuelve `results[0].hits[]` de una respuesta Algolia (o [] si no hay).

    Robusto ante respuestas vacías/malformadas: nunca revienta, devuelve [].
    """
    results = payload.get("results") or []
    if not results or not isinstance(results[0], dict):
        return []
    return [h for h in (results[0].get("hits") or []) if isinstance(h, dict)]


def _construrama_price(hit: dict, price_prefix: str) -> Decimal | None:
    """Precio Decimal de la zona (`{prefix}_priceValue_mxn_double`) o None.

    Ignora `priceValue_mxn_double` base (viene 0). Devuelve None si el atributo
    namespaced falta o no es > 0 (hit sin precio fiable → se omite, no se inventa).
    """
    return _decimal_or_none(hit.get(f"{price_prefix}_priceValue_mxn_double"))


def construrama_brand(hit: dict) -> str:
    """Marca del hit desde `brand_string_mv`, filtrando el token `"brands"`.

    `brand_string_mv` es un array que Algolia namespacea con la faceta raíz
    `"brands"` (p.ej. `["brands","GENÉRICO"]` o `["TRUPER","brands"]`). Se
    descarta ese token y se toma la primera marca real; "" si no hay ninguna.
    """
    tokens = hit.get("brand_string_mv") or []
    for token in tokens:
        texto = str(token).strip()
        if texto and texto.lower() != _CONSTRURAMA_BRAND_NOISE:
            return texto
    return ""


def construrama_url(hit: dict) -> str:
    """URL absoluta del PDP: base + `url_es_mx_string` (relativa). "" si falta."""
    relativa = str(hit.get("url_es_mx_string") or "").strip()
    if not relativa:
        return ""
    if relativa.startswith("http"):
        return relativa
    if not relativa.startswith("/"):
        relativa = f"/{relativa}"
    return f"{CONSTRURAMA_BASE_URL}{relativa}"


def construrama_unit_raw(name: str) -> str:
    """Unidad cruda del nombre: el último segmento tras la última coma.

    El nombre de Construrama termina en la unidad de venta, p.ej.
    "Varilla ... 9.15 M, Kilogramos" → "Kilogramos"; "Varilla 5/8\" 12 m, Pieza"
    → "Pieza". Sin coma, "" (no se infiere). Función pura (auditable).
    """
    texto = str(name or "")
    if "," not in texto:
        return ""
    return texto.rsplit(",", 1)[-1].strip()


def construrama_sale_unit(name: str) -> str:
    """`SaleUnit` (F031) inferida de la cola del nombre.

    "Kilogramos"→kg, "Pieza"→pieza, "Metro(s)"→m; cualquier otra/desconocida→""
    (se cura en Admin, igual que el matching a canónico). Función pura.
    """
    unidad = construrama_unit_raw(name).lower()
    return _CONSTRURAMA_UNIT_TO_SALE_UNIT.get(unidad, "")


def _construrama_sku(hit: dict) -> str:
    """Identificador del SKU: `code_string` (10 díg.); `objectID`/`pk` de respaldo."""
    for clave in ("code_string", "objectID", "pk"):
        valor = hit.get(clave)
        if valor:
            return str(valor)
    return ""


def parse_construrama(
    payload: dict, *, price_prefix: str = CONSTRURAMA_DEFAULT_PRICE_PREFIX
) -> list[RawProduct]:
    """Parsea una respuesta Algolia de Construrama a `RawProduct` (función pura).

    De `results[0].hits[]` extrae SKU (`code_string`) y nombre (`name_text_es_mx`),
    OMITIENDO los hits sin precio fiable en la zona (`{prefix}_priceValue_mxn_double`
    > 0). El `raw_payload` conserva el hit crudo para auditoría y para resolver el
    precio aguas abajo con `parse_construrama_prices`.
    """
    productos: list[RawProduct] = []
    for hit in _construrama_hits(payload):
        if _construrama_price(hit, price_prefix) is None:
            continue
        sku = _construrama_sku(hit)
        if not sku:
            continue
        productos.append(
            RawProduct(
                sku=sku,
                raw_name=str(hit.get("name_text_es_mx") or ""),
                source=CONSTRURAMA_SOURCE,
                raw_payload=hit,
            )
        )
    return productos


def parse_construrama_prices(
    payload: dict,
    *,
    price_prefix: str = CONSTRURAMA_DEFAULT_PRICE_PREFIX,
    captured_at: datetime,
) -> list[RawPrice]:
    """Lecturas de precio (`RawPrice`) de una respuesta Algolia de Construrama.

    Misma extracción que `parse_construrama`, pero produce `RawPrice` con el
    precio Decimal de la zona, moneda MXN, disponibilidad (`inStockFlag_boolean`)
    y `captured_at` fijado por el llamador (el adapter). Omite hits sin precio
    fiable (> 0): no se inventan precios.
    """
    precios: list[RawPrice] = []
    for hit in _construrama_hits(payload):
        precio = _construrama_price(hit, price_prefix)
        if precio is None:
            continue
        sku = _construrama_sku(hit)
        if not sku:
            continue
        precios.append(
            RawPrice(
                sku=sku,
                raw_name=str(hit.get("name_text_es_mx") or ""),
                price=precio,
                currency=DEFAULT_CURRENCY,
                is_available=bool(hit.get("inStockFlag_boolean")),
                source=CONSTRURAMA_SOURCE,
                captured_at=captured_at,
                raw_payload=hit,
            )
        )
    return precios
