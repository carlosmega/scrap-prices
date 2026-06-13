"""Router de Ninja de la app core: SOLO parseo, validación y delegación.

Ninguna llamada al ORM aquí (regla de capas, ver docs/conventions-backend.md).
"""

from ninja import Router

from apps.core import services
from apps.core.schemas import HealthOut

router = Router(tags=["core"])


@router.get("/health", response=HealthOut)
def health(request):
    """Estado del servicio. Estático, no toca la DB."""
    return services.get_health()
