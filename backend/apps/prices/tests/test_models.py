"""Tests de modelo de precios y auditoría de scraping (F008).

Cubre los criterios de aceptación de la spec:
- varias `PriceObservation` del mismo producto+zona con distintos `captured_at`;
  la "última observación" (vía services) es la más reciente;
- `ScrapeRun` `partial` con `errors` no vacío;
- `raw_payload` persiste y se recupera como JSON;
- herencia de la base abstracta y `price` como Decimal exacto.
SQLite, sin Docker.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.catalog.models import RetailerProduct
from apps.geo.models import Retailer, RetailerLocation, Zone
from apps.prices import services
from apps.prices.models import PriceObservation, ScrapeRun


@pytest.fixture
def home_depot():
    return Retailer.objects.create(
        name="Home Depot",
        slug="home-depot",
        base_url="https://www.homedepot.com.mx",
        pricing_model=Retailer.PricingModel.ZONE_COOKIE,
    )


@pytest.fixture
def zona(home_depot):
    return Zone.objects.create(
        name="Monterrey Metro",
        slug="monterrey-metro",
        state="Nuevo León",
    )


@pytest.fixture
def location(home_depot):
    return RetailerLocation.objects.create(
        retailer=home_depot,
        external_id="store-1234",
        name="HD Monterrey Centro",
        city="Monterrey",
        state="Nuevo León",
    )


@pytest.fixture
def sku(home_depot):
    return RetailerProduct.objects.create(
        retailer=home_depot,
        external_sku="HD-001",
        raw_name="Varilla corrugada 3/8 12m",
    )


@pytest.mark.django_db
def test_price_observation_hereda_base_y_price_decimal(sku, zona):
    """PriceObservation hereda la base; price es Decimal exacto, no float."""
    obs = PriceObservation.objects.create(
        retailer_product=sku,
        zone=zona,
        price=Decimal("199.99"),
        source=PriceObservation.Source.XHR,
        captured_at=datetime(2026, 6, 13, 10, 0, tzinfo=UTC),
    )
    assert isinstance(obs.id, uuid.UUID)
    assert obs.created_at is not None
    assert obs.updated_at is not None
    assert obs.is_active is True

    obs.refresh_from_db()
    # Decimal exacto (no float): se conserva la representación monetaria.
    assert obs.price == Decimal("199.99")
    assert isinstance(obs.price, Decimal)
    assert obs.currency == "MXN"
    assert obs.is_available is True


@pytest.mark.django_db
def test_ultima_observacion_devuelve_la_mas_reciente(sku, zona):
    """Con varias observaciones del mismo producto+zona, la última es la más reciente."""
    vieja = PriceObservation.objects.create(
        retailer_product=sku,
        zone=zona,
        price=Decimal("180.00"),
        source=PriceObservation.Source.XHR,
        captured_at=datetime(2026, 6, 10, 8, 0, tzinfo=UTC),
    )
    intermedia = PriceObservation.objects.create(
        retailer_product=sku,
        zone=zona,
        price=Decimal("185.50"),
        source=PriceObservation.Source.HTML,
        captured_at=datetime(2026, 6, 11, 8, 0, tzinfo=UTC),
    )
    reciente = PriceObservation.objects.create(
        retailer_product=sku,
        zone=zona,
        price=Decimal("190.25"),
        source=PriceObservation.Source.PLAYWRIGHT,
        captured_at=datetime(2026, 6, 12, 8, 0, tzinfo=UTC),
    )

    ultima = services.ultima_observacion(sku, zona)
    assert ultima == reciente
    assert ultima.price == Decimal("190.25")
    # Las anteriores no se sobrescriben: el histórico se conserva.
    assert PriceObservation.objects.filter(retailer_product=sku, zone=zona).count() == 3
    assert {vieja, intermedia, reciente} == set(
        PriceObservation.objects.filter(retailer_product=sku, zone=zona)
    )


@pytest.mark.django_db
def test_ultima_observacion_sin_observaciones_devuelve_none(sku, zona):
    """Sin observaciones, el helper devuelve None (no lanza)."""
    assert services.ultima_observacion(sku, zona) is None


@pytest.mark.django_db
def test_ultima_observacion_aisla_por_zona(sku, zona):
    """La última observación se aísla por zona: otra zona no contamina el resultado."""
    otra_zona = Zone.objects.create(
        name="Guadalajara", slug="guadalajara", state="Jalisco"
    )
    PriceObservation.objects.create(
        retailer_product=sku,
        zone=otra_zona,
        price=Decimal("999.99"),
        source=PriceObservation.Source.XHR,
        captured_at=datetime(2026, 6, 13, 23, 0, tzinfo=UTC),
    )
    esperada = PriceObservation.objects.create(
        retailer_product=sku,
        zone=zona,
        price=Decimal("200.00"),
        source=PriceObservation.Source.XHR,
        captured_at=datetime(2026, 6, 12, 8, 0, tzinfo=UTC),
    )
    assert services.ultima_observacion(sku, zona) == esperada


@pytest.mark.django_db
def test_observations_related_name(sku, zona, location):
    """Las FKs exponen el related_name 'observations' en product/zone/location."""
    obs = PriceObservation.objects.create(
        retailer_product=sku,
        zone=zona,
        retailer_location=location,
        price=Decimal("150.00"),
        source=PriceObservation.Source.HTML,
        captured_at=datetime(2026, 6, 13, 9, 0, tzinfo=UTC),
    )
    assert list(sku.observations.all()) == [obs]
    assert list(zona.observations.all()) == [obs]
    assert list(location.observations.all()) == [obs]


@pytest.mark.django_db
def test_raw_payload_persiste_como_json(sku, zona):
    """raw_payload se persiste y recupera como JSON (auditabilidad §2.3)."""
    payload = {
        "endpoint": "/api/v1/products/HD-001",
        "http_status": 200,
        "fields": {"precio": "190.25", "stock": True},
        "tags": ["xhr", "varilla"],
    }
    obs = PriceObservation.objects.create(
        retailer_product=sku,
        zone=zona,
        price=Decimal("190.25"),
        source=PriceObservation.Source.XHR,
        captured_at=datetime(2026, 6, 13, 9, 0, tzinfo=UTC),
        raw_payload=payload,
    )
    obs.refresh_from_db()
    assert obs.raw_payload == payload
    assert obs.raw_payload["fields"]["stock"] is True


@pytest.mark.django_db
def test_raw_payload_default_dict(sku, zona):
    """raw_payload tiene default dict vacío si no se especifica."""
    obs = PriceObservation.objects.create(
        retailer_product=sku,
        zone=zona,
        price=Decimal("100.00"),
        source=PriceObservation.Source.HTML,
        captured_at=datetime(2026, 6, 13, 9, 0, tzinfo=UTC),
    )
    assert obs.raw_payload == {}


@pytest.mark.django_db
def test_scrape_run_partial_con_errores(home_depot, zona):
    """Un ScrapeRun 'partial' guarda errors no vacío como JSON y items_found."""
    errores = [
        {"sku": "HD-002", "error": "timeout"},
        {"sku": "HD-003", "error": "precio no encontrado"},
    ]
    run = ScrapeRun.objects.create(
        retailer=home_depot,
        zone=zona,
        started_at=datetime(2026, 6, 13, 6, 0, tzinfo=UTC),
        finished_at=datetime(2026, 6, 13, 6, 5, tzinfo=UTC),
        status=ScrapeRun.Status.PARTIAL,
        items_found=48,
        errors=errores,
    )
    run.refresh_from_db()
    assert run.status == ScrapeRun.Status.PARTIAL
    assert run.items_found == 48
    assert run.errors == errores
    assert len(run.errors) == 2
    # related_name en Retailer.
    assert list(home_depot.scrape_runs.all()) == [run]


@pytest.mark.django_db
def test_scrape_run_defaults(home_depot):
    """ScrapeRun: items_found default 0 y errors default lista vacía."""
    run = ScrapeRun.objects.create(
        retailer=home_depot,
        started_at=datetime(2026, 6, 13, 6, 0, tzinfo=UTC),
        status=ScrapeRun.Status.OK,
    )
    assert run.items_found == 0
    assert run.errors == []
    assert run.zone is None
    assert run.finished_at is None
