"""Lógica de negocio de la app core. Sin HTTP, sin routers.

El estado de salud es estático por diseño (no toca la DB): /api/health debe
responder aunque la base de datos esté caída.
"""

from apps.core.schemas import HealthOut


def get_health() -> HealthOut:
    """Devuelve el estado del servicio. Estático: no consulta la DB."""
    return HealthOut(status="ok")
