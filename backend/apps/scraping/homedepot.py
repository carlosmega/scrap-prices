"""Adapter de Home Depot México (F025) — `source=xhr`, plataforma HCL Commerce.

Implementa `BaseRetailerAdapter` (F024) sobre el endpoint XHR documentado en el
reconocimiento (docs/recon/homedepot.md §2.1):

    GET /search/resources/api/v2/products
        ?storeId=10351&partNumber={PN}&catalogId=10101&langId=-5
        &physicalStoreId={STORE_ID}&contractId=...&currency=MXN

El adapter NO contiene ninguna técnica de evasión: la cortesía (rate-limit, UA
honesto) y el `stop-if-blocked` viven en el `PoliteClient` (F024) que usa por
composición. El parseo del cuerpo vive en `apps.scraping.parsers.parse_homedepot`
(función pura, testeada con golden fixtures). `set_zone(location)` fija el
`physicalStoreId` desde `RetailerLocation.external_id`.

Sin red en tests: el `PoliteClient` recibe un `httpx.MockTransport`.
"""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlencode

from django.utils import timezone

from apps.geo.models import RetailerLocation, Zone
from apps.scraping.base import BaseRetailerAdapter, RawPrice, RawProduct
from apps.scraping.client import PoliteClient, build_polite_client
from apps.scraping.parsers import parse_homedepot, parse_homedepot_prices

# Constantes de la plataforma HCL Commerce de HD MX (recon §0 y §2.1). No son
# secretos: son parámetros públicos del catálogo es_MX, observados en el HAR.
HOMEDEPOT_BASE_URL = "https://www.homedepot.com.mx"
PRODUCTS_PATH = "/search/resources/api/v2/products"
STORE_ID = "10351"  # storeId de la tienda online MX
CATALOG_ID = "10101"
LANG_ID = "-5"  # es_MX
CONTRACT_ID = "4000000000000000003"
CURRENCY = "MXN"


class HomeDepotAdapter(BaseRetailerAdapter):
    """Adapter de Home Depot México (`source=xhr`).

    Usa el `PoliteClient` de F024 por composición; el adapter solo arma URLs y
    delega el parseo. No reintenta ni evade bloqueos: si HD responde 403/429 o un
    challenge, el cliente lanza `RetailerBlockedError` y la corrida se detiene.
    """

    source = "xhr"

    def __init__(self, client: PoliteClient | None = None) -> None:
        # Por composición: si no se inyecta cliente, se construye uno con los
        # defaults honestos de settings (UA, delay, reintentos).
        self._client = client or build_polite_client()
        self._physical_store_id: str | None = None

    # -- zona ----------------------------------------------------------------
    def set_zone(self, location: RetailerLocation | Zone) -> None:
        """Fija el `physicalStoreId` de la tienda desde `RetailerLocation`.

        En HD la zona es una tienda física; su código (`external_id`, p.ej.
        `1333` para Monterrey) viaja como `physicalStoreId` en cada llamada de
        precio (recon §1/§3). `Zone` no porta tienda: se exige `RetailerLocation`.
        """
        if not isinstance(location, RetailerLocation):
            raise TypeError(
                "HomeDepotAdapter.set_zone requiere una RetailerLocation "
                "(la tienda física); una Zone no fija el physicalStoreId."
            )
        self._physical_store_id = str(location.external_id)

    # -- construcción de URL -------------------------------------------------
    def _build_products_url(self, part_numbers: list[str]) -> str:
        """Arma la URL del endpoint de productos con la tienda fijada.

        Acepta múltiples `partNumber` repetidos (batch, recon §2.1). Incluye el
        `physicalStoreId` para obtener precio/inventario de la tienda.
        """
        params: list[tuple[str, str]] = [
            ("storeId", STORE_ID),
            ("catalogId", CATALOG_ID),
            ("langId", LANG_ID),
            ("contractId", CONTRACT_ID),
            ("currency", CURRENCY),
        ]
        if self._physical_store_id:
            params.append(("physicalStoreId", self._physical_store_id))
        for pn in part_numbers:
            params.append(("partNumber", pn))
        return f"{HOMEDEPOT_BASE_URL}{PRODUCTS_PATH}?{urlencode(params)}"

    def _build_search_url(self, search_term: str, *, limit: int, offset: int) -> str:
        """Arma la URL de búsqueda/listado por término (recon §2.2)."""
        params: list[tuple[str, str]] = [
            ("storeId", STORE_ID),
            ("searchTerm", search_term),
            ("limit", str(limit)),
            ("offset", str(offset)),
            ("profileName", "HCL_V2_findProductsBySearchTermWithPrice"),
            ("contractId", CONTRACT_ID),
            ("currency", CURRENCY),
            ("langId", LANG_ID),
        ]
        if self._physical_store_id:
            params.append(("physicalStoreId", self._physical_store_id))
            params.append(("stLocId", self._physical_store_id))
        return f"{HOMEDEPOT_BASE_URL}{PRODUCTS_PATH}?{urlencode(params)}"

    # -- interfaz F024 -------------------------------------------------------
    def list_products(
        self, category: str, location: RetailerLocation | Zone
    ) -> list[RawProduct]:
        """Lista productos de una categoría (búsqueda por término) en la tienda.

        `category` se usa como término de búsqueda (p.ej. "varilla"). El cuerpo
        se pasa por `parse_homedepot` (pura). El `PoliteClient` aplica cortesía y
        stop-if-blocked.
        """
        self.set_zone(location)
        url = self._build_search_url(category, limit=28, offset=0)
        response = self._client.get(url, headers=self._request_headers())
        response.raise_for_status()
        payload = response.json()
        return parse_homedepot(payload, store_id=self._physical_store_id)

    def get_price(
        self, product: RawProduct, location: RetailerLocation | Zone
    ) -> RawPrice:
        """Obtiene el precio de un SKU concreto en la tienda fijada."""
        self.set_zone(location)
        captured_at = timezone.now()
        url = self._build_products_url([product.sku])
        response = self._client.get(url, headers=self._request_headers())
        response.raise_for_status()
        payload = response.json()
        precios = parse_homedepot_prices(
            payload, store_id=self._physical_store_id, captured_at=captured_at
        )
        for precio in precios:
            if precio.sku == product.sku:
                return precio
        raise ValueError(
            f"Home Depot no devolvió precio fiable para el SKU {product.sku}."
        )

    def fetch_products_with_prices(
        self,
        category: str,
        location: RetailerLocation | Zone,
        *,
        captured_at: datetime | None = None,
    ) -> list[RawPrice]:
        """Devuelve directamente los `RawPrice` de una categoría en la tienda.

        Atajo usado por la ingestión: una sola llamada (la de búsqueda) ya trae
        `contents[].price`, así que se evita una segunda petición por SKU
        (cortesía: menos requests). `captured_at` lo fija el llamador para que
        toda la corrida comparta el mismo timestamp de lectura.
        """
        self.set_zone(location)
        captured_at = captured_at or timezone.now()
        url = self._build_search_url(category, limit=28, offset=0)
        response = self._client.get(url, headers=self._request_headers())
        response.raise_for_status()
        payload = response.json()
        return parse_homedepot_prices(
            payload, store_id=self._physical_store_id, captured_at=captured_at
        )

    @staticmethod
    def _request_headers() -> dict[str, str]:
        """Headers honestos observados en el recon (§2.1). El UA lo pone el cliente.

        Se replican `Accept`/`Origin`/`Referer` del mismo origen (no son evasión:
        son los headers normales de una petición legítima al API público).
        """
        return {
            "Accept": "application/json",
            "Origin": HOMEDEPOT_BASE_URL,
            "Referer": f"{HOMEDEPOT_BASE_URL}/",
        }

    def close(self) -> None:
        self._client.close()
