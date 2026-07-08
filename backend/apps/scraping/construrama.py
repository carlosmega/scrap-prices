"""Adapter de Construrama (F026) — `source=xhr`, precio servido por Algolia.

Construrama (red CEMEX, SAP Commerce/Hybris + InstantSearch) sirve el precio por
zona como un atributo de su índice Algolia `construrama_mx`
(`{prefijo}_priceValue_mxn_double`, p.ej. `OSS7_priceValue_mxn_double` para
Nuevo León/Monterrey). Este adapter consulta Algolia **directamente** (Plan A del
recon §5): así evita el WAF Imperva del host `construrama.com` y NO necesita
render JS para leer el precio.

Guardrails (§2.3), heredados del `PoliteClient` (F024) por composición:
UA honesto, rate-limit por dominio, reintentos solo de transitorios y
**stop-if-blocked** (403/429/challenge → `RetailerBlockedError`, sin evasión). El
adapter NO trae ninguna técnica de evasión.

**Search key:** es pública (search-only) pero NO se hardcodea ni se commitea. Se
lee de `settings.CONSTRURAMA_ALGOLIA_SEARCH_KEY` (de env) o se inyecta por
constructor; si falta, el adapter falla claro ANTES de pegar a la red. El App ID
y el índice sí son públicos (default en settings). El parseo del cuerpo vive en
`apps.scraping.parsers.parse_construrama*` (funciones puras, golden fixtures).

Sin red en tests: el `PoliteClient` recibe un `httpx.MockTransport`.
"""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlencode

from django.conf import settings
from django.utils import timezone

from apps.geo.models import RetailerLocation, Zone
from apps.scraping.base import BaseRetailerAdapter, RawPrice, RawProduct
from apps.scraping.client import PoliteClient, build_polite_client
from apps.scraping.exceptions import ScrapeError
from apps.scraping.parsers import (
    CONSTRURAMA_BASE_URL,
    CONSTRURAMA_DEFAULT_PRICE_PREFIX,
    parse_construrama,
    parse_construrama_prices,
)

# Cuántos hits pide una página de la PLP. Conservador: una sola página cubre la
# categoría piloto (varilla, 7 hits reales). La paginación por `page`/`nbPages`
# queda como seguimiento (igual que en HD).
DEFAULT_HITS_PER_PAGE = 20

# userToken anónimo y ESTABLE (analytics de Algolia). Honesto: no suplanta a un
# usuario real ni rota identidad; identifica a ConstruScan de forma anónima.
ANONYMOUS_USER_TOKEN = "cma-anonymous-construscan"

# Se identifica ante Algolia de forma honesta (transparencia, no evasión).
ALGOLIA_AGENT = "ConstruScan (respetuoso; +contacto)"


class ConstruramaAdapter(BaseRetailerAdapter):
    """Adapter de Construrama (`source=xhr`) sobre la Query API de Algolia.

    Usa el `PoliteClient` de F024 por composición; solo arma la URL/cuerpo de la
    consulta y delega el parseo. No reintenta ni evade bloqueos: si Algolia/el
    retailer responde 403/429 o un challenge, el cliente lanza
    `RetailerBlockedError` y la corrida se detiene (§2.3).
    """

    source = "xhr"

    def __init__(
        self,
        client: PoliteClient | None = None,
        *,
        app_id: str | None = None,
        search_key: str | None = None,
        index: str | None = None,
        price_prefix: str | None = None,
    ) -> None:
        # Por composición: si no se inyecta cliente, se construye con los
        # defaults honestos de settings (UA, delay, reintentos).
        self._client = client or build_polite_client()
        self._app_id = app_id or settings.CONSTRURAMA_ALGOLIA_APP_ID
        # La search key: env por defecto (default vacío) o inyectada en tests.
        self._search_key = (
            search_key if search_key is not None else settings.CONSTRURAMA_ALGOLIA_SEARCH_KEY
        )
        self._index = index or settings.CONSTRURAMA_ALGOLIA_INDEX
        self._price_prefix = price_prefix or CONSTRURAMA_DEFAULT_PRICE_PREFIX

    # -- zona ----------------------------------------------------------------
    def set_zone(self, location: RetailerLocation | Zone) -> None:
        """Fija los params de zona Algolia desde `RetailerLocation.extra`.

        En Construrama la zona es un estado/distribuidor cuyo precio vive en un
        atributo namespaced por tienda/lista de precios (`currentStore=OSS7`).
        `extra` (sembrado por el seed F026) puede portar `current_store` (→
        prefijo de precio), `algolia_app_id` y `algolia_index`; cualquiera que
        falte cae al default del constructor/settings. `Zone` no porta esos
        params: se exige `RetailerLocation`.
        """
        if not isinstance(location, RetailerLocation):
            raise TypeError(
                "ConstruramaAdapter.set_zone requiere una RetailerLocation "
                "(el distribuidor/estado con su prefijo de precio); una Zone no "
                "porta el currentStore/índice de Algolia."
            )
        extra = location.extra or {}
        current_store = extra.get("current_store")
        if current_store:
            self._price_prefix = str(current_store)
        app_id = extra.get("algolia_app_id")
        if app_id:
            self._app_id = str(app_id)
        index = extra.get("algolia_index")
        if index:
            self._index = str(index)

    # -- construcción de la petición Algolia --------------------------------
    def _algolia_url(self) -> str:
        """URL de la Query API multi-índice de Algolia para este App ID.

        El host usa el App ID en minúsculas (`{appid}-dsn.algolia.net`); el
        `x-algolia-agent` se identifica de forma honesta.
        """
        host = f"{self._app_id.lower()}-dsn.algolia.net"
        query = urlencode({"x-algolia-agent": ALGOLIA_AGENT})
        return f"https://{host}/1/indexes/*/queries?{query}"

    def _build_params(self, category: str, *, hits_per_page: int, page: int) -> str:
        """Arma el `params` (query string) de la consulta de un índice.

        Incluye el filtro con el precio de la zona (`{prefix}_priceValue... > 0`),
        que además descarta hits sin precio del lado del servidor.
        """
        filtro = (
            f"allCategories_string_mv:{self._price_prefix}Category "
            f"AND ({self._price_prefix}_priceValue_mxn_double > 0)"
        )
        return urlencode(
            {
                "query": category,
                "hitsPerPage": hits_per_page,
                "page": page,
                "filters": filtro,
                "userToken": ANONYMOUS_USER_TOKEN,
            }
        )

    def _build_body(self, category: str, *, hits_per_page: int, page: int) -> dict:
        """Cuerpo multi-query InstantSearch para el índice de productos."""
        return {
            "requests": [
                {
                    "indexName": self._index,
                    "params": self._build_params(category, hits_per_page=hits_per_page, page=page),
                }
            ]
        }

    def _request_headers(self) -> dict[str, str]:
        """Headers honestos de la Query API (el UA lo pone el `PoliteClient`).

        Exige la search key ANTES de pegar a la red: sin ella no hay consulta
        (no se inventa ni se hardcodea). App ID e índice son públicos.
        """
        if not self._search_key:
            raise ScrapeError(
                "Falta la search key de Algolia de Construrama. Defínela en "
                "CONSTRURAMA_ALGOLIA_SEARCH_KEY (o re-obténla de `get/algolia`). "
                "No se hardcodea ni se commitea."
            )
        return {
            "x-algolia-application-id": self._app_id,
            "x-algolia-api-key": self._search_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": CONSTRURAMA_BASE_URL,
        }

    def _post_query(self, category: str, *, hits_per_page: int, page: int) -> dict:
        """POST cortés a Algolia y devuelve el JSON (el cliente aplica §2.3)."""
        headers = self._request_headers()
        url = self._algolia_url()
        body = self._build_body(category, hits_per_page=hits_per_page, page=page)
        response = self._client.post(url, json=body, headers=headers)
        response.raise_for_status()
        return response.json()

    # -- interfaz F024 -------------------------------------------------------
    def list_products(self, category: str, location: RetailerLocation | Zone) -> list[RawProduct]:
        """Lista productos de una categoría (query Algolia) en la zona."""
        self.set_zone(location)
        payload = self._post_query(category, hits_per_page=DEFAULT_HITS_PER_PAGE, page=0)
        return parse_construrama(payload, price_prefix=self._price_prefix)

    def get_price(self, product: RawProduct, location: RetailerLocation | Zone) -> RawPrice:
        """Obtiene el precio de un SKU concreto (query por su `code`) en la zona."""
        self.set_zone(location)
        captured_at = timezone.now()
        payload = self._post_query(product.sku, hits_per_page=DEFAULT_HITS_PER_PAGE, page=0)
        precios = parse_construrama_prices(
            payload, price_prefix=self._price_prefix, captured_at=captured_at
        )
        for precio in precios:
            if precio.sku == product.sku:
                return precio
        raise ValueError(f"Construrama no devolvió precio fiable para el SKU {product.sku}.")

    def fetch_products_with_prices(
        self,
        category: str,
        location: RetailerLocation | Zone,
        *,
        captured_at: datetime | None = None,
    ) -> list[RawPrice]:
        """`RawPrice` de una categoría en la zona en UNA sola consulta (cortesía).

        La respuesta Algolia ya trae el precio de cada hit, así que se evita una
        2ª petición por SKU. `captured_at` lo fija el llamador para que toda la
        corrida comparta el mismo timestamp de lectura.
        """
        self.set_zone(location)
        captured_at = captured_at or timezone.now()
        payload = self._post_query(category, hits_per_page=DEFAULT_HITS_PER_PAGE, page=0)
        return parse_construrama_prices(
            payload, price_prefix=self._price_prefix, captured_at=captured_at
        )

    def close(self) -> None:
        self._client.close()
