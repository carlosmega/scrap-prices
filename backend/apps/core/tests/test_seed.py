"""Tests del management command `seed` (F013/F033).

Cubre los criterios de aceptación de la spec:
- `call_command("seed")` crea el grafo mínimo del PRD (Monterrey Metro · varilla);
- los conteos esperados existen (retailers, locations, zona, mapas, categoría,
  canónicos, retailer-products matcheados y observaciones con historial);
- `services.ultima_observacion` (F008) devuelve la observación más reciente;
- F033: cada RP tiene una observación FRESCA (captured_at ≈ ahora) — con datos
  frescos la búsqueda sembrada NO dispara el scrape en vivo — y existe ≥1
  RetailerProduct SIN matchear (el amarrador Truper, real del fixture Algolia
  de Construrama) con observación → la sección cruda es visible con seed;
- una 2ª corrida es **idempotente**: no duplica filas ni cambia conteos.
SQLite, sin Docker.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone

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
    # F029: params reales de routing HCL (marketId/stLocId) en extra.
    assert hd_loc.extra == {"market_id": "10", "st_loc_id": "18503"}
    assert cr_loc.subpath  # distribuidor Construrama identificado por subpath

    # Zona "Monterrey Metro" con centroide aprox.
    zona = Zone.objects.get(slug="monterrey-metro")
    assert zona.name == "Monterrey Metro"
    assert zona.state == "NL"
    assert zona.centroid_lat is not None
    assert zona.centroid_lng is not None

    # ZoneLocationMap une la zona con cada location; una primaria POR retailer
    # (la consume el resolver del comando `scrape`, que filtra por retailer; la
    # búsqueda de precios no depende de un único primario por zona).
    assert ZoneLocationMap.objects.filter(zone=zona).count() == RetailerLocation.objects.count()
    for retailer in (hd, cr):
        assert (
            ZoneLocationMap.objects.filter(
                zone=zona, is_primary=True, retailer_location__retailer=retailer
            ).count()
            == 1
        )

    # Categoría "Varilla".
    cat = Category.objects.get(slug="varilla")
    assert cat.name == "Varilla"

    # 3-5 CanonicalProduct de varilla, unidad pieza, con specs y mass_kg (F031).
    canonicos = CanonicalProduct.objects.filter(category=cat)
    assert 3 <= canonicos.count() <= 5
    for cp in canonicos:
        assert cp.unit == CanonicalProduct.Unit.PIEZA
        assert cp.specs  # specs no vacío (calibre/diametro/longitud)
        assert "calibre" in cp.specs
        # F031: el seed siembra el factor de conversión (peso de la pieza canónica).
        assert cp.mass_kg is not None
        assert cp.mass_kg > 0

    # RetailerProduct por (canónico x retailer), matcheado manual, MÁS el crudo
    # sin matchear de F033 (amarrador Truper).
    assert RetailerProduct.objects.count() == canonicos.count() * 2 + 1
    matcheados = RetailerProduct.objects.filter(match_status=RetailerProduct.MatchStatus.MANUAL)
    assert matcheados.count() == canonicos.count() * 2
    for rp in matcheados:
        assert rp.canonical_product is not None
        assert rp.external_sku
        assert rp.raw_name
        assert rp.url
    # F031: HD lista por tonelada, Construrama (matcheado) por kg (normalización).
    assert (
        RetailerProduct.objects.filter(retailer=hd)
        .exclude(sale_unit=RetailerProduct.SaleUnit.TONELADA)
        .count()
        == 0
    )
    assert (
        matcheados.filter(retailer=cr).exclude(sale_unit=RetailerProduct.SaleUnit.KG).count() == 0
    )


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
        assert ultima.raw_payload.get("seed") is True
        # F033: la última observación es la FRESCA (captured_at ≈ ahora, dentro
        # del TTL de 24 h): la búsqueda de términos sembrados no dispara el vivo.
        assert ultima.raw_payload.get("fresh") is True
        assert timezone.now() - ultima.captured_at < timedelta(hours=1)


@pytest.mark.django_db
def test_seed_siembra_crudo_sin_matchear_con_observacion():
    """F033: existe ≥1 RP SIN canónico (amarrador Truper) con su observación.

    Es el dato que hace visible la sección "resultados de las tiendas (sin
    comparar)" de la búsqueda con datos sembrados (lo exige el E2E de F033).
    """
    call_command("seed")
    zona = Zone.objects.get(slug="monterrey-metro")
    cr = Retailer.objects.get(slug="construrama")

    crudo = RetailerProduct.objects.get(external_sku="0204000086")
    assert crudo.retailer == cr
    assert crudo.canonical_product is None
    assert crudo.match_status == RetailerProduct.MatchStatus.UNMATCHED
    assert crudo.raw_name == "Truper, Amarrador De Varillas Con Grip, Pieza"
    assert crudo.brand == "TRUPER"
    assert crudo.sale_unit == RetailerProduct.SaleUnit.PIEZA
    assert crudo.url.endswith("/p/0204000086")

    obs = PriceObservation.objects.filter(retailer_product=crudo, zone=zona)
    assert obs.count() >= 2  # historial + fresca
    ultima = services.ultima_observacion(crudo, zona)
    assert ultima.price == Decimal("125.00")
    assert ultima.is_available is True
    assert timezone.now() - ultima.captured_at < timedelta(hours=1)


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
    # F029: el extra de routing se conserva idéntico tras re-sembrar (idempotente).
    assert hd_locs.get().extra == {"market_id": "10", "st_loc_id": "18503"}
    # F033: ni el crudo sin matchear ni su observación FRESCA se duplican; la
    # fresca se REFRESCA en sitio (marker raw_payload.fresh, no fila nueva).
    assert RetailerProduct.objects.filter(external_sku="0204000086").count() == 1
    for rp in RetailerProduct.objects.all():
        assert (
            PriceObservation.objects.filter(retailer_product=rp, raw_payload__fresh=True).count()
            == 1
        )
