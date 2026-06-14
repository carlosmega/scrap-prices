"""Schemas de entrada/salida de la app geo. El contrato vive aquí.

`ZoneOut` es la frontera de salida de la zona hacia la API (subconjunto público
del modelo `Zone`). `ResolveIn` es el body de POST /api/zones/resolve.
"""

from ninja import Schema


class ZoneOut(Schema):
    """Representación pública de una zona (subconjunto del modelo Zone)."""

    id: str
    name: str
    slug: str
    state: str


class ResolveIn(Schema):
    """Coordenadas del usuario para resolver su zona más cercana."""

    lat: float
    lng: float
