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

    # Canónico con specs y mass_kg expuestos (F031).
    cp = data["canonical_product"]
    assert set(cp.keys()) == {"id", "name", "category", "unit", "mass_kg", "specs"}
    assert cp["id"] == str(canonico.id)
    assert cp["category"] == "Varilla"
    assert cp["specs"]["diametro"] == '3/8"'
    # mass_kg de la #3 = 0.557 kg/m × 12 m = 6.684 (string Decimal).
    assert cp["mass_kg"] == "6.684"

    # prices: ambos retailers, última observación NATIVA (seed 3/8 ×1.030:
    # HD 20085.00/ton, CR 21.53/kg) + normalizados $/kg (HD 20.09, CR 21.53).
    por_slug = {p["retailer"]["slug"]: p for p in data["prices"]}
    assert set(por_slug.keys()) == {"home-depot", "construrama"}
    assert por_slug["home-depot"]["price"] == "20085.00"
    assert por_slug["home-depot"]["sale_unit"] == "tonelada"
    assert por_slug["home-depot"]["price_per_kg"] == "20.09"
    assert por_slug["construrama"]["price"] == "21.53"
    assert por_slug["construrama"]["sale_unit"] == "kg"
    assert por_slug["construrama"]["price_per_kg"] == "21.53"
    for precio in data["prices"]:
        assert precio["is_available"] is True
        assert precio["captured_at"] is not None
        assert precio["currency"] == "MXN"
        # F031: el detalle también trae los campos normalizados.
        assert "price_per_piece" in precio
        assert "price_per_kg" in precio

    # history: no vacío, cada punto con su retailer, orden -captured_at.
    history = data["history"]
    assert len(history) > 0
    # El seed tiene 4 capturas por retailer (3 fijas + la FRESCA de F033) × 2
    # retailers = 8 puntos.
    assert len(history) == 8
    primer_punto = history[0]
    # F031: cada punto del historial gana `sale_unit` (etiqueta de unidad nativa).
    assert set(primer_punto.keys()) == {
        "retailer",
        "price",
        "currency",
        "is_available",
        "captured_at",
        "sale_unit",
    }
    assert primer_punto["sale_unit"] in {"tonelada", "kg"}
    assert set(primer_punto["retailer"].keys()) == {"slug", "name"}

    capturas = [p["captured_at"] for p in history]
    assert capturas == sorted(capturas, reverse=True)
    # F033: la captura más reciente del seed es la FRESCA (captured_at ≈ ahora,
    # así los términos sembrados no disparan el scrape en vivo); las fijas del
    # historial (2026-06-13, -06-06, -05-30) van detrás.
    assert any(c.startswith("2026-06-13") for c in capturas)
    assert history[0]["captured_at"] > "2026-06-13"


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
