"""Tests del endpoint de salud /api/health.

El endpoint es estático (no toca la DB), así que se prueba el contrato con el
TestClient de Ninja (sin cliente HTTP real, sin red) y la lógica con el
servicio directo.
"""

from ninja.testing import TestClient

from apps.core import services
from apps.core.api import router


def test_health_endpoint_devuelve_status_ok():
    """GET /health responde 200 con el shape {"status": "ok"} del contrato."""
    client = TestClient(router)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_servicio_health_es_estatico():
    """El servicio de salud devuelve 'ok' sin consultar la DB."""
    resultado = services.get_health()

    assert resultado.status == "ok"
