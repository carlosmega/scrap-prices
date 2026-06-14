"""Lógica de negocio de la app geo. Sin HTTP, sin routers.

Incluye el listado de zonas activas y la resolución de la zona activa más
cercana a unas coordenadas. La distancia se calcula con haversine sobre
`centroid_lat/lng` (MVP: sin PostGIS). Las funciones reciben/devuelven tipos
del dominio o schemas, nunca `request`/`HttpResponse`.
"""

from math import asin, cos, radians, sin, sqrt

from apps.geo.models import Zone
from apps.geo.schemas import ZoneOut

# Radio medio de la Tierra en km (suficiente para ordenar por cercanía).
_EARTH_RADIUS_KM = 6371.0


def _to_out(zone: Zone) -> ZoneOut:
    """Mapea un modelo Zone a su schema público ZoneOut."""
    return ZoneOut(id=str(zone.id), name=zone.name, slug=zone.slug, state=zone.state)


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distancia haversine en km entre dos puntos (lat/lng en grados)."""
    rlat1, rlng1, rlat2, rlng2 = map(radians, (lat1, lng1, lat2, lng2))
    dlat = rlat2 - rlat1
    dlng = rlng2 - rlng1
    a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlng / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * asin(sqrt(a))


def listar_zonas_activas() -> list[ZoneOut]:
    """Devuelve las zonas activas ordenadas por nombre como ZoneOut."""
    zonas = Zone.objects.filter(is_active=True).order_by("name")
    return [_to_out(zona) for zona in zonas]


def resolver_zona(lat: float, lng: float) -> ZoneOut | None:
    """Resuelve la zona activa con centroide más cercano a (lat, lng).

    Solo considera zonas activas que tengan centroide definido. Devuelve None
    si ninguna zona activa tiene centroide (el router lo traduce a 404).
    """
    candidatas = Zone.objects.filter(
        is_active=True,
        centroid_lat__isnull=False,
        centroid_lng__isnull=False,
    )

    mas_cercana: Zone | None = None
    menor_distancia = float("inf")
    for zona in candidatas:
        distancia = _haversine_km(
            lat, lng, float(zona.centroid_lat), float(zona.centroid_lng)
        )
        if distancia < menor_distancia:
            menor_distancia = distancia
            mas_cercana = zona

    if mas_cercana is None:
        return None
    return _to_out(mas_cercana)
