"""Schemas de entrada/salida de la app geo. El contrato vive aquí.

`ZoneOut` es la frontera de salida de la zona hacia la API (subconjunto público
del modelo `Zone`). `RetailerOut` expone el estado de cada retailer/scraper
(GET /api/retailers, F018). `ResolveIn` es el body de POST /api/zones/resolve.
"""

from ninja import Schema


class ZoneOut(Schema):
    """Representación pública de una zona (subconjunto del modelo Zone)."""

    id: str
    name: str
    slug: str
    state: str


class RetailerOut(Schema):
    """Representación de soporte/diagnóstico de un retailer (F018).

    Expone el modelo de pricing y el estado del scraper para que la UI/operador
    vea de un vistazo qué fuentes están activas/pausadas/no viables.
    """

    id: str
    name: str
    slug: str
    pricing_model: str
    scraper_status: str
    is_active: bool


class ResolveIn(Schema):
    """Coordenadas del usuario para resolver su zona más cercana."""

    lat: float
    lng: float
