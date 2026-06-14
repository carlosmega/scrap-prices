"""Tests de la API de detalle de producto (F016): GET /products/{id}.

Cubre los criterios de la spec: happy path (un canónico de varilla en Monterrey
con `prices` de ambos retailers usando la ÚLTIMA observación y `history` no vacío
ordenado `-captured_at`), 404 producto inexistente y 404 zona inexistente. Datos
del `seed` (idempotente). SQLite.
"""

import pytest
from django.core.management import call_command
from ninja.testing import TestClient

from apps.catalog.api import router
from apps.catalog.models import CanonicalProduct
from apps.geo.models import Zone


@pytest.fixture
def client():
    return TestClient(router)


@pytest.fixture
def seeded(db):
    """Aplica el seed demo y devuelve la zona piloto y un canónico de varilla."""
    call_command("seed")
    zona = Zone.objects.get(slug="monterrey-metro")
    canonico = CanonicalProduct.objects.get(name__startswith="Varilla corrugada 3/8")
    return {"zona": zona, "canonico": canonico}


@pytest.mark.django_db
def test_detalle_canonico_con_prices_y_history(client, seeded):
    """GET /products/{id}?zone_id=<MTY> devuelve canónico, prices e history."""
    zona = seeded["zona"]
    canonico = seeded["canonico"]

    response = client.get(f"/products/{canonico.id}?zone_id={zona.id}")

    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"canonical_product", "prices", "history"}

    # Canónico con specs expuestas.
    cp = data["canonical_product"]
    assert set(cp.keys()) == {"id", "name", "category", "unit", "specs"}
    assert cp["id"] == str(canonico.id)
    assert cp["category"] == "Varilla"
    assert cp["specs"]["diametro"] == '3/8"'

    # prices: ambos retailers, con la última observación (seed 3/8: HD 198.50, CR 191.00).
    por_slug = {p["retailer"]["slug"]: p for p in data["prices"]}
    assert set(por_slug.keys()) == {"home-depot", "construrama"}
    assert por_slug["home-depot"]["price"] == "198.50"
    assert por_slug["construrama"]["price"] == "191.00"
    for precio in data["prices"]:
        assert precio["is_available"] is True
        assert precio["captured_at"] is not None
        assert precio["currency"] == "MXN"

    # history: no vacío, cada punto con su retailer, orden -captured_at.
    history = data["history"]
    assert len(history) > 0
    # El seed tiene 3 capturas por retailer (2 retailers) = 6 puntos.
    assert len(history) == 6
    primer_punto = history[0]
    assert set(primer_punto.keys()) == {
        "retailer",
        "price",
        "currency",
        "is_available",
        "captured_at",
    }
    assert set(primer_punto["retailer"].keys()) == {"slug", "name"}

    capturas = [p["captured_at"] for p in history]
    assert capturas == sorted(capturas, reverse=True)
    # La captura más reciente del seed es 2026-06-13.
    assert history[0]["captured_at"].startswith("2026-06-13")


@pytest.mark.django_db
def test_producto_inexistente_responde_404(client, seeded):
    """product_id que no existe → 404."""
    zona = seeded["zona"]
    fantasma = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/products/{fantasma}?zone_id={zona.id}")
    assert response.status_code == 404


@pytest.mark.django_db
def test_producto_inactivo_responde_404(client, seeded):
    """product_id de un canónico inactivo (soft-delete) → 404."""
    zona = seeded["zona"]
    canonico = seeded["canonico"]
    canonico.is_active = False
    canonico.save(update_fields=["is_active"])

    response = client.get(f"/products/{canonico.id}?zone_id={zona.id}")
    assert response.status_code == 404


@pytest.mark.django_db
def test_zona_inexistente_responde_404(client, seeded):
    """zone_id que no existe → 404."""
    canonico = seeded["canonico"]
    fantasma = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/products/{canonico.id}?zone_id={fantasma}")
    assert response.status_code == 404


@pytest.mark.django_db
def test_zona_inactiva_responde_404(client, seeded):
    """zone_id de una zona inactiva (soft-delete) → 404."""
    zona = seeded["zona"]
    canonico = seeded["canonico"]
    zona.is_active = False
    zona.save(update_fields=["is_active"])

    response = client.get(f"/products/{canonico.id}?zone_id={zona.id}")
    assert response.status_code == 404
