"""Tests del fix F035: crudos por término scrapeado (no solo por substring del nombre).

100% OFFLINE (sin red): se siembra el grafo con ORM y se llama al servicio
`buscar` con `live="never"` (jamás dispara la corrida en vivo ni toca adapters).
Reproduce el bug de uso real —el retailer resuelve un typo/fuzzy y devuelve
productos cuyo nombre NO contiene el texto tecleado— y verifica la UNIÓN
(término scrapeado ∪ nombre), el dedup y la normalización acento/case/espacio-
insensible del término (mismo helper que la búsqueda por nombre).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalog import services
from apps.catalog.models import RetailerProduct
from apps.geo.models import Retailer, Zone
from apps.prices.models import PriceObservation, ScrapeRun


@pytest.fixture
def home_depot(db):
    return Retailer.objects.create(
        name="Home Depot",
        slug="home-depot",
        base_url="https://www.homedepot.com.mx",
        pricing_model=Retailer.PricingModel.ZONE_COOKIE,
    )


@pytest.fixture
def zona(db):
    return Zone.objects.create(name="Monterrey Metro", slug="monterrey-metro", state="NL")


def _sembrar_crudo(
    *,
    retailer: Retailer,
    zona: Zone,
    external_sku: str,
    raw_name: str,
    search_term: str | None,
    price: str = "199.00",
    triggered_by: str = ScrapeRun.TriggeredBy.SEARCH,
) -> RetailerProduct:
    """Crea un RetailerProduct SIN canónico + su ScrapeRun (con `search_term`) + una
    PriceObservation en la zona ligada a esa corrida, tal como hace la ingestión F035.
    """
    rp = RetailerProduct.objects.create(
        retailer=retailer,
        external_sku=external_sku,
        raw_name=raw_name,
    )
    run = ScrapeRun.objects.create(
        retailer=retailer,
        zone=zona,
        started_at=timezone.now(),
        finished_at=timezone.now(),
        status=ScrapeRun.Status.OK,
        items_found=1,
        search_term=search_term,
        triggered_by=triggered_by,
    )
    PriceObservation.objects.create(
        retailer_product=rp,
        zone=zona,
        scrape_run=run,
        price=Decimal(price),
        currency="MXN",
        is_available=True,
        source=PriceObservation.Source.XHR,
        captured_at=timezone.now(),
    )
    return rp


def _skus(salida) -> list[str]:
    return [c.external_sku for c in salida.raw_results]


@pytest.mark.django_db
def test_bug_typo_muestra_crudos_por_termino_scrapeado(home_depot, zona):
    """El bug: el nombre dice 'Impermeabilizante' pero se scrapeó con el typo
    'impermiabilizante'. Sin el fix (filtro solo por nombre) daría 0 crudos."""
    rp = _sembrar_crudo(
        retailer=home_depot,
        zona=zona,
        external_sku="IMP-001",
        raw_name="Impermeabilizante Comex 19L blanco",
        search_term="impermiabilizante",  # el typo con que el retailer lo scrapeó
    )

    salida = services.buscar(q="impermiabilizante", zone_id=str(zona.id), live="never")

    assert salida is not None
    assert rp.external_sku in _skus(salida)
    # El nombre real (bien escrito) NO contiene el texto tecleado: prueba que se
    # halló por el término scrapeado (a), no por substring del nombre (b).
    assert "impermiabilizante" not in rp.raw_name.lower()


@pytest.mark.django_db
def test_sin_regresion_busqueda_por_nombre_sigue_funcionando(home_depot, zona):
    """El filtro (b) por nombre se conserva: buscar el nombre bien escrito lo
    encuentra aunque el término scrapeado registrado fuera otro."""
    rp = _sembrar_crudo(
        retailer=home_depot,
        zona=zona,
        external_sku="IMP-002",
        raw_name="Impermeabilizante Comex 19L blanco",
        search_term="promocion-mayo",  # término ajeno; el match debe ser por nombre
    )

    salida = services.buscar(q="impermeabilizante", zone_id=str(zona.id), live="never")

    assert rp.external_sku in _skus(salida)


@pytest.mark.django_db
def test_dedup_cuando_termino_y_nombre_se_solapan(home_depot, zona):
    """Un producto que cumple (a) término scrapeado Y (b) nombre aparece UNA sola vez."""
    _sembrar_crudo(
        retailer=home_depot,
        zona=zona,
        external_sku="IMP-003",
        raw_name="Impermeabilizante Comex 19L",
        search_term="impermeabilizante",  # coincide con el nombre Y con el término
    )

    salida = services.buscar(q="impermeabilizante", zone_id=str(zona.id), live="never")

    assert _skus(salida).count("IMP-003") == 1


@pytest.mark.django_db
def test_match_de_termino_es_acento_case_y_espacio_insensible(home_depot, zona):
    """El término se compara con el MISMO helper que el nombre (acento/case/espacio).
    El nombre NO contiene la query → el único camino posible es (a) por término."""
    rp = _sembrar_crudo(
        retailer=home_depot,
        zona=zona,
        external_sku="SEL-001",
        raw_name="Sellador elastico marca Generica",  # no dice 'impermeabilizante'
        search_term="  Impermeabilizànte  ",  # acentos + mayúsculas + espacios
    )

    salida = services.buscar(q="impermeabilizante", zone_id=str(zona.id), live="never")

    assert rp.external_sku in _skus(salida)


@pytest.mark.django_db
def test_termino_ajeno_no_arrastra_crudos_sin_relacion(home_depot, zona):
    """Un crudo scrapeado bajo OTRO término y cuyo nombre no matchea NO debe salir."""
    _sembrar_crudo(
        retailer=home_depot,
        zona=zona,
        external_sku="CLA-001",
        raw_name="Clavo de acero 2 pulgadas",
        search_term="clavo",
    )

    salida = services.buscar(q="impermeabilizante", zone_id=str(zona.id), live="never")

    assert "CLA-001" not in _skus(salida)
