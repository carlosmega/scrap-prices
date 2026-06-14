"""Tests de la API de retailers (F018): GET /retailers.

Usa el TestClient de Ninja sobre el router de geo (path relativo al router:
/retailers; la URL final es /api/retailers). Los datos se crean con el ORM
dentro del test para que sean deterministas e independientes del seed.
SQLite, sin Docker.
"""

import pytest
from ninja.testing import TestClient

from apps.geo.api import router
from apps.geo.models import Retailer


@pytest.fixture
def client():
    return TestClient(router)


@pytest.fixture
def retailers():
    """Tres retailers: dos activos y uno inactivo (diagnóstico)."""
    home_depot = Retailer.objects.create(
        name="Home Depot",
        slug="home-depot",
        base_url="https://www.homedepot.com.mx",
        pricing_model=Retailer.PricingModel.ZONE_COOKIE,
        scraper_status=Retailer.ScraperStatus.ACTIVE,
    )
    construrama = Retailer.objects.create(
        name="Construrama",
        slug="construrama",
        base_url="https://www.construrama.com",
        pricing_model=Retailer.PricingModel.DISTRIBUTOR_SUBPATH,
        scraper_status=Retailer.ScraperStatus.PAUSED,
    )
    # Retailer inactivo: DEBE aparecer (endpoint de diagnóstico).
    Retailer.objects.create(
        name="Aki Construye",
        slug="aki-construye",
        base_url="https://www.aki.example",
        pricing_model=Retailer.PricingModel.ZONE_COOKIE,
        scraper_status=Retailer.ScraperStatus.NON_VIABLE,
        is_active=False,
    )
    return {"home_depot": home_depot, "construrama": construrama}


@pytest.mark.django_db
def test_listar_retailers_todos_ordenados_por_nombre(client, retailers):
    """GET /retailers devuelve TODOS los retailers (incl. inactivos) por nombre."""
    response = client.get("/retailers")

    assert response.status_code == 200
    data = response.json()
    # Los tres aparecen (incluye el inactivo), ordenados por nombre.
    nombres = [r["name"] for r in data]
    assert nombres == ["Aki Construye", "Construrama", "Home Depot"]


@pytest.mark.django_db
def test_listar_retailers_shape_y_valores(client, retailers):
    """Cada item respeta el shape exacto de RetailerOut con valores correctos."""
    response = client.get("/retailers")
    data = response.json()

    construrama = next(r for r in data if r["slug"] == "construrama")
    assert set(construrama.keys()) == {
        "id",
        "name",
        "slug",
        "pricing_model",
        "scraper_status",
        "is_active",
    }
    assert construrama["id"] == str(retailers["construrama"].id)
    assert construrama["name"] == "Construrama"
    assert construrama["pricing_model"] == "distributor_subpath"
    assert construrama["scraper_status"] == "paused"
    assert construrama["is_active"] is True

    home_depot = next(r for r in data if r["slug"] == "home-depot")
    assert home_depot["pricing_model"] == "zone_cookie"
    assert home_depot["scraper_status"] == "active"

    inactivo = next(r for r in data if r["slug"] == "aki-construye")
    assert inactivo["is_active"] is False
    assert inactivo["scraper_status"] == "non_viable"
