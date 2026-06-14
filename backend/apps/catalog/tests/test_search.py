"""Tests de la API de búsqueda (F015): GET /search.

Cubre los criterios de la spec: happy path (varilla en Monterrey con Home Depot
y Construrama, ambos con precio + captured_at usando la ÚLTIMA observación),
orden por precio, retailer sin observación → price null / is_available False,
zona inexistente/inactiva → 404 y tolerancia a acentos. Datos del `seed`
(idempotente) y casos extra con ORM para que sean deterministas. SQLite.
"""

from decimal import Decimal

import pytest
from django.core.management import call_command
from ninja.testing import TestClient

from apps.catalog.api import router
from apps.catalog.models import CanonicalProduct, RetailerProduct
from apps.geo.models import Retailer, Zone
from apps.prices.models import PriceObservation


@pytest.fixture
def client():
    return TestClient(router)


@pytest.fixture
def seeded(db):
    """Aplica el seed demo y devuelve atajos a la zona y retailers piloto."""
    call_command("seed")
    zona = Zone.objects.get(slug="monterrey-metro")
    hd = Retailer.objects.get(slug="home-depot")
    cr = Retailer.objects.get(slug="construrama")
    return {"zona": zona, "hd": hd, "cr": cr}


@pytest.mark.django_db
def test_busqueda_varilla_en_mty_con_ambos_retailers(client, seeded):
    """GET /search?q=varilla&zone_id=<MTY> devuelve varillas con HD y CR + frescura."""
    zona = seeded["zona"]
    response = client.get(f"/search?q=varilla&zone_id={zona.id}")

    assert response.status_code == 200
    data = response.json()
    # El seed tiene 3 varillas canónicas.
    assert len(data) == 3

    item = data[0]
    assert set(item.keys()) == {"canonical_product", "prices"}
    assert set(item["canonical_product"].keys()) == {"id", "name", "category", "unit"}
    assert item["canonical_product"]["category"] == "Varilla"

    slugs = {p["retailer"]["slug"] for p in item["prices"]}
    assert slugs == {"home-depot", "construrama"}

    for precio in item["prices"]:
        assert set(precio.keys()) == {
            "retailer",
            "retailer_product_id",
            "price",
            "currency",
            "is_available",
            "captured_at",
            "url",
        }
        # Ambos retailers tienen precio y frescura (última observación).
        assert precio["price"] is not None
        assert precio["is_available"] is True
        assert precio["captured_at"] is not None
        assert precio["currency"] == "MXN"
        assert precio["url"]


@pytest.mark.django_db
def test_usa_la_ultima_observacion_por_retailer_y_zona(client, seeded):
    """El precio devuelto es el de la observación MÁS reciente (captured_at)."""
    zona = seeded["zona"]
    # Para el canónico de 3/8 (#3), el seed pone HD base 189.50 + delta 9.00 en la
    # última captura (2026-06-13) → 198.50, y CR 182.00 + 9.00 → 191.00.
    canonico = CanonicalProduct.objects.get(name__startswith="Varilla corrugada 3/8")
    response = client.get(f"/search?q=3/8&zone_id={zona.id}")

    assert response.status_code == 200
    data = response.json()
    item = next(i for i in data if i["canonical_product"]["id"] == str(canonico.id))
    por_slug = {p["retailer"]["slug"]: p for p in item["prices"]}
    assert por_slug["home-depot"]["price"] == "198.50"
    assert por_slug["construrama"]["price"] == "191.00"
    assert por_slug["home-depot"]["captured_at"].startswith("2026-06-13")


@pytest.mark.django_db
def test_orden_por_precio_menor_primero(client, seeded):
    """sort=price ordena por el menor precio disponible entre retailers."""
    zona = seeded["zona"]
    response = client.get(f"/search?q=varilla&zone_id={zona.id}&sort=price")

    assert response.status_code == 200
    data = response.json()

    def menor(item):
        return min(
            Decimal(p["price"])
            for p in item["prices"]
            if p["price"] is not None and p["is_available"]
        )

    menores = [menor(i) for i in data]
    assert menores == sorted(menores)
    # La varilla más barata (1/4 6m) va primero.
    assert "1/4" in data[0]["canonical_product"]["name"]


@pytest.mark.django_db
def test_orden_por_nombre(client, seeded):
    """sort=name ordena alfabéticamente por el nombre del canónico."""
    zona = seeded["zona"]
    response = client.get(f"/search?q=varilla&zone_id={zona.id}&sort=name")

    assert response.status_code == 200
    nombres = [i["canonical_product"]["name"] for i in response.json()]
    assert nombres == sorted(nombres)


@pytest.mark.django_db
def test_retailer_sin_observacion_price_null_no_disponible(client, seeded):
    """Un retailer enlazado pero SIN observación en la zona → price null, no disp."""
    zona = seeded["zona"]
    cr = seeded["cr"]
    canonico = CanonicalProduct.objects.get(name__startswith="Varilla corrugada 1/2")
    # Borra TODAS las observaciones de Construrama para este canónico en la zona.
    rp_cr = RetailerProduct.objects.get(retailer=cr, canonical_product=canonico)
    PriceObservation.objects.filter(retailer_product=rp_cr, zone=zona).delete()

    response = client.get(f"/search?q=1/2&zone_id={zona.id}")

    assert response.status_code == 200
    item = next(
        i for i in response.json() if i["canonical_product"]["id"] == str(canonico.id)
    )
    por_slug = {p["retailer"]["slug"]: p for p in item["prices"]}
    # Construrama aparece pero sin precio ni frescura.
    assert por_slug["construrama"]["price"] is None
    assert por_slug["construrama"]["is_available"] is False
    assert por_slug["construrama"]["captured_at"] is None
    assert por_slug["construrama"]["retailer_product_id"] == str(rp_cr.id)
    # Home Depot sí tiene precio.
    assert por_slug["home-depot"]["price"] is not None


@pytest.mark.django_db
def test_zona_inexistente_responde_404(client, seeded):
    """zone_id que no existe → 404."""
    fantasma = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/search?q=varilla&zone_id={fantasma}")
    assert response.status_code == 404


@pytest.mark.django_db
def test_zona_inactiva_responde_404(client, seeded):
    """zone_id de una zona inactiva (soft-delete) → 404."""
    zona = seeded["zona"]
    zona.is_active = False
    zona.save(update_fields=["is_active"])

    response = client.get(f"/search?q=varilla&zone_id={zona.id}")
    assert response.status_code == 404


@pytest.mark.django_db
def test_busqueda_tolerante_a_acentos(client, seeded):
    """'várilla' (con acento) encuentra los mismos resultados que 'varilla'."""
    zona = seeded["zona"]
    sin_acento = client.get(f"/search?q=varilla&zone_id={zona.id}").json()
    con_acento = client.get(f"/search?q=várilla&zone_id={zona.id}").json()

    assert len(con_acento) == len(sin_acento) == 3
    ids_con = {i["canonical_product"]["id"] for i in con_acento}
    ids_sin = {i["canonical_product"]["id"] for i in sin_acento}
    assert ids_con == ids_sin


@pytest.mark.django_db
def test_acento_en_el_nombre_del_canonico(client, seeded):
    """Un canónico con acento se encuentra buscando sin acento."""
    zona = seeded["zona"]
    canonico = CanonicalProduct.objects.create(
        name="Cemento Pórtland gris 50kg",
        category=CanonicalProduct.objects.first().category,
        unit=CanonicalProduct.Unit.SACO,
    )

    response = client.get(f"/search?q=portland&zone_id={zona.id}")

    assert response.status_code == 200
    ids = {i["canonical_product"]["id"] for i in response.json()}
    assert str(canonico.id) in ids
