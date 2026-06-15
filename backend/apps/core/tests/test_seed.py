"""Tests del management command `seed` (F013).

Cubre los criterios de aceptación de la spec:
- `call_command("seed")` crea el grafo mínimo del PRD (Monterrey Metro · varilla);
- los conteos esperados existen (retailers, locations, zona, mapas, categoría,
  canónicos, retailer-products matcheados y observaciones con historial);
- `services.ultima_observacion` (F008) devuelve la observación más reciente;
- una 2ª corrida es **idempotente**: no duplica filas ni cambia conteos.
SQLite, sin Docker.
"""

from decimal import Decimal

import pytest
from django.core.management import call_command

from apps.catalog.models import CanonicalProduct, Category, RetailerProduct
from apps.geo.models import Retailer, RetailerLocation, Zone, ZoneLocationMap
from apps.prices import services
from apps.prices.models import PriceObservation


def _conteos() -> dict[str, int]:
    """Snapshot de conteos de todas las entidades sembradas."""
    return {
        "retailer": Retailer.objects.count(),
        "location": RetailerLocation.objects.count(),
        "zone": Zone.objects.count(),
        "zone_map": ZoneLocationMap.objects.count(),
        "category": Category.objects.count(),
        "canonical": CanonicalProduct.objects.count(),
        "retailer_product": RetailerProduct.objects.count(),
        "observation": PriceObservation.objects.count(),
    }


@pytest.mark.django_db
def test_seed_crea_el_grafo_de_la_spec():
    """Tras seed existe el grafo mínimo del PRD para Monterrey Metro · varilla."""
    call_command("seed")

    # 2 Retailers, ambos activos, con sus pricing_model.
    assert Retailer.objects.count() == 2
    hd = Retailer.objects.get(slug="home-depot")
    cr = Retailer.objects.get(slug="construrama")
    assert hd.pricing_model == Retailer.PricingModel.ZONE_COOKIE
    assert cr.pricing_model == Retailer.PricingModel.DISTRIBUTOR_SUBPATH
    assert hd.scraper_status == Retailer.ScraperStatus.ACTIVE
    assert cr.scraper_status == Retailer.ScraperStatus.ACTIVE

    # >= 2 RetailerLocation en Monterrey (HD con external_id; Construrama con subpath).
    assert RetailerLocation.objects.count() >= 2
    assert RetailerLocation.objects.filter(city="Monterrey").count() >= 2
    hd_loc = RetailerLocation.objects.filter(retailer=hd).first()
    cr_loc = RetailerLocation.objects.filter(retailer=cr).first()
    assert hd_loc.external_id  # tienda HD identificada por external_id
    # F028: la tienda HD de Monterrey usa el código real del recon F010 (no placeholder).
    assert hd_loc.external_id == "1333"
    assert hd_loc.city == "Monterrey"
    assert hd_loc.state == "NL"
    assert cr_loc.subpath  # distribuidor Construrama identificado por subpath

    # Zona "Monterrey Metro" con centroide aprox.
    zona = Zone.objects.get(slug="monterrey-metro")
    assert zona.name == "Monterrey Metro"
    assert zona.state == "NL"
    assert zona.centroid_lat is not None
    assert zona.centroid_lng is not None

    # ZoneLocationMap une la zona con cada location; exactamente una primaria.
    assert ZoneLocationMap.objects.filter(zone=zona).count() == RetailerLocation.objects.count()
    assert ZoneLocationMap.objects.filter(zone=zona, is_primary=True).count() == 1

    # Categoría "Varilla".
    cat = Category.objects.get(slug="varilla")
    assert cat.name == "Varilla"

    # 3-5 CanonicalProduct de varilla, unidad pieza, con specs.
    canonicos = CanonicalProduct.objects.filter(category=cat)
    assert 3 <= canonicos.count() <= 5
    for cp in canonicos:
        assert cp.unit == CanonicalProduct.Unit.PIEZA
        assert cp.specs  # specs no vacío (calibre/diametro/longitud)
        assert "calibre" in cp.specs

    # RetailerProduct por (canónico x retailer), matcheado manual.
    assert RetailerProduct.objects.count() == canonicos.count() * 2
    assert RetailerProduct.objects.filter(
        match_status=RetailerProduct.MatchStatus.MANUAL
    ).count() == RetailerProduct.objects.count()
    for rp in RetailerProduct.objects.all():
        assert rp.canonical_product is not None
        assert rp.external_sku
        assert rp.raw_name
        assert rp.url


@pytest.mark.django_db
def test_seed_crea_historial_y_ultima_observacion():
    """Cada retailer_product tiene >=2 observaciones en la zona; la última es la más reciente."""
    call_command("seed")
    zona = Zone.objects.get(slug="monterrey-metro")

    for rp in RetailerProduct.objects.all():
        obs = PriceObservation.objects.filter(retailer_product=rp, zone=zona).order_by(
            "captured_at"
        )
        assert obs.count() >= 2  # historial: varias capturas
        # captured_at distintos -> hay una más reciente real.
        capturas = [o.captured_at for o in obs]
        assert len(set(capturas)) == len(capturas)

        ultima = services.ultima_observacion(rp, zona)
        assert ultima is not None
        assert ultima == obs.last()  # la de captured_at mayor
        assert isinstance(ultima.price, Decimal)
        assert ultima.currency == "MXN"
        assert ultima.is_available is True
        assert ultima.source == PriceObservation.Source.XHR
        assert ultima.raw_payload == {"seed": True}


@pytest.mark.django_db
def test_seed_es_idempotente():
    """Correr seed 2 veces no duplica filas ni cambia conteos."""
    call_command("seed")
    primera = _conteos()

    call_command("seed")
    segunda = _conteos()

    assert primera == segunda
    # Y sigue habiendo exactamente lo esperado de cabeceras.
    assert segunda["retailer"] == 2
    assert segunda["zone"] == 1
    assert segunda["category"] == 1
    # F028: re-sembrar NO deja una location HD huérfana; queda exactamente 1
    # con el external_id real "1333" (la clave de lookup estable es (retailer, name)).
    hd = Retailer.objects.get(slug="home-depot")
    hd_locs = RetailerLocation.objects.filter(retailer=hd)
    assert hd_locs.count() == 1
    assert hd_locs.get().external_id == "1333"
