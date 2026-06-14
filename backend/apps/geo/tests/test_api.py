"""Tests de la API de zonas (F014): GET /zones y POST /zones/resolve.

Usa el TestClient de Ninja sobre el router de geo (paths relativos al router:
/zones, /zones/resolve). Los datos se crean con el ORM dentro del test para que
sean deterministas e independientes del seed. SQLite, sin Docker.
"""

from decimal import Decimal

import pytest
from ninja.testing import TestClient

from apps.geo import services
from apps.geo.api import router
from apps.geo.models import Zone


@pytest.fixture
def client():
    return TestClient(router)


@pytest.fixture
def monterrey():
    """Zona activa con centroide cerca de Monterrey (la del seed)."""
    return Zone.objects.create(
        name="Monterrey Metro",
        slug="monterrey-metro",
        state="NL",
        centroid_lat=Decimal("25.673200"),
        centroid_lng=Decimal("-100.297300"),
    )


@pytest.mark.django_db
def test_listar_zonas_devuelve_solo_activas_ordenadas(client, monterrey):
    """GET /zones lista zonas activas como ZoneOut, ordenadas por nombre."""
    # Una zona activa adicional que va antes alfabéticamente.
    Zone.objects.create(
        name="Guadalajara Metro",
        slug="guadalajara-metro",
        state="JAL",
        centroid_lat=Decimal("20.659699"),
        centroid_lng=Decimal("-103.349609"),
    )
    # Una zona inactiva: NO debe aparecer.
    Zone.objects.create(
        name="Zona Inactiva",
        slug="zona-inactiva",
        state="NL",
        is_active=False,
    )

    response = client.get("/zones")

    assert response.status_code == 200
    data = response.json()
    nombres = [z["name"] for z in data]
    assert nombres == ["Guadalajara Metro", "Monterrey Metro"]
    # Shape exacto del contrato ZoneOut.
    mty = next(z for z in data if z["slug"] == "monterrey-metro")
    assert set(mty.keys()) == {"id", "name", "slug", "state"}
    assert mty["state"] == "NL"
    assert mty["id"] == str(monterrey.id)


@pytest.mark.django_db
def test_resolve_monterrey_devuelve_zona_mas_cercana(client, monterrey):
    """POST /zones/resolve con coords de Monterrey devuelve 'Monterrey Metro'."""
    # Una zona lejana (Guadalajara) que NO debe ganar.
    Zone.objects.create(
        name="Guadalajara Metro",
        slug="guadalajara-metro",
        state="JAL",
        centroid_lat=Decimal("20.659699"),
        centroid_lng=Decimal("-103.349609"),
    )

    response = client.post("/zones/resolve", json={"lat": 25.68, "lng": -100.31})

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Monterrey Metro"
    assert data["slug"] == "monterrey-metro"
    assert data["id"] == str(monterrey.id)


@pytest.mark.django_db
def test_resolve_sin_zonas_con_centroide_responde_404(client):
    """Sin zonas activas con centroide, /zones/resolve → 404 'aún sin cobertura'."""
    # Zona activa pero SIN centroide: no es candidata.
    Zone.objects.create(name="Sin Centroide", slug="sin-centroide", state="NL")

    response = client.post("/zones/resolve", json={"lat": 25.68, "lng": -100.31})

    assert response.status_code == 404
    assert response.json() == {"detail": "aún sin cobertura"}


@pytest.mark.django_db
def test_service_resolver_zona_ignora_inactivas(monterrey):
    """La lógica de negocio (services) descarta zonas inactivas al resolver."""
    monterrey.is_active = False
    monterrey.save(update_fields=["is_active"])

    assert services.resolver_zona(lat=25.68, lng=-100.31) is None
