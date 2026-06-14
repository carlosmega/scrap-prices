"""Router de Ninja de la app geo: SOLO parseo, validación y delegación.

Ninguna llamada al ORM aquí (regla de capas, ver docs/conventions-backend.md):
toda la lógica vive en services.py.
"""

from ninja import Router
from ninja.errors import HttpError

from apps.geo import services
from apps.geo.schemas import ResolveIn, ZoneOut

router = Router(tags=["geo"])


@router.get("/zones", response=list[ZoneOut])
def listar_zonas(request):
    """Lista las zonas activas ordenadas por nombre."""
    return services.listar_zonas_activas()


@router.post("/zones/resolve", response=ZoneOut)
def resolver_zona(request, data: ResolveIn):
    """Resuelve la zona activa más cercana al centroide. 404 si sin cobertura."""
    zona = services.resolver_zona(lat=data.lat, lng=data.lng)
    if zona is None:
        raise HttpError(404, "aún sin cobertura")
    return zona
