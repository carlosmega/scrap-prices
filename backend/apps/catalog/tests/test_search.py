"""Tests de la API de búsqueda (F015/F033): GET /search.

Cubre los criterios de la spec: happy path (varilla en Monterrey con Home Depot
y Construrama, ambos con precio + captured_at usando la ÚLTIMA observación),
orden por precio, retailer sin observación → price null / is_available False,
zona inexistente/inactiva → 404 y tolerancia a acentos. Datos del `seed`
(idempotente) y casos extra con ORM para que sean deterministas. SQLite.

F033 (BREAKING): la respuesta pasa de lista a objeto `SearchOut`
(`results` + `raw_results` + `live`). Estos tests verifican la búsqueda servida
de la DB: el seed deja observaciones FRESCAS, así que `live` es null (no se
dispara el vivo); el disparo en vivo se cubre en `test_live_search.py`. La
única query sin datos ("portland") usa `live=never` explícito.
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone
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


def _results(response) -> list[dict]:
    """Extrae los canónicos comparados del objeto SearchOut (F033)."""
    assert response.status_code == 200
    return response.json()["results"]


@pytest.mark.django_db
def test_busqueda_varilla_en_mty_con_ambos_retailers(client, seeded):
    """GET /search?q=varilla&zone_id=<MTY> devuelve varillas con HD y CR + frescura."""
    zona = seeded["zona"]
    response = client.get(f"/search?q=varilla&zone_id={zona.id}")

    assert response.status_code == 200
    body = response.json()
    # F033: respuesta objeto (BREAKING): canónicos + crudos + info del vivo.
    assert set(body.keys()) == {"results", "raw_results", "live"}
    # El seed deja datos FRESCOS → la corrida en vivo NO se dispara.
    assert body["live"] is None
    data = body["results"]
    # El seed tiene 3 varillas canónicas.
    assert len(data) == 3
    # F033: la sección cruda trae el hallazgo sembrado sin matchear (Truper).
    assert [c["external_sku"] for c in body["raw_results"]] == ["0204000086"]

    item = data[0]
    assert set(item.keys()) == {"canonical_product", "prices"}
    # F031: el canónico expone mass_kg (factor de normalización).
    assert set(item["canonical_product"].keys()) == {
        "id",
        "name",
        "category",
        "unit",
        "mass_kg",
    }
    assert item["canonical_product"]["category"] == "Varilla"
    assert item["canonical_product"]["mass_kg"] is not None

    slugs = {p["retailer"]["slug"] for p in item["prices"]}
    assert slugs == {"home-depot", "construrama"}

    for precio in item["prices"]:
        # F031: cada precio trae unidad nativa + normalizados $/pieza y $/kg.
        assert set(precio.keys()) == {
            "retailer",
            "retailer_product_id",
            "price",
            "currency",
            "is_available",
            "captured_at",
            "url",
            "sale_unit",
            "price_per_piece",
            "price_per_kg",
        }
        # Ambos retailers tienen precio NATIVO y frescura (última observación).
        assert precio["price"] is not None
        assert precio["is_available"] is True
        assert precio["captured_at"] is not None
        assert precio["currency"] == "MXN"
        assert precio["url"]
        # El seed siembra unidad por retailer (HD tonelada, CR kg) → normalizables.
        assert precio["sale_unit"] in {"tonelada", "kg"}
        assert precio["price_per_piece"] is not None
        assert precio["price_per_kg"] is not None


@pytest.mark.django_db
def test_usa_la_ultima_observacion_por_retailer_y_zona(client, seeded):
    """El precio devuelto es el NATIVO de la observación MÁS reciente (captured_at)."""
    zona = seeded["zona"]
    # F031: para el canónico de 3/8 (#3), el seed pone HD base 19500.00/ton y CR
    # 20.90/kg; la captura vigente aplica ×1.030 → HD 20085.00/ton, CR 21.53/kg
    # (precios NATIVOS en cada unidad). F033: esa captura vigente es FRESCA
    # (captured_at = ahora, la siembra `_sembrar_observacion_fresca`).
    canonico = CanonicalProduct.objects.get(name__startswith="Varilla corrugada 3/8")
    response = client.get(f"/search?q=3/8&zone_id={zona.id}")

    data = _results(response)
    item = next(i for i in data if i["canonical_product"]["id"] == str(canonico.id))
    por_slug = {p["retailer"]["slug"]: p for p in item["prices"]}
    assert por_slug["home-depot"]["price"] == "20085.00"
    assert por_slug["home-depot"]["sale_unit"] == "tonelada"
    assert por_slug["construrama"]["price"] == "21.53"
    assert por_slug["construrama"]["sale_unit"] == "kg"
    # La última observación es la fresca del seed (hace instantes, no la fija
    # de 2026-06-13): así la búsqueda sembrada no dispara el vivo (F033).
    capturado = datetime.fromisoformat(por_slug["home-depot"]["captured_at"])
    assert timezone.now() - capturado < timedelta(hours=1)
    # Normalizado: HD 20085/ton → 20.09/kg; CR 21.53/kg directo.
    assert por_slug["home-depot"]["price_per_kg"] == "20.09"
    assert por_slug["construrama"]["price_per_kg"] == "21.53"


@pytest.mark.django_db
def test_orden_por_precio_menor_primero(client, seeded):
    """sort=price ordena por el menor $/kg disponible entre retailers (F031)."""
    zona = seeded["zona"]
    response = client.get(f"/search?q=varilla&zone_id={zona.id}&sort=price")

    data = _results(response)

    def menor_por_kg(item):
        return min(
            Decimal(p["price_per_kg"])
            for p in item["prices"]
            if p["price_per_kg"] is not None and p["is_available"]
        )

    menores = [menor_por_kg(i) for i in data]
    assert menores == sorted(menores)


@pytest.mark.django_db
def test_para_varilla_4_home_depot_es_menor_por_kg_aunque_nativo_mayor(client, seeded):
    """Criterio clave F031: para la #4, HD (nativo por tonelada) tiene el menor
    $/kg aunque su `price` nativo sea MUCHO mayor que el de Construrama."""
    zona = seeded["zona"]
    canonico = CanonicalProduct.objects.get(name__startswith="Varilla corrugada 1/2")
    response = client.get(f"/search?q=1/2&zone_id={zona.id}")

    data = _results(response)
    item = next(i for i in data if i["canonical_product"]["id"] == str(canonico.id))
    por_slug = {p["retailer"]["slug"]: p for p in item["prices"]}

    hd, cr = por_slug["home-depot"], por_slug["construrama"]
    # El número NATIVO de HD es mayor (tonelada vs kg): 20085.00 >> 21.53.
    assert Decimal(hd["price"]) > Decimal(cr["price"])
    assert hd["sale_unit"] == "tonelada"
    assert cr["sale_unit"] == "kg"
    # Pero normalizado a $/kg, HD es MÁS BARATO: 20.09 < 21.53.
    assert Decimal(hd["price_per_kg"]) < Decimal(cr["price_per_kg"])
    assert hd["price_per_kg"] == "20.09"
    assert cr["price_per_kg"] == "21.53"


@pytest.mark.django_db
def test_orden_por_nombre(client, seeded):
    """sort=name ordena alfabéticamente por el nombre del canónico."""
    zona = seeded["zona"]
    response = client.get(f"/search?q=varilla&zone_id={zona.id}&sort=name")

    nombres = [i["canonical_product"]["name"] for i in _results(response)]
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

    data = _results(response)
    item = next(i for i in data if i["canonical_product"]["id"] == str(canonico.id))
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
    sin_acento = _results(client.get(f"/search?q=varilla&zone_id={zona.id}"))
    con_acento = _results(client.get(f"/search?q=várilla&zone_id={zona.id}"))

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

    # live=never: este canónico recién creado NO tiene observaciones (sin datos
    # frescos dispararía el vivo, F033); aquí solo se prueba el matcheo de DB.
    response = client.get(f"/search?q=portland&zone_id={zona.id}&live=never")

    ids = {i["canonical_product"]["id"] for i in _results(response)}
    assert str(canonico.id) in ids
